"""
Generates the base `accounts` table: one row per company that signs up
for TaskFlow, with signup metadata and the hidden engagement_propensity.
"""

import datetime as dt
import numpy as np
import pandas as pd
from faker import Faker

import config as cfg

rng = np.random.default_rng(cfg.RANDOM_SEED)
fake = Faker()
Faker.seed(cfg.RANDOM_SEED)


def daily_signup_volume() -> np.ndarray:
    """Expected new accounts per day: linear growth from ~1.5/day to ~5/day
    over the window, with weekends running at half volume (B2B product)."""
    days = np.arange(cfg.SIM_DAYS)
    growth = 1.5 + (5.0 - 1.5) * (days / cfg.SIM_DAYS)
    dow = np.array([(cfg.SIM_START + dt.timedelta(int(d))).weekday() for d in days])
    weekend_mult = np.where(dow >= 5, 0.5, 1.0)
    return growth * weekend_mult


def generate_accounts() -> pd.DataFrame:
    lam = daily_signup_volume()
    n_per_day = rng.poisson(lam)

    rows = []
    account_id = 1
    for day_offset, n in enumerate(n_per_day):
        signup_date = cfg.SIM_START + dt.timedelta(int(day_offset))
        for _ in range(int(n)):
            channel = rng.choice(list(cfg.CHANNELS.keys()), p=list(cfg.CHANNELS.values()))
            size_bucket = rng.choice(
                list(cfg.COMPANY_SIZE_BUCKETS.keys()), p=list(cfg.COMPANY_SIZE_BUCKETS.values())
            )
            propensity = rng.beta(cfg.ENGAGEMENT_BETA_A, cfg.ENGAGEMENT_BETA_B)
            rows.append(
                {
                    "account_id": account_id,
                    "company_name": fake.company(),
                    "signup_date": signup_date,
                    "signup_channel": channel,
                    "company_size_bucket": size_bucket,
                    "engagement_propensity": round(propensity, 4),
                }
            )
            account_id += 1

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_accounts()
    print(f"Total accounts generated: {len(df)}")
    print("\nSignups per month:")
    print(pd.to_datetime(df["signup_date"]).dt.to_period("M").value_counts().sort_index())
    print("\nChannel mix:")
    print(df["signup_channel"].value_counts(normalize=True).round(3))
    print("\nCompany size mix:")
    print(df["company_size_bucket"].value_counts(normalize=True).round(3))
    print("\nEngagement propensity distribution:")
    print(df["engagement_propensity"].describe().round(3))
