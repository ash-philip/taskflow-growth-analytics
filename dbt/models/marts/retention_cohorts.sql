with activity as (
    select
        date_trunc(cohort_week_date, month) as cohort_month,
        account_id,
        week_number_post_trial,
        active
    from {{ ref('int_cohort_weekly_activity') }}
),

-- cohort size: distinct accounts per month-cohort (same for all week numbers)
cohort_sizes as (
    select
        cohort_month,
        count(distinct account_id) as cohort_size
    from activity
    group by cohort_month
),

-- active accounts at each (cohort_month, week_number)
weekly_active as (
    select
        cohort_month,
        week_number_post_trial,
        count(distinct case when active then account_id end) as active_accounts
    from activity
    group by cohort_month, week_number_post_trial
),

retention as (
    select
        wa.cohort_month,
        wa.week_number_post_trial,
        cs.cohort_size,
        wa.active_accounts,
        round(wa.active_accounts / cs.cohort_size, 4) as retention_rate

    from weekly_active as wa
    inner join cohort_sizes as cs on wa.cohort_month = cs.cohort_month
)

select * from retention
order by cohort_month, week_number_post_trial