"""
Simulates the trial -> paid decision for each account: whether they convert,
which plan/billing cycle they choose, and Experiment 2 (trial discount framing),
which affects only the annual-vs-monthly choice among accounts that convert.

Also generates trial_period_task_count: a Poisson proxy for trial engagement,
driven by the hidden engagement_propensity. This is the observable covariate
used by CUPED later, since a real analyst never sees engagement_propensity
directly, only behavioral proxies like this.
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

    # trial-engagement proxy; lambda scales with propensity (~2-20 tasks over 14 days)
    lam = 2 + 18 * df["engagement_propensity"]
    df["trial_period_task_count"] = rng.poisson(lam)

    df = assign_experiment_2(df)

    # conversion: activated accounts convert far more; propensity shifts both
    base_convert_logit = np.where(df["activated"], logit(0.55), logit(0.12))
    propensity_effect_convert = 2.0 * (df["engagement_propensity"] - df["engagement_propensity"].mean())
    p_convert = logistic(base_convert_logit + propensity_effect_convert)
    df["p_convert_true"] = p_convert.round(4)
    df["converted"] = np.where(df["trial_observed"], rng.binomial(1, p_convert).astype(bool), np.nan)

    # plan choice (larger companies lean Team), conditional on converting
    team_base_p = df["company_size_bucket"].map({"small": 0.10, "medium": 0.35, "large": 0.65})
    chose_team = rng.binomial(1, team_base_p).astype(bool)
    df["plan"] = np.select(
        [df["converted"] == True, df["converted"] == False],  # noqa: E712 -- explicit True/False excludes NaN
        [np.where(chose_team, "team", "pro"), "free"],
        default=None,
    )

    seat_lambda = df["company_size_bucket"].map({"small": 2.5, "medium": 8, "large": 22})
    df["seats"] = np.where(df["converted"] == True, np.maximum(1, rng.poisson(seat_lambda)), np.nan)  # noqa: E712

    # billing cycle is where Experiment 2's effect is applied
    base_annual_logit = logit(cfg.BASE_ANNUAL_SELECT_RATE)
    exp2_effect = np.where(
        (df["converted"] == True) & (df["exp2_variant"] == "treatment"),  # noqa: E712
        logit(cfg.BASE_ANNUAL_SELECT_RATE + cfg.EXP2_LIFT) - logit(cfg.BASE_ANNUAL_SELECT_RATE),
        0.0,
    )
    # strong propensity effect on purpose: CUPED's benefit scales with the square
    # of the covariate-outcome correlation, so the proxy needs real signal here
    propensity_effect_annual = 8.0 * (df["engagement_propensity"] - df["engagement_propensity"].mean())
    p_annual = logistic(base_annual_logit + exp2_effect + propensity_effect_annual)
    df["p_annual_true"] = p_annual.round(4)
    df["billing_cycle"] = np.where(
        df["converted"] == True,  # noqa: E712
        np.where(rng.binomial(1, p_annual).astype(bool), "annual", "monthly"),
        None,
    )

    price_per_seat = df["plan"].map(cfg.PLAN_PRICES).fillna(0)
    annual_discount = np.where(df["billing_cycle"] == "annual", 0.83, 1.0)  # annual ~= 2 months free
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

    elig2 = converted[converted["exp2_eligible"]].copy()
    print("\nAnnual-selection rate by Experiment 2 arm (converted, eligible only):")
    print(elig2.groupby("exp2_variant")["billing_cycle"].apply(lambda s: (s == "annual").mean()).round(4))
    print("Sample sizes:", elig2["exp2_variant"].value_counts().to_dict())

    elig2["chose_annual"] = (elig2["billing_cycle"] == "annual").astype(int)
    print("\nCorrelation, trial_period_task_count vs engagement_propensity:",
          round(df["trial_period_task_count"].corr(df["engagement_propensity"]), 3))
    print("Correlation, trial_period_task_count vs annual selection (converted, eligible):",
          round(elig2["trial_period_task_count"].corr(elig2["chose_annual"]), 3))