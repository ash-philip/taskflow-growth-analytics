"""
Orchestrates the full TaskFlow synthetic data generation pipeline and writes
analysis-ready CSVs to data/raw/, plus a separate ground_truth.csv holding
the hidden variables (engagement_propensity, true probabilities) that a real
analyst would never observe -- kept apart so later phases can't accidentally
leak on them, and so we can check recovered estimates against reality.

Run: python3 run_all.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

import config as cfg
from generate_accounts import generate_accounts
from simulate_activation import simulate_activation
from simulate_subscriptions import simulate_subscriptions
from simulate_usage_experiment3 import simulate_free_account_usage, simulate_late_upgrade
from simulate_churn import simulate_subscription_lifecycle, summarize_lifecycle

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def main():
    print("1/6 Generating accounts...")
    accounts = generate_accounts()

    print("2/6 Simulating activation + Experiment 1...")
    df = simulate_activation(accounts)

    print("3/6 Simulating trial conversion + Experiment 2...")
    df = simulate_subscriptions(df)

    print("4/6 Simulating free-account usage + Experiment 3...")
    usage_df, free_accounts = simulate_free_account_usage(df)
    free_accounts = simulate_late_upgrade(free_accounts)

    # Late upgraders get a conversion_date so they can enter the paid lifecycle sim.
    free_accounts["late_upgrade_date"] = np.where(
        free_accounts["late_upgraded"] & free_accounts["crossed_threshold"],
        free_accounts["threshold_crossed_date"] + pd.Timedelta(days=7),
        np.where(
            free_accounts["late_upgraded"],
            free_accounts["trial_end_date"] + pd.Timedelta(days=45),
            pd.NaT,
        ),
    )

    print("5/6 Simulating paid subscription lifecycle + churn...")
    trial_converts = df[df["converted"] == True].copy()  # noqa: E712
    trial_converts["conversion_date"] = trial_converts["trial_end_date"]
    trial_converts["upgrade_path"] = "trial_conversion"

    late_upgraders = free_accounts[free_accounts["late_upgraded"]].copy()
    late_upgraders["conversion_date"] = late_upgraders["late_upgrade_date"]
    late_upgraders["upgrade_path"] = "late_upgrade"
    # Late upgraders default to Pro, monthly billing, seats scaled to company size.
    late_upgraders["plan"] = "pro"
    late_upgraders["seats"] = late_upgraders["company_size_bucket"].map(
        {"small": 2, "medium": 6, "large": 15}
    )

    all_paid = pd.concat(
        [
            trial_converts[["account_id", "conversion_date", "seats", "engagement_propensity", "plan", "upgrade_path"]],
            late_upgraders[["account_id", "conversion_date", "seats", "engagement_propensity", "plan", "upgrade_path"]],
        ],
        ignore_index=True,
    )
    all_paid = all_paid[pd.to_datetime(all_paid["conversion_date"]) <= pd.Timestamp(cfg.SIM_END)]

    lifecycle_df = simulate_subscription_lifecycle(all_paid)
    lifecycle_summary = summarize_lifecycle(lifecycle_df)

    print("6/6 Assembling and writing output tables...")

    # --- Ground truth (held out) ---
    ground_truth_cols = [
        "account_id", "engagement_propensity", "p_activate_true",
        "p_convert_true", "p_annual_true",
    ]
    ground_truth = df[ground_truth_cols].merge(
        free_accounts[["account_id", "p_late_upgrade_true"]], on="account_id", how="left"
    )

    # --- accounts.csv ---
    accounts_out = df[["account_id", "company_name", "signup_date", "signup_channel", "company_size_bucket"]]

    # --- activation.csv ---
    activation_out = df[["account_id", "activated", "activation_date", "exp1_eligible", "exp1_variant"]]

    # --- trials_and_conversion.csv ---
    trials_out = df[
        ["account_id", "trial_end_date", "trial_observed", "converted", "plan", "seats",
         "billing_cycle", "mrr", "exp2_eligible", "exp2_variant", "trial_period_task_count"]
    ]

    # --- free_account_weekly_usage.csv ---
    usage_out = usage_df

    # --- free_account_late_upgrade.csv ---
    late_upgrade_out = free_accounts[
        ["account_id", "crossed_threshold", "threshold_crossed_date", "exp3_nudged", "late_upgraded", "late_upgrade_date"]
    ]

    # --- subscription_lifecycle.csv + subscription_summary.csv ---
    lifecycle_out = lifecycle_df
    lifecycle_summary_out = lifecycle_summary.merge(
        all_paid[["account_id", "upgrade_path", "plan"]], on="account_id", how="left"
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    accounts_out.to_csv(OUT_DIR / "accounts.csv", index=False)
    activation_out.to_csv(OUT_DIR / "activation.csv", index=False)
    trials_out.to_csv(OUT_DIR / "trials_and_conversion.csv", index=False)
    usage_out.to_csv(OUT_DIR / "free_account_weekly_usage.csv", index=False)
    late_upgrade_out.to_csv(OUT_DIR / "free_account_late_upgrade.csv", index=False)
    lifecycle_out.to_csv(OUT_DIR / "subscription_lifecycle.csv", index=False)
    lifecycle_summary_out.to_csv(OUT_DIR / "subscription_summary.csv", index=False)
    ground_truth.to_csv(OUT_DIR / "ground_truth.csv", index=False)

    print(f"\nDone. Files written to {OUT_DIR}:")
    for f in sorted(OUT_DIR.glob("*.csv")):
        n_rows = sum(1 for _ in open(f)) - 1
        print(f"  {f.name}: {n_rows} rows")


if __name__ == "__main__":
    main()
