"""
Simulates the trial -> paid decision for each account: whether they convert
at all, which plan/billing cycle they choose, and Experiment 2 (trial
discount framing), which affects ONLY the annual-vs-monthly choice among
accounts that do convert.

Also generates `trial_period_task_count`: a Poisson-distributed proxy for
engagement during the trial, driven by the hidden engagement_propensity.
This is the observable covariate CUPED will use in Phase 4 -- a real analyst
never sees engagement_propensity itself, only behavioral proxies like this.
"""

import numpy as np
import pandas as pd

import config as cfg
from generate_accounts import generate_accounts
from simulate_activation import simulate_activation, logistic, logit

rng = np.random.default_rng(cfg.RANDOM_SEED + 2)


def assign_experiment_2(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    eligible = df["trial_end_date"] >= pd.Timestamp(cfg.EXP2_START)
    df["exp2_eligible"] = eligible
    df["exp2_variant"] = np.where(
        eligible,
        rng.choice(["control", "treatment"], size=len(df), p=[1 - cfg.EXP2_SPLIT, cfg.EXP2_SPLIT]),
        "not_eligible",
    )
    return df


def simulate_subscriptions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["trial_end_date"] = pd.to_datetime(df["signup_date"]) + pd.Timedelta(days=cfg.TRIAL_LENGTH_DAYS)
    df["trial_observed"] = df["trial_end_date"] <= pd.Timestamp(cfg.SIM_END)

    # Trial-period engagement proxy (observable covariate for CUPED later).
    # Lambda scales with hidden propensity -- more engaged accounts create
    # more tasks during the trial.
    lam = 2 + 18 * df["engagement_propensity"]  # ranges roughly 2-20 tasks over 14 days
    df["trial_period_task_count"] = rng.poisson(lam)

    df = assign_experiment_2(df)

    # --- Conversion decision ---
    # Activated accounts convert much more than non-activated ones. Both are
    # further shifted by engagement_propensity.
    base_convert_logit = np.where(df["activated"], logit(0.55), logit(0.12))
    propensity_effect_convert = 2.0 * (df["engagement_propensity"] - df["engagement_propensity"].mean())
    p_convert = logistic(base_convert_logit + propensity_effect_convert)
    df["p_convert_true"] = p_convert.round(4)
    df["converted"] = np.where(df["trial_observed"], rng.binomial(1, p_convert).astype(bool), np.nan)

    # --- Plan choice (Pro vs Team), conditional on converting ---
    # Larger companies lean Team.
    team_base_p = df["company_size_bucket"].map({"small": 0.10, "medium": 0.35, "large": 0.65})
    chose_team = rng.binomial(1, team_base_p).astype(bool)
    df["plan"] = np.select(
        [df["converted"] == True, df["converted"] == False],  # noqa: E712
        [np.where(chose_team, "team", "pro"), "free"],
        default=None,
    )

    # --- Seats, conditional on converting ---
    seat_lambda = df["company_size_bucket"].map({"small": 2.5, "medium": 8, "large": 22})
    df["seats"] = np.where(df["converted"] == True, np.maximum(1, rng.poisson(seat_lambda)), np.nan)  # noqa: E712

    # --- Billing cycle (Experiment 2 lives here), conditional on converting ---
    base_annual_logit = logit(cfg.BASE_ANNUAL_SELECT_RATE)
    exp2_effect = np.where(
        (df["converted"] == True) & (df["exp2_variant"] == "treatment"),  # noqa: E712
        logit(cfg.BASE_ANNUAL_SELECT_RATE + cfg.EXP2_LIFT) - logit(cfg.BASE_ANNUAL_SELECT_RATE),
        0.0,
    )
    # Propensity effect on annual selection -- deliberately strong. This is what
    # makes trial_period_task_count a genuinely useful CUPED covariate: we need
    # real correlation between the pre-experiment proxy and the outcome for
    # variance reduction to do meaningful work in Phase 4 (CUPED's benefit
    # scales with the SQUARE of this correlation, so it needs to not be weak).
    propensity_effect_annual = 8.0 * (df["engagement_propensity"] - df["engagement_propensity"].mean())
    p_annual = logistic(base_annual_logit + exp2_effect + propensity_effect_annual)
    df["p_annual_true"] = p_annual.round(4)
    df["billing_cycle"] = np.where(
        df["converted"] == True,  # noqa: E712
        np.where(rng.binomial(1, p_annual).astype(bool), "annual", "monthly"),
        None,
    )

    # --- MRR ---
    price_per_seat = df["plan"].map(cfg.PLAN_PRICES).fillna(0)
    annual_discount = np.where(df["billing_cycle"] == "annual", 0.83, 1.0)  # ~2 months free ~ 17% off
    df["mrr"] = (price_per_seat * df["seats"].fillna(0) * annual_discount).round(2)

    return df


if __name__ == "__main__":
    accounts = generate_accounts()
    df = simulate_activation(accounts)
    df = simulate_subscriptions(df)

    observed = df[df["trial_observed"]]
    print(f"Accounts with observed trial outcome: {len(observed)} / {len(df)}")
    print("\nOverall conversion rate:", observed["converted"].mean().round(4))
    print("Conversion rate by activation status:")
    print(observed.groupby("activated")["converted"].mean().round(4))

    converted = observed[observed["converted"] == True]  # noqa: E712
    print(f"\nConverted accounts: {len(converted)}")
    print("Plan mix:", converted["plan"].value_counts(normalize=True).round(3).to_dict())

    elig2 = converted[converted["exp2_eligible"]]
    print("\nAnnual-selection rate by Experiment 2 arm (converted, eligible only):")
    print(elig2.groupby("exp2_variant")["billing_cycle"].apply(lambda s: (s == "annual").mean()).round(4))
    print("Sample sizes:", elig2["exp2_variant"].value_counts().to_dict())

    print("\nCorrelation check -- trial_period_task_count vs engagement_propensity:")
    print(round(df["trial_period_task_count"].corr(df["engagement_propensity"]), 3))
    print("Correlation -- trial_period_task_count vs annual selection (among converted, eligible):")
    elig2 = elig2.copy()
    elig2["chose_annual"] = (elig2["billing_cycle"] == "annual").astype(int)
    print(round(elig2["trial_period_task_count"].corr(elig2["chose_annual"]), 3))
