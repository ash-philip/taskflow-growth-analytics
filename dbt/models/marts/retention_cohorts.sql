with activity as (
    select
        date_trunc(cohort_week_date, month) as cohort_month,
        account_id,
        week_number_post_trial,
        active
    from {{ ref('int_cohort_weekly_activity') }}
),

-- separate CTE so cohort_size is the full cohort, a fixed denominator across all weeks
cohort_sizes as (
    select
        cohort_month,
        count(distinct account_id) as cohort_size
    from activity
    group by cohort_month
),

weekly_active as (
    select
        cohort_month,
        week_number_post_trial,
        -- case returns null when inactive; count(distinct) ignores nulls, so this counts active accounts
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