"""
Configuration for the TaskFlow synthetic data generator.

Every rate and effect size below is a design choice, chosen to be realistic
and moderate, not a real-world benchmark. They exist so the later statistical
methods (power analysis, A/B testing, CUPED, causal inference) have real,
recoverable signal to work with.
"""

import datetime as dt

RANDOM_SEED = 42

# --- Simulation window ---
SIM_START = dt.date(2024, 1, 1)
SIM_END = dt.date(2025, 12, 31)          # 24 months
SIM_DAYS = (SIM_END - SIM_START).days + 1

# --- Acquisition channels ---
CHANNELS = {
    "organic_search": 0.35,
    "paid_search": 0.25,
    "content": 0.15,
    "referral": 0.15,
    "direct": 0.10,
}

# --- Company size (affects eventual seat count / expansion potential) ---
COMPANY_SIZE_BUCKETS = {
    "small": 0.60,     # 1-10 employees
    "medium": 0.30,    # 11-50
    "large": 0.10,     # 51+
}

# --- Plans ---
PLAN_PRICES = {"free": 0, "pro": 12, "team": 29}   # per user / month
TRIAL_LENGTH_DAYS = 14

# --- Activation ---
# Activation = verify email + create first project + invite >=1 teammate,
# all within ACTIVATION_WINDOW_DAYS of signup.
BASE_ACTIVATION_RATE = 0.32               # control / pre-experiment baseline
ACTIVATION_WINDOW_DAYS = 7

# --- Experiment 1: Onboarding redesign (RANDOMIZED) ---
EXP1_NAME = "onboarding_redesign"
EXP1_START = dt.date(2024, 10, 1)         # ~month 10
EXP1_LIFT = 0.04                          # +4pp absolute lift in activation rate
EXP1_SPLIT = 0.5                          # 50/50 randomization

# --- Experiment 2: Trial discount framing (RANDOMIZED) ---
EXP2_NAME = "trial_discount_framing"
EXP2_START = dt.date(2024, 4, 1)          # runs most of the simulation
BASE_ANNUAL_SELECT_RATE = 0.22            # control: "Save 20%" framing
EXP2_LIFT = 0.04                          # +4pp for "2 months free" framing
EXP2_SPLIT = 0.5

# --- Experiment 3: Usage-threshold upgrade nudge (NOT RANDOMIZED) ---
EXP3_NAME = "usage_threshold_nudge"
EXP3_START = dt.date(2025, 5, 1)          # ~month 16
EXP3_WEEKLY_TASK_THRESHOLD = 15           # tasks/week on Free plan -> nudge shown
EXP3_TRUE_LIFT = 0.06                     # genuine causal lift from the nudge, on top of the engagement confound

# --- Latent engagement propensity ---
# Hidden per-account value in [0,1], Beta(2,5) so most accounts are low/moderate
# and a minority highly engaged. Drives activation, usage, conversion, and churn.
# A real analyst never observes this directly, only proxies like past usage.
ENGAGEMENT_BETA_A = 2
ENGAGEMENT_BETA_B = 5

# --- Churn ---
CHURN_INACTIVITY_DAYS = 30
BASE_MONTHLY_CHURN_HAZARD = 0.045         # ~4.5%/month baseline, modulated by propensity
