import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="TaskFlow Growth Analytics",
    page_icon="📊",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load(name):
    return pd.read_csv(DATA_DIR / f"{name}.csv")

funnel = load("funnel_summary")

# ---------- HERO ----------
st.title("📊 TaskFlow Growth Analytics")
st.markdown(
    "#### A growth analytics case study on a simulated B2B SaaS product"
)

with st.expander("About this project"):
    st.markdown("""
    This project demonstrates the **full experimentation lifecycle** end-to-end:
    funnel & retention analysis, rigorous A/B testing, CUPED variance reduction,
    causal inference, and survival analysis. A deliberate theme throughout is the
    **honest handling of underpowered and confounded results** — the realistic
    scenarios most tutorials skip.

    **Stack:** Python · BigQuery · dbt · statsmodels · lifelines · Streamlit
    &nbsp;·&nbsp; *All data is synthetic.*
    """)

st.divider()

# ---------- TABS ----------
tab_overview, tab_funnel, tab_retention, tab_experiments, tab_lifetime = st.tabs(
    ["Overview", "Funnel", "Retention", "Experiments", "Lifetime"]
)

# ===== OVERVIEW =====
with tab_overview:
    st.subheader("The story in three findings")

    c1, c2, c3 = st.columns(3)
    c1.metric("Activation rate", f"{funnel['activation_rate'][0]*100:.0f}%",
              help="Share of signups that activate")
    c2.metric("Conversion of activated", f"{funnel['conversion_rate_of_activated'][0]*100:.0f}%",
              help="Share of activated accounts that convert to paid")
    c3.metric("Median customer lifetime", "18 months",
              help="From survival analysis")

    st.markdown("""
    **1. Activation is the bottleneck.** Only a third of signups activate — but
    ~79% of *activated* accounts convert to paid. The leak is at the top of the
    funnel, not the bottom.

    **2. Rigorous experiments beat eyeballing.** Two of three experiments were
    underpowered by design. Naively reading them would mislead; power analysis and
    CUPED show the *honest* conclusion is "not enough data yet," not "it failed."

    **3. Correlation isn't causation.** An upgrade nudge *looked* like a +52pp win —
    but that was entirely confounding. Controlling for it, the real effect was ~0.
    """)

    st.caption("Use the tabs above to explore each analysis in detail.")

# ===== FUNNEL =====
with tab_funnel:
    st.subheader("Activation Funnel")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Signups", f"{int(funnel['total_signups'][0]):,}")
    c2.metric("Activated", f"{int(funnel['total_activated'][0]):,}",
              f"{funnel['activation_rate'][0]*100:.1f}% of signups")
    c3.metric("Converted", f"{int(funnel['total_converted'][0]):,}",
              f"{funnel['conversion_rate_overall'][0]*100:.1f}% of signups")

    st.info(
        f"**Key insight:** Activation is the bottleneck — only "
        f"{funnel['activation_rate'][0]*100:.0f}% of signups activate, but "
        f"{funnel['conversion_rate_of_activated'][0]*100:.0f}% of *activated* accounts "
        f"convert. Fix the top of the funnel; monetization already works."
    )

# ===== RETENTION =====
with tab_retention:
    st.subheader("Cohort Retention")
    st.markdown("Each row is a monthly cohort; each column is weeks since signup. "
                "Darker = higher % still active.")
    retention = load("retention_cohorts")
    pivot = retention.pivot_table(
        index="cohort_month", columns="week_number_post_trial", values="retention_rate"
    )
    st.dataframe(
        pivot.style.format("{:.0%}", na_rep="").background_gradient(cmap="Greens", axis=None),
        width="stretch"
    )
    st.caption("Cohorts are small (often 15–35 accounts), so early-week rates are "
               "noisy and can recover week-to-week — an honest property of the data.")

# ===== EXPERIMENTS =====
with tab_experiments:
    st.subheader("Three Embedded Experiments")
    st.markdown("Demonstrating the full experimentation lifecycle — including the "
                "realistic, less-taught case of **underpowered results**.")

    st.markdown("##### 1 · Onboarding Redesign — Randomized A/B")
    exp1 = load("exp_onboarding_assignment")
    e1 = exp1.groupby("variant")["did_activate"].agg(["count", "mean"])
    c1, c2 = st.columns([1, 2])
    c1.dataframe(e1.style.format({"mean": "{:.1%}"}))
    c2.markdown(
        "33.0% vs 33.0% activation — **p = 0.977**, inconclusive. Power analysis: "
        "we'd need ~2,200 accounts/arm (vs ~750 available) to detect the expected "
        "4pp effect. **Honest conclusion: 'underpowered, need more data' — not 'failed.'**"
    )

    st.markdown("##### 2 · Trial Discount Framing — A/B + CUPED")
    exp2 = load("exp_discount_assignment")
    e2 = exp2.groupby("variant")["chose_annual"].agg(["count", "mean"])
    c1, c2 = st.columns([1, 2])
    c1.dataframe(e2.style.format({"mean": "{:.1%}"}))
    c2.markdown(
        "Naive test inconclusive (p = 0.486). **CUPED** variance reduction cut "
        "variance 12% and standard error 6.4% — a more precise estimate from the "
        "same data. **CUPED's value shows in the standard error, not the p-value.**"
    )

    st.markdown("##### 3 · Upgrade Nudge — Causal Inference ⭐")
    exp3 = load("exp_nudge_assignment")
    def label_group(row):
        if row["exp3_nudged"]:
            return "nudged"
        elif row["crossed_threshold"]:
            return "crossed_before_nudge"
        else:
            return "never_crossed"
    exp3["group"] = exp3.apply(label_group, axis=1)
    e3 = exp3.groupby("group")["late_upgraded"].agg(["count", "mean"])
    c1, c2 = st.columns([1, 2])
    c1.dataframe(e3.style.format({"mean": "{:.1%}"}))
    c2.markdown(
        "**The confounding trap:** A naive comparison (nudged 58% vs never-crossed 6%) "
        "suggests a **+52pp lift** — a 9x improvement. But the nudge wasn't randomized; "
        "it reached self-selected heavy users who upgrade anyway. Comparing nudged vs "
        "**crossed-before-nudge** (both heavy users) collapses the effect to **−0.4pp** — "
        "indistinguishable from zero across three methods. **The 52pp was almost entirely "
        "confounding.**"
    )

# ===== LIFETIME =====
with tab_lifetime:
    st.subheader("Customer Lifetime — Survival Analysis")
    from lifelines import KaplanMeierFitter
    import matplotlib.pyplot as plt

    churn = load("churn_features")
    kmf = KaplanMeierFitter()
    kmf.fit(churn["months_retained"], event_observed=churn["churned"].astype(int))

    fig, ax = plt.subplots(figsize=(9, 5))
    kmf.plot_survival_function(ax=ax)
    ax.axhline(y=0.5, color="#E15759", linestyle="--", alpha=0.6, label="50% survival")
    ax.set_title("Paid Account Survival Curve (Kaplan-Meier)")
    ax.set_xlabel("Months since conversion")
    ax.set_ylabel("Probability still active")
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(True, alpha=0.3)

    c1, c2 = st.columns([2, 1])
    c1.pyplot(fig)
    c2.metric("Median survival", f"{kmf.median_survival_time_:.0f} months")
    c2.markdown(
        "Half of paid accounts remain active ~18 months after conversion. "
        "Kaplan-Meier correctly handles **censoring** — accounts still active at the "
        "window's end aren't counted as churned, which a naive average gets wrong."
    )
    st.caption("Segmented survival by signup channel did not show reliable separation "
               "at this sample size — differences fall within small-sample noise.")