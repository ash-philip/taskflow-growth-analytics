"""
Simulates ongoing weekly usage for accounts that did NOT convert during the
trial (still on Free), for up to 52 weeks post-trial (right-censored at
SIM_END). Detects the first week each account crosses the
EXP3_WEEKLY_TASK_THRESHOLD, and simulates whether/when they later upgrade.

Experiment 3 is NOT randomized: every account that crosses the threshold
after EXP3_START sees the nudge. The confound is structural, not injected --
high-propensity accounts are simply more likely to cross the threshold AND
independently more likely to upgrade regardless of any nudge. That's the
whole point of this experiment.
"""

import numpy as np
import pandas as pd

import config as cfg

rng = np.random.default_rng(cfg.RANDOM_SEED + 3)

MAX_WEEKS_POST_TRIAL = 52


def simulate_free_account_usage(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a long-format weekly usage table for Free (non-converted) accounts."""
    free_accounts = df[df["converted"] == False].copy()  # noqa: E712
    free_accounts["trial_end_date"] = pd.to_datetime(free_accounts["trial_end_date"])

    rows = []
    for _, acct in free_accounts.iterrows():
        propensity = acct["engagement_propensity"]
        base_lambda = 0.5 + 12 * propensity  # base weekly task rate, propensity-driven
        weeks_available = min(
            MAX_WEEKS_POST_TRIAL,
            (cfg.SIM_END - acct["trial_end_date"].date()).days // 7,
        )
        if weeks_available <= 0:
            continue

        threshold_crossed_week = None
        for w in range(weeks_available):
            # Mild organic growth in usage over time for higher-propensity accounts --
            # this is what produces realistic, gradual threshold crossings rather than
            # an implausible jump in week 1.
            growth_mult = 1 + 0.015 * w * propensity
            lam = base_lambda * growth_mult
            task_count = rng.poisson(lam)

            week_date = acct["trial_end_date"] + pd.Timedelta(weeks=w)
            rows.append(
                {
                    "account_id": acct["account_id"],
                    "week_number_post_trial": w,
                    "week_date": week_date,
                    "task_count": task_count,
                    "active": task_count > 0,
                }
            )

            if threshold_crossed_week is None and task_count >= cfg.EXP3_WEEKLY_TASK_THRESHOLD:
                threshold_crossed_week = w

    usage_df = pd.DataFrame(rows)

    # --- Determine threshold crossing + experiment 3 exposure per account ---
    crossings = (
        usage_df[usage_df["task_count"] >= cfg.EXP3_WEEKLY_TASK_THRESHOLD]
        .sort_values("week_date")
        .groupby("account_id")
        .first()
        .reset_index()[["account_id", "week_date"]]
        .rename(columns={"week_date": "threshold_crossed_date"})
    )

    free_accounts = free_accounts.merge(crossings, on="account_id", how="left")
    free_accounts["crossed_threshold"] = free_accounts["threshold_crossed_date"].notna()
    free_accounts["exp3_nudged"] = free_accounts["crossed_threshold"] & (
        free_accounts["threshold_crossed_date"] >= pd.Timestamp(cfg.EXP3_START)
    )

    return usage_df, free_accounts


def simulate_late_upgrade(free_accounts: pd.DataFrame) -> pd.DataFrame:
    df = free_accounts.copy()

    # Baseline late-upgrade probability, propensity-driven, higher if the
    # account crossed the threshold at all (structural confound -- this is
    # true regardless of whether the nudge existed).
    base_logit = np.log(0.05 / 0.95)  # ~5% baseline for accounts that never cross
    propensity_effect = 3.0 * (df["engagement_propensity"] - df["engagement_propensity"].mean())
    crossed_effect = np.where(df["crossed_threshold"], np.log(0.35 / 0.65) - base_logit, 0.0)  # crossing alone -> ~35%
    nudge_effect = np.where(
        df["exp3_nudged"],
        np.log((0.35 + cfg.EXP3_TRUE_LIFT) / (1 - 0.35 - cfg.EXP3_TRUE_LIFT)) - np.log(0.35 / 0.65),
        0.0,
    )

    def logistic(x):
        return 1 / (1 + np.exp(-x))

    p_late_upgrade = logistic(base_logit + propensity_effect + crossed_effect + nudge_effect)
    df["p_late_upgrade_true"] = p_late_upgrade.round(4)
    df["late_upgraded"] = rng.binomial(1, p_late_upgrade).astype(bool)

    return df


if __name__ == "__main__":
    from generate_accounts import generate_accounts
    from simulate_activation import simulate_activation
    from simulate_subscriptions import simulate_subscriptions

    accounts = generate_accounts()
    df = simulate_activation(accounts)
    df = simulate_subscriptions(df)

    usage_df, free_accounts = simulate_free_account_usage(df)
    free_accounts = simulate_late_upgrade(free_accounts)

    print(f"Free accounts simulated: {len(free_accounts)}")
    print(f"Weekly usage rows: {len(usage_df)}")
    print(f"\nAccounts that ever crossed the {cfg.EXP3_WEEKLY_TASK_THRESHOLD}-task threshold:",
          free_accounts["crossed_threshold"].sum())
    print("Of those, nudged (crossed after EXP3_START):", free_accounts["exp3_nudged"].sum())

    print("\n--- The naive comparison a rushed analyst might make ---")
    print("Late-upgrade rate, nudged vs never-crossed (WRONG comparison -- confounded):")
    naive = free_accounts.groupby(
        np.select(
            [free_accounts["exp3_nudged"], ~free_accounts["crossed_threshold"]],
            ["nudged", "never_crossed"],
            default="crossed_not_nudged",
        )
    )["late_upgraded"].agg(["mean", "count"])
    print(naive.round(4))

    print("\n--- The correct comparison: nudged vs crossed-but-before-nudge-existed ---")
    print("(same 'type' of account -- crossed the threshold -- differing only by timing)")
    correct = free_accounts[free_accounts["crossed_threshold"]].groupby("exp3_nudged")["late_upgraded"].agg(["mean", "count"])
    print(correct.round(4))
