"""
One-time snapshot: pull marts from BigQuery into local CSVs so the deployed
Streamlit app can read them without a live warehouse connection.
Rerun only if the underlying data is regenerated.
"""

from pathlib import Path
from google.cloud import bigquery

client = bigquery.Client(project="taskflow-growth-analytics")

OUT_DIR = Path(__file__).parent / "data"
OUT_DIR.mkdir(exist_ok=True)

tables = [
    "funnel_summary",
    "retention_cohorts",
    "exp_onboarding_assignment",
    "exp_discount_assignment",
    "exp_nudge_assignment",
    "churn_features",
]

for table in tables:
    query = f"SELECT * FROM `taskflow-growth-analytics.taskflow_dev.{table}`"
    df = client.query(query).to_dataframe()
    df.to_csv(OUT_DIR / f"{table}.csv", index=False)
    print(f"Saved {table}.csv ({len(df)} rows)")

print("\nSnapshot complete.")