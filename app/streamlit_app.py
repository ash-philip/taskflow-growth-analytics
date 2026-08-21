import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from lifelines import KaplanMeierFitter

st.set_page_config(
    page_title="TaskFlow Growth Analytics",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load(name):
    return pd.read_csv(DATA_DIR / f"{name}.csv")


funnel = load("funnel_summary")

# ---------- HERO ----------
st.title("TaskFlow Growth Analytics")
st.markdown(
    "#### A growth analytics case study on a simulated B2B SaaS product"
)

with st.expander("About this project"):
    st.markdown("""
    For this portfolio project, I built "TaskFlow," a simulated B2B project management app, 
    and engineered two years of customer data from scratch. Then, I analyzed it exactly how 
    a real growth team would. Why use synthetic data? Because knowing the underlying truth 
    behind every metric allows me to test the analytics themselves. The goal is to prove whether 
    standard growth models actually uncover the truth or get fooled by the data. This project is 
    about moving beyond running an analysis to knowing exactly when to trust the results.
    """)

st.divider()

# ---------- TABS ----------
tab_overview, tab_funnel, tab_retention, tab_experiments, tab_lifetime = st.tabs(
    ["Overview", "Funnel", "Retention", "Experiments", "Lifetime"]
)

# ===== OVERVIEW =====
with tab_overview:
    # Custom CSS for the dark blueprint and violet aesthetic
    st.markdown("""
    <style>
        .intro-text {
            max-width: 800px;
            color: #d1d1d6;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 25px;
        }
        .metric-card {
            background-color: #1c1c21;
            border: 1px solid #2d2d35;
            border-radius: 8px;
            padding: 20px;
            height: 100%;
        }
        .card-title {
            color: #8b5cf6; 
            font-weight: 600;
            font-size: 14px;
            letter-spacing: 1px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .card-question {
            color: #a1a1aa;
            font-size: 14px;
            line-height: 1.4;
        }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("The story")

    st.markdown(
        '<div class="intro-text">TaskFlow faces the exact same lifecycle challenges as any scaling SaaS product: thousands sign up, a fraction converts to paid, and some inevitably churn. I designed this analysis to tackle three existential questions every growth team must answer:</div>',
        unsafe_allow_html=True)

    # 3-column grid for the questions
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="card-title">Friction</div>
                <div class="card-question">Where exactly are users dropping out of the funnel?</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="metric-card">
                <div class="card-title">Retention</div>
                <div class="card-question">What specific behaviors drive long-term loyalty?</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="metric-card">
                <div class="card-title">Impact</div>
                <div class="card-question">When we launch something new, does it actually move the needle?</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<br><div class="intro-text">Here is what the analysis revealed.</div>', unsafe_allow_html=True)

    st.divider()

    # Finding 1
    st.markdown("##### Finding 1")
    a, b = st.columns([1, 3])
    a.metric("Get started", "33%")
    b.markdown("""
    **Activation is the Primary Bottleneck.** 

    Most sign-ups churn before they ever truly use the app. 
    However, those who successfully complete their first core action almost always convert to paid. 
    The best way to drive revenue is to fix the onboarding experience so more users reach that first milestone.
    """)

    st.divider()

    # Finding 2
    st.markdown("##### Finding 2")
    a, b = st.columns([1, 3])
    a.metric("Clear answers", "1 of 3")
    b.markdown("""
    **The Value of Inconclusive Results.** 

    Out of three product experiments, two lacked the statistical 
    power to declare a clear winner. A common mistake is forcing a conclusion from noisy data just to 
    show a result. By applying rigorous statistical testing, the true takeaway was simply that we need a 
    larger sample size. Preventing false positives holds just as much value as finding real wins.
    """)

    st.divider()

    # Finding 3
    st.markdown("##### Finding 3")
    a, b = st.columns([1, 3])
    a.metric("Apparent lift", "9x")
    b.markdown("""
    **The Danger of Selection Bias.** 

    An upgrade nudge appeared to drive a massive 9x lift in conversions. 
    This was a classic trap because it only targeted power users who were already highly engaged and likely to upgrade anyway. 
    When controlled for baseline engagement levels, the causal effect of the pop-up completely vanished. 
    The high metric simply reflected existing user behavior rather than the success of the nudge.
    """)

    st.divider()
    st.caption("Open the tabs above to see the analysis behind each finding.")

# ===== FUNNEL =====
with tab_funnel:
    st.subheader("Activation Funnel")

    stages = ["Signups", "Activated", "Converted"]
    values = [
        int(funnel["total_signups"][0]),
        int(funnel["total_activated"][0]),
        int(funnel["total_converted"][0]),
    ]

    fig_funnel = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        marker={"color": ["#8b5cf6", "#7c3aed", "#6d28d9"]},  # Adjusted to match violet accent
        connector={"line": {"color": "#3A4152"}},
    ))
    fig_funnel.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E8EAED"),
    )

    c1, c2 = st.columns([2, 1])
    c1.plotly_chart(fig_funnel, use_container_width=True)
    with c2:
        st.metric("Activation rate", f"{funnel['activation_rate'][0] * 100:.1f}%")
        st.metric("Conversion (of activated)", f"{funnel['conversion_rate_of_activated'][0] * 100:.1f}%")
        st.info(
            f"Most drop-off happens early. Only "
            f"{funnel['activation_rate'][0] * 100:.0f}% of signups become active users, "
            f"but {funnel['conversion_rate_of_activated'][0] * 100:.0f}% of active users go "
            f"on to pay. The problem is getting people started, not getting them to pay."
        )

# ===== RETENTION =====
with tab_retention:
    st.subheader("Cohort Retention")
    st.markdown("Each row is a monthly cohort; columns are milestone weeks since signup. "
                "Hover any cell for the exact retention rate.")

    retention = load("retention_cohorts")
    pivot = retention.pivot_table(
        index="cohort_month", columns="week_number_post_trial", values="retention_rate"
    )

    # keep only milestone weeks that actually exist in the data
    milestones = [0, 1, 2, 4, 8, 12, 24]
    milestones = [w for w in milestones if w in pivot.columns]
    pivot = pivot[milestones]

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"Week {c}" for c in pivot.columns],
        y=[str(i) for i in pivot.index],
        colorscale="RdYlGn",
        zmin=0.4, zmax=1,
        xgap=3, ygap=3,
        hovertemplate="Cohort %{y}<br>%{x}<br>Retention: %{z:.0%}<extra></extra>",
        colorbar=dict(title="Retention", tickformat=".0%"),
    ))
    fig_heat.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=520,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E8EAED"),
        xaxis=dict(title="Weeks since signup", showgrid=False, side="top"),
        yaxis=dict(title="Cohort month", showgrid=False, autorange="reversed"),
    )

    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("Showing milestone weeks (0, 1, 2, 4, 8, 12, 24). Cohorts are small "
               "(often 15–35 accounts), so rates are noisy — an honest property of the data. "
               "Blank cells are cohorts too recent to have reached that week.")

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
    c2.markdown("""
        The onboarding redesign experiment yielded identical 33.0% activation rates across 
        both the control and treatment groups. A subsequent power analysis revealed the 
        test only had about 750 accounts per arm, falling well short of the 2,200 required 
        to detect a four percentage point effect. The honest takeaway is simply that the test lacked sufficient data.
    """
                )

    st.markdown("##### 2 · Trial Discount Framing — A/B + CUPED")
    exp2 = load("exp_discount_assignment")
    e2 = exp2.groupby("variant")["chose_annual"].agg(["count", "mean"])
    c1, c2 = st.columns([1, 2])
    c1.dataframe(e2.style.format({"mean": "{:.1%}"}))
    c2.markdown("""
        A standard A/B test evaluating trial discount framing returned an inconclusive p-value of 0.486. 
        Applying CUPED variance reduction to the exact same dataset successfully decreased variance by 12% 
        and reduced the standard error by 6.4%. This step delivered a significantly more precise estimate 
        without requiring any additional traffic.
    """
                )

    st.markdown("##### 3 · Upgrade Nudge — Causal Inference")
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
    c2.markdown("""
        An upgrade nudge initially showed a 9x improvement and suggested a massive 52 percentage point 
        lift in conversions. This raw comparison ignored a major selection bias because the feature specifically 
        targeted heavy users. Comparing the nudged cohort against an equally engaged control group collapsed 
        the actual effect to a statistically insignificant negative 0.4 percentage points. The initial success 
        metric was almost entirely driven by confounding user behavior rather than the feature itself.
    """
                )

# ===== LIFETIME =====
with tab_lifetime:
    st.subheader("Customer Lifetime — Survival Analysis")

    churn = load("churn_features")
    kmf = KaplanMeierFitter()
    kmf.fit(churn["months_retained"], event_observed=churn["churned"].astype(int))

    sf = kmf.survival_function_
    ci = kmf.confidence_interval_
    x = sf.index.tolist()
    y = sf.iloc[:, 0].tolist()
    lower = ci.iloc[:, 0].tolist()
    upper = ci.iloc[:, 1].tolist()

    fig_surv = go.Figure()
    # confidence band
    fig_surv.add_trace(go.Scatter(
        x=x + x[::-1], y=upper + lower[::-1],
        fill="toself", fillcolor="rgba(139,92,246,0.15)",  # Adjusted to match violet accent
        line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", showlegend=False,
    ))
    # survival line
    fig_surv.add_trace(go.Scatter(
        x=x, y=y, mode="lines", line=dict(color="#8b5cf6", width=3),  # Adjusted to match violet accent
        name="Survival", line_shape="hv",
        hovertemplate="Month %{x}<br>Still active: %{y:.0%}<extra></extra>",
    ))
    # 50% reference line
    fig_surv.add_hline(y=0.5, line_dash="dash", line_color="#E15759",
                       annotation_text="50% survival", annotation_position="top right")

    fig_surv.update_layout(
        margin=dict(l=20, r=20, t=20, b=20), height=420,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E8EAED"),
        xaxis=dict(title="Months since conversion", showgrid=True, gridcolor="#2A303C"),
        yaxis=dict(title="Probability still active", range=[0, 1], tickformat=".0%",
                   showgrid=True, gridcolor="#2A303C"),
        showlegend=False,
    )

    c1, c2 = st.columns([2, 1])
    c1.plotly_chart(fig_surv, use_container_width=True)
    with c2:
        st.metric("Median survival", f"{kmf.median_survival_time_:.0f} months")
        st.markdown("""
        Half of paid accounts remain active 18 months after conversion. The Kaplan-Meier method accurately 
        handles data censoring. It keeps accounts still active at the end of the observation window in 
        the calculation to guarantee a precise metric.
        """
                    )
    st.caption(
        "Segmented survival by signup channel lacks reliable separation at this sample size. Any observed differences "
        "fall entirely within statistical noise.")