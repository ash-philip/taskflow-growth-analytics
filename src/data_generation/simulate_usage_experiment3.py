"""
Simulates ongoing weekly usage for accounts still on Free (didn't convert in
the trial), up to 52 weeks post-trial, right-censored at SIM_END. Detects the
first week each account crosses EXP3_WEEKLY_TASK_THRESHOLD and simulates
whether they later upgrade.

Experiment 3 is not randomized: every account crossing the threshold after
EXP3_START sees the nudge. The confound is structural, not injected. High-
propensity accounts are more likely to cross the threshold AND, independently,
more likely to upgrade regardless of the nudge. That is the point of this
experiment.
"""

import numpy as np
import pandas as pd

import config as cfg

rng = np.random.default_rng(cfg.RANDOM_SEED + 3)

MAX_WEEKS_POST_TRIAL = 52


def _logistic(x):
    return 1 / (1 + np.exp(-x))


def simulate_free_account_usage(df: pd.DataFrame):
    """Returns (weekly usage table, free-account table with threshold/nudge flags)."""
    free_accounts = df[df["converted"] == False].copy()  # noqa: E712 -- explicit False excludes NaN
    free_accounts["trial_end_date"] = pd.to_datetime(free_accounts["trial_end_date"])

    rows = []
    for _, acct in free_accounts.iterrows():
        propensity = acct["engagement_propensity"]
        base_lambda = 0.5 + 12 * propensity
        weeks_available = min(
            MAX_WEEKS_POST_TRIAL,
            (cfg.SIM_END - acct["trial_end_date"].date()).days // 7,
        )
        if weeks_available <= 0:
            continue

        for w in range(weeks_available):
            # mild usage growth over time so threshold crossings are gradual, not week-1 jumps
            lam = base_lambda * (1 + 0.015 * w * propensity)
            task_count = rng.poisson(lam)
            rows.append({
                "account_id": acct["account_id"],
                "week_number_post_trial": w,
                "week_date": acct["trial_end_date"] + pd.Timedelta(weeks=w),
                "task_count": task_count,
                "active": task_count > 0,
            })

    usage_df = pd.DataFrame(rows)

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

    # base ~5% for accounts that never cross; crossing alone lifts to ~35%
    # (the structural confound); the nudge adds EXP3_TRUE_LIFT on top of that
    base_logit = np.log(0.05 / 0.95)
    crossed_logit = np.log(0.35 / 0.65)
    propensity_effect = 3.0 * (df["engagement_propensity"] - df["engagement_propensity"].mean())
    crossed_effect = np.where(df["crossed_threshold"], crossed_logit - base_logit, 0.0)
    nudge_effect = np.where(
        df["exp3_nudged"],
        np.log((0.35 + cfg.EXP3_TRUE_LIFT) / (1 - 0.35 - cfg.EXP3_TRUE_LIFT)) - crossed_logit,
        0.0,
    )

    p_late_upgrade = _logistic(base_logit + propensity_effect + crossed_effect + nudge_effect)
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

    # naive vs confounder-controlled comparison (the whole point of the experiment)
    print("\nNaive comparison, nudged vs never-crossed (confounded):")
    naive = free_accounts.groupby(
        np.select(
            [free_accounts["exp3_nudged"], ~free_accounts["crossed_threshold"]],
            ["nudged", "never_crossed"],
            default="crossed_not_nudged",
        )
    )["late_upgraded"].agg(["mean", "count"])
    print(naive.round(4))

    print("\nControlled comparison, nudged vs crossed-before-nudge (both crossed the threshold):")
    correct = (
        free_accounts[free_accounts["crossed_threshold"]]
        .groupby("exp3_nudged")["late_upgraded"]
        .agg(["mean", "count"])
    )
    print(correct.round(4))