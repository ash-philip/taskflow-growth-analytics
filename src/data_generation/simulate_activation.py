"""
Simulates activation (verify email + create first project + invite a
teammate, all within 7 days) for each account, and assigns/applies
Experiment 1 (onboarding redesign) for accounts that sign up after its
start date.

Design: activation probability per account = base rate, shifted up/down by
engagement_propensity (via a logistic link so it stays a valid probability),
plus a flat lift for Experiment 1 treatment accounts. We don't simulate the
three sub-events (verify/first-project/invite) separately with their own
probabilities -- we model the combined "did they activate" outcome directly.
That's a deliberate simplification: it keeps the *target* activation rate
exact and checkable against the config, which matters because Phase 4 will
ask you to recover EXP1_LIFT from noisy data -- we want to know precisely
what "ground truth" we're checking your estimate against.
"""

import numpy as np
import pandas as pd

import config as cfg
from generate_accounts import generate_accounts

rng = np.random.default_rng(cfg.RANDOM_SEED + 1)


def logistic(x):
    return 1 / (1 + np.exp(-x))


def logit(p):
    return np.log(p / (1 - p))


def assign_experiment_1(accounts: pd.DataFrame) -> pd.DataFrame:
    df = accounts.copy()
    eligible = pd.to_datetime(df["signup_date"]) >= pd.Timestamp(cfg.EXP1_START)
    df["exp1_eligible"] = eligible
    df["exp1_variant"] = np.where(
        eligible,
        rng.choice(["control", "treatment"], size=len(df), p=[1 - cfg.EXP1_SPLIT, cfg.EXP1_SPLIT]),
        "not_eligible",
    )
    return df


def simulate_activation(accounts: pd.DataFrame) -> pd.DataFrame:
    df = assign_experiment_1(accounts)

    # Base activation probability as a logit, centered so that when
    # engagement_propensity = its mean (~0.286), P(activate) ~= BASE_ACTIVATION_RATE.
    base_logit = logit(cfg.BASE_ACTIVATION_RATE)

    # engagement_propensity in [0,1] -> center and scale it into a logit contribution.
    # Coefficient of 2.5 gives high-propensity accounts a meaningfully higher
    # activation chance without letting anyone hit ~0% or ~100%.
    propensity_effect = 2.5 * (df["engagement_propensity"] - df["engagement_propensity"].mean())

    exp1_effect = np.where(
        df["exp1_variant"] == "treatment",
        logit(cfg.BASE_ACTIVATION_RATE + cfg.EXP1_LIFT) - logit(cfg.BASE_ACTIVATION_RATE),
        0.0,
    )

    p_activate = logistic(base_logit + propensity_effect + exp1_effect)
    df["p_activate_true"] = p_activate.round(4)  # kept for validation only, drop before "official" release
    df["activated"] = rng.binomial(1, p_activate).astype(bool)

    # Activation timestamp: activated accounts activate somewhere in days 1-7
    activation_day_offset = rng.integers(1, cfg.ACTIVATION_WINDOW_DAYS + 1, size=len(df))
    df["activation_date"] = np.where(
        df["activated"],
        pd.to_datetime(df["signup_date"]) + pd.to_timedelta(activation_day_offset, unit="D"),
        pd.NaT,
    )

    return df


if __name__ == "__main__":
    accounts = generate_accounts()
    df = simulate_activation(accounts)

    print("Overall activation rate:", df["activated"].mean().round(4))
    print("\nActivation rate by Experiment 1 arm (eligible accounts only):")
    print(
        df[df["exp1_eligible"]]
        .groupby("exp1_variant")["activated"]
        .agg(["mean", "count"])
        .round(4)
    )
    print("\nActivation rate for pre-experiment accounts (should be ~0.32):")
    print(df[~df["exp1_eligible"]]["activated"].mean().round(4))
    print("\nSanity check -- activation rate by propensity quartile (should increase):")
    df["propensity_quartile"] = pd.qcut(df["engagement_propensity"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    print(df.groupby("propensity_quartile")["activated"].mean().round(4))
