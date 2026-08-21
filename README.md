# TaskFlow Growth Analytics

A growth analytics case study on a simulated B2B SaaS company. It covers the full
path a real growth team works through: funnel and retention analysis, A/B testing,
causal inference, churn modeling, and customer lifetime estimation.

**Live app:** [PASTE STREAMLIT URL HERE]

## What this is

TaskFlow is a fictional project-management product. I generated two years of
realistic customer data for it, then analyzed that data end to end. Because I
built the data, I know the true answer behind every number, so the project can
show whether standard analysis methods actually recover the truth or get fooled
by it. That is the real focus here: not just running the analysis, but knowing
when to trust the result.

The project deliberately includes the situations most tutorials skip: experiments
that are underpowered, and a result that looks impressive but is caused by
confounding rather than the change being tested.

## Key findings

**Activation is the bottleneck.** Only about a third of signups become active
users, but around 79% of active users go on to pay. The problem is getting people
started, not getting them to pay.

**Two of three experiments were inconclusive, and saying so is the point.** A
naive read would pick a winner from noisy data. Proper power analysis showed one
onboarding test needed roughly 2,200 accounts per arm to detect the expected
effect, but only about 750 were available. The honest conclusion is "not enough
data yet," which is different from "the change failed."

**A pop-up nudge looked like a 9x win but did almost nothing.** Users who saw an
upgrade nudge were far more likely to upgrade, but the nudge only reached heavy
users who were already likely to upgrade. Comparing heavy users who saw the nudge
against equally heavy users who did not, the effect fell from +52 percentage
points to roughly zero, confirmed three separate ways. Correlation was not
causation.

**Median customer lifetime is about 18 months,** estimated with survival analysis
so that customers who have not yet churned are handled correctly.

## Stack

- **Data generation:** Python (numpy, pandas)
- **Warehouse:** Google BigQuery
- **Transformation:** dbt (staging, intermediate, and marts models, with tests)
- **Analysis:** pandas, statsmodels, scipy, scikit-learn, lifelines
- **App:** Streamlit, deployed on Streamlit Community Cloud

## How it works

```
src/data_generation/   Python scripts that generate the synthetic data
dbt/                   dbt models: staging -> intermediate -> marts, plus tests
notebooks/             statistical analysis (experiments, churn, survival)
app/                   Streamlit app that reads snapshot CSVs of the final marts
```

Data flows one direction: the Python scripts generate raw CSVs, dbt loads and
transforms them in BigQuery into clean marts, the notebook runs the statistical
analysis, and the Streamlit app presents the results.

## Running it locally

```bash
# 1. set up the environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. generate the synthetic data
python3 src/data_generation/run_all.py

# 3. load into BigQuery and build the dbt models
#    (requires a BigQuery project and `gcloud auth application-default login`)
./scripts/load_raw_data_to_bigquery.sh
cd dbt && dbt build

# 4. run the app
streamlit run app/streamlit_app.py
```

All data is synthetic. No real company or customer data is used.

## Author

Ashwin Philip · [GitHub](https://github.com/ash-philip) · [LinkedIn](https://www.linkedin.com/in/ashwinabrahamphilip)
