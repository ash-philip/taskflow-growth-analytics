with usage as (
    select * from {{ ref('stg_free_account_weekly_usage') }}
),

cohorts as (
    select * from {{ ref('int_account_cohorts') }}
),

joined as (
    select
        u.account_id,
        c.cohort_week_date,
        u.week_number_post_trial,
        u.active

    from usage as u
    inner join cohorts as c on u.account_id = c.account_id
)

select * from joined