# TaskFlow Growth Analytics

**Status: Phase 1 (synthetic data generation) — in progress**

An end-to-end growth analytics case study built on a simulated B2B
project-management SaaS (TaskFlow). Goes beyond descriptive analytics
(funnels, cohorts) into the tools growth data teams actually use to make
decisions: rigorous A/B testing, causal inference for changes that couldn't
be randomized, and churn/LTV modeling.

See [`PROJECT_PLAN.md`](./PROJECT_PLAN.md) for the full spec, experiment
designs, and phase-by-phase roadmap.

## Why this project

Most portfolio analytics projects stop at descriptive work — cohorts, RFM,
dashboards. This one is built to also answer: *if we make a change, how do we
know it worked, and when can we trust that answer?* One of the three
experiments in this project is deliberately **not randomized**, forcing the
use of causal inference (diff-in-differences / propensity matching) instead
of a naive before/after comparison — the kind of judgment call that separates
"ran a t-test" from "knew when a t-test was the wrong tool."

## Stack

Python (data generation, analysis) → BigQuery (warehouse) → dbt (transformation,
testing, docs) → statsmodels/scipy/lifelines (experimentation, survival
analysis) → Streamlit (deployed interactive app)

## Repository Structure

```
taskflow-growth-analytics/
├── PROJECT_PLAN.md        # full spec, experiment designs, roadmap
├── data/
│   ├── raw/                # generated synthetic source data
│   └── processed/          # cleaned / modeled outputs
├── src/
│   └── data_generation/    # synthetic data generation scripts
├── dbt/                    # dbt project (staging -> intermediate -> marts)
├── notebooks/              # exploratory + phase-by-phase analysis notebooks
├── experiments/            # A/B test and causal inference analysis
├── app/                    # Streamlit app
└── docs/                   # diagrams, writeups
```

## Roadmap

1. Synthetic data generation
2. dbt models on BigQuery
3. Growth metrics layer (AARRR, retention)
4. Statistics fundamentals + A/B testing (frequentist + Bayesian, CUPED)
5. Causal inference (diff-in-diff / propensity matching)
6. Churn prediction + LTV (survival analysis)
7. Streamlit app
8. Case study writeup

## Data Note

All data in this repository is synthetic, generated for portfolio purposes.
No real company or user data is included.
