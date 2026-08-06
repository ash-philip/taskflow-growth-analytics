#!/bin/bash
set -e

PROJECT_ID="taskflow-growth-analytics"
DATASET="taskflow_raw"
LOCATION="US"

echo "Creating dataset ${DATASET} (if it doesn't already exist)..."
bq mk --location=${LOCATION} --dataset ${PROJECT_ID}:${DATASET} || echo "Dataset already exists, continuing..."

TABLES=(
  "accounts"
  "activation"
  "trials_and_conversion"
  "free_account_weekly_usage"
  "free_account_late_upgrade"
  "subscription_lifecycle"
  "subscription_summary"
)

for TABLE in "${TABLES[@]}"; do
  echo "Loading ${TABLE}..."
  bq load \
    --source_format=CSV \
    --autodetect \
    --skip_leading_rows=1 \
    --replace \
    ${PROJECT_ID}:${DATASET}.${TABLE} \
    data/raw/${TABLE}.csv
done

echo ""
echo "Done. Row counts in BigQuery:"
for TABLE in "${TABLES[@]}"; do
  bq query --use_legacy_sql=false --format=pretty \
    "SELECT '${TABLE}' AS table_name, COUNT(*) AS row_count FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`"
done
