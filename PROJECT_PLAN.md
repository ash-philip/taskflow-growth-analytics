# TaskFlow Growth Analytics — Project Plan

This is the living reference doc for the project. Update it as decisions change.
Status fields use: `[ ] not started`, `[~] in progress`, `[x] done`.

---

## 1. Purpose

Portfolio centerpiece project demonstrating growth analytics: product funnel
analysis, rigorous A/B testing, causal inference for non-randomized changes,
and churn/LTV modeling — built on a modern-ish data stack and shipped as a
deployed, interactive app rather than static notebooks.

---

## 2. Product Concept: TaskFlow

Fictional B2B project-management SaaS.

**Plans**
| Plan | Price | Limits |
|---|---|---|
| Free | $0 | 3 projects, 5 team members |
| Pro | $12/user/mo | Unlimited projects, integrations, advanced reporting |
| Team | $29/user/mo | Pro + admin controls, SSO, priority support |

New signups get a 14-day Pro trial before falling back to Free (if they don't
convert) or converting to Pro/Team.

**Acquisition channels:** organic search, paid search, content/blog, referral, direct.

**Funnel (AARRR)**
- **Acquisition:** signup (email + company name + channel)
- **Activation:** verify email + create first project + invite ≥1 teammate,
  all within 7 days of signup. (Deliberately a 3-step "aha moment" definition —
  worth defending in the README: why these 3 actions, why 7 days.)
- **Retention:** weekly active usage (task/comment creation), tracked via
  cohort retention curves
- **Revenue:** trial→paid conversion, seat expansion, churn
- **Churn definition:** 30 consecutive days with no activity while on a paid plan

**Simulated timeframe:** 24 months of daily events across monthly signup cohorts.
Small enough to stay well within BigQuery's free tier (10GB storage / 1TB query
processing per month).

---

## 3. The Three Built-In Experiments

These are synthetic ground-truth effects designed into the data generator so
the statistical methods have real signal to recover. They are NOT real-world
benchmarks — just realistic, intentionally modest effect sizes.

### Experiment 1 — Onboarding Redesign
- **Type:** Randomized A/B, user-level
- **What changed:** 5-step onboarding → streamlined 3-step onboarding
- **Starts:** simulated month 10
- **True effect:** activation rate 32% → 36% (a small, realistic lift)
- **Sample size reality check:** required ~2,198 accounts/arm for 80% power;
  the simulated window only produces ~750-786/arm. **This is intentional.**
  A single naive test on this data will often come back statistically
  inconclusive even though a real effect exists — which is the point. The
  deliverable here isn't "found significance," it's correctly running a
  power analysis *before* trusting the result, and drawing the honest
  conclusion ("underpowered, can't confirm or rule out the effect") instead
  of misreading a null result as "no effect."
- **Method:** frequentist two-proportion test + power analysis + Bayesian
  A/B comparison (Bayesian framing communicates the actual uncertainty
  better than a binary reject/fail-to-reject call here)

### Experiment 2 — Trial Discount Framing
- **Type:** Randomized A/B, user-level, shown at trial-to-paid decision point
- **What changed:** "Save 20% with annual billing" vs "Get 2 months free"
  (economically identical, different framing)
- **True effect:** ~4pp lift in annual-plan selection
- **Sample size reality check:** required ~1,786/arm for 80% power; naive
  test is also underpowered here. This is where CUPED earns its keep —
  using pre-trial engagement level (a proxy for the hidden engagement
  propensity) as a covariate to reduce outcome variance and recover enough
  sensitivity to detect the same true effect with the same sample. Plan is
  to show both: naive test (likely inconclusive) vs CUPED-adjusted test
  (should detect it) side by side.
- **Method:** frequentist test, naive vs CUPED-adjusted, compared directly

### Experiment 3 — In-App Upgrade Nudge (the important one)
- **Type:** NOT randomized — rolled out to all Free users who cross a usage
  threshold (>15 tasks created in a week)
- **Starts:** simulated month 16
- **True effect:** genuine lift in upgrade rate exists (~5–8pp) but is
  confounded — heavy users were already more likely to convert regardless of
  the nudge. A naive before/after comparison will overstate the effect.
- **Method:** difference-in-differences (using near-threshold users as
  comparison) and/or propensity score matching
- **Why this matters:** this is the experiment that demonstrates judgment —
  knowing when a t-test is the wrong tool.

---

## 4. Tech Stack

- **Data generation:** Python (numpy/pandas/faker)
- **Warehouse:** Google BigQuery (free tier — no credit card required for sandbox)
- **Transformation:** dbt (staging → intermediate → marts, with tests + docs)
- **Analysis:** Python (pandas, scipy, statsmodels, scikit-learn, lifelines for survival analysis)
- **App:** Streamlit, deployed on Streamlit Community Cloud
- **Version control:** Git/GitHub

Deliberately excluded for scope reasons (listed as "Future Improvements" in
the README instead): Airflow/Dagster orchestration, real-time streaming.

---

