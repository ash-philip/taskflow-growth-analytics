"""
Simulates month-by-month subscription lifecycle for accounts that converted
to paid (at trial end OR via late upgrade): monthly active/churned status,
and light seat expansion (upsell) over time. Feeds Phase 6 survival analysis
(Kaplan-Meier / Cox) for LTV.

Monthly churn hazard is propensity-driven: higher engagement_propensity ->
lower hazard. Right-censored at SIM_END for accounts still active.
"""

import numpy as np
import pandas as pd

import config as cfg

rng = np.random.default_rng(cfg.RANDOM_SEED + 4)


def simulate_subscription_lifecycle(paid_accounts: pd.DataFrame) -> pd.DataFrame:
    """paid_accounts must have: account_id, conversion_date, seats, engagement_propensity."""
    rows = []
    for _, acct in paid_accounts.iterrows():
        propensity = acct["engagement_propensity"]
        # Hazard multiplier centered at 1.0 for mean propensity; higher propensity -> lower hazard.
        hazard_mult = np.exp(-2.5 * (propensity - 0.282))
        monthly_hazard = min(0.30, cfg.BASE_MONTHLY_CHURN_HAZARD * hazard_mult)

        seats = acct["seats"]
        month = 0
        current_date = pd.Timestamp(acct["conversion_date"])
        churned = False
        churn_date = None

        while current_date <= pd.Timestamp(cfg.SIM_END):
            # Light seat expansion: small monthly chance, more likely for engaged accounts.
            if rng.random() < 0.03 + 0.05 * propensity:
                seats += rng.integers(1, 3)

            rows.append(
                {
                    "account_id": acct["account_id"],
                    "month_number": month,
                    "month_date": current_date,
                    "seats": seats,
                    "churned_this_month": False,
                }
            )

            if rng.random() < monthly_hazard:
                churned = True
                churn_date = current_date
                rows[-1]["churned_this_month"] = True
                break

            month += 1
            current_date = current_date + pd.DateOffset(months=1)

        # (churned flag / churn_date used by the caller via the last row / separate summary)

    lifecycle_df = pd.DataFrame(rows)
    return lifecycle_df


def summarize_lifecycle(lifecycle_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        lifecycle_df.groupby("account_id")
        .agg(
            months_retained=("month_number", "max"),
            final_seats=("seats", "last"),
            churned=("churned_this_month", "max"),
        )
        .reset_index()
    )
    summary["months_retained"] = summary["months_retained"] + 1  # 0-indexed -> count
    return summary


if __name__ == "__main__":
    from generate_accounts import generate_accounts
    from simulate_activation import simulate_activation
    from simulate_subscriptions import simulate_subscriptions

    accounts = generate_accounts()
    df = simulate_activation(accounts)
    df = simulate_subscriptions(df)

    paid = df[df["converted"] == True].copy()  # noqa: E712
    paid["conversion_date"] = paid["trial_end_date"]

    lifecycle_df = simulate_subscription_lifecycle(paid)
    summary = summarize_lifecycle(lifecycle_df)

    print(f"Paid accounts simulated: {len(summary)}")
    print(f"Lifecycle rows (account-months): {len(lifecycle_df)}")
    print("\nChurn rate so far (observed, includes right-censored 'not yet churned'):")
    print(summary["churned"].mean().round(4))
    print("\nMonths retained distribution:")
    print(summary["months_retained"].describe().round(2))
    print("\nChecking propensity effect on churn -- churn rate by propensity quartile (should decrease):")
    paid_with_summary = paid.merge(summary, on="account_id")
    paid_with_summary["propensity_quartile"] = pd.qcut(paid_with_summary["engagement_propensity"], 4, labels=["Q1","Q2","Q3","Q4"])
    print(paid_with_summary.groupby("propensity_quartile")["churned"].mean().round(4))