## 5. Phase Roadmap

- [x] **Phase 1 — Synthetic data generation** (done)
  2,026 accounts over 24 months. Verified end-to-end: activation rate ~33%
  (propensity gradient 24%→42% across quartiles, confirming the hidden
  engagement_propensity variable is doing real work), trial conversion 26.7%
  (11.6% non-activated vs 58.1% activated -- activation is a real lever),
  churn decreasing cleanly across propensity quartiles (38.6%→15.2%). All
  three experiments verified against their true probabilities, not just
  realized outcomes. Output: 8 CSVs in `data/raw/` (1.8MB total) + a held-out
  `ground_truth.csv` with the hidden variables, kept separate from the
  analysis-ready tables.
- [ ] **Phase 2 — dbt models on BigQuery**
  Staging models, intermediate (session/user-level rollups), mart models
  (funnel, retention, experiment assignment/results tables), tests, docs.
- [ ] **Phase 3 — Growth metrics layer**
  AARRR funnel, activation rate, cohort retention curves, DAU/WAU/MAU,
  North Star metric definition.
- [ ] **Phase 4 — Statistics fundamentals + experimentation**
  Hypothesis testing basics, power analysis, frequentist A/B testing,
  multiple-testing pitfalls, CUPED, intro Bayesian A/B testing — taught
  from scratch, applied to Experiments 1 and 2.
- [ ] **Phase 5 — Causal inference**
  Diff-in-differences and/or propensity score matching applied to Experiment 3.
- [ ] **Phase 6 — Churn prediction + LTV**
  Churn classifier (logistic regression / gradient boosting), survival
  analysis (Kaplan-Meier / Cox proportional hazards) for LTV.
- [ ] **Phase 7 — Streamlit app**
  Interactive funnel viewer, retention curves, experiment results explorer,
  churn risk lookup. Deployed, not just local.
- [ ] **Phase 8 — README / case study writeup**
  Business-framed writeup matching the style of your other two repos.

---

## 6. Setup Checklist (before Phase 1)

- [ ] Python 3.x environment (venv)
- [ ] Git repo created on GitHub (private is fine until ready to publish)
- [ ] Google Cloud account + BigQuery sandbox (no credit card needed)
- [ ] `pip install dbt-core dbt-bigquery` (once we reach Phase 2)

---

## 6a. Phase 1 Output Tables (in `data/raw/`)

| File | Rows | Grain |
|---|---|---|
| `accounts.csv` | 2,026 | 1 row/account |
| `activation.csv` | 2,026 | 1 row/account |
| `trials_and_conversion.csv` | 2,026 | 1 row/account |
| `free_account_weekly_usage.csv` | 48,798 | 1 row/account/week (Free accounts only) |
| `free_account_late_upgrade.csv` | 1,444 | 1 row/Free account |
| `subscription_lifecycle.csv` | 5,081 | 1 row/paid account/month |
| `subscription_summary.csv` | 665 | 1 row/paid account (trial converts + late upgraders) |
| `ground_truth.csv` | 2,026 | **Held out.** Hidden engagement_propensity + true probabilities. Not for use in analysis — validation only. |

## 6b. Discoveries Made During Phase 1 (kept intentionally, not "bugs")

- **Experiment 1 is genuinely underpowered as generated**: needs ~2,198
  accounts/arm for 80% power on a 32%→36% lift; the 24-month window only
  produces ~750-786/arm. A single realized run can show anywhere from -2.5pp
  to +10.8pp purely from sampling noise (checked via 500 resamples against
  the true probabilities). Kept deliberately — teaches power analysis and
  honest interpretation of inconclusive results.
- **Experiment 2 needed a stronger covariate correlation to make CUPED's
  value legible**: initial design gave trial_period_task_count only a 0.089
  correlation with the outcome (chose annual) — too weak for CUPED to show a
  meaningful variance reduction (benefit scales with correlation²). Increased
  the propensity effect on annual-selection until correlation reached 0.347.
- **Experiment 3's confound is structural, not injected**: crossed-threshold
  accounts are inherently high-propensity, which is exactly the trap a naive
  "nudged vs never-crossed" comparison falls into (58% vs 6% — a wildly
  overstated apparent effect). The correct comparison (nudged vs
  crossed-but-before-the-nudge-existed) shows the real, much smaller signal,
  and even that comparison is thin (n=53 vs 62) — realistic for a feature
  that's only been live 8 of the 24 simulated months.

## 7. Decisions Log

- 2026-08-04: Chose growth analytics (over other portfolio directions) —
  reasoning: complements existing SQL/BI/forecasting work, fills the
  experimentation/causal-inference gap, matches current industry emphasis.
- 2026-08-04: Chose TaskFlow (B2B SaaS) as the single centerpiece project.
  Inkwell AI (AI writing SaaS) parked as a possible future second project.
- 2026-08-04: Stack = BigQuery + dbt + Python + Streamlit. Orchestration
  (Airflow/Dagster) explicitly deferred to "future improvements."
