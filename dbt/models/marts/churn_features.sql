with summary as (
    select * from {{ ref('stg_subscription_summary') }}
),

accounts as (
    select * from {{ ref('stg_accounts') }}
),

features as (
    select
        s.account_id,
        s.churned,
        s.plan,
        s.upgrade_path,
        s.final_seats,
        a.signup_channel,
        a.company_size_bucket,

        -- kept for survival analysis (duration), NOT the churn classifier:
        -- it leaks the churn outcome since it's when a churned account left
        s.months_retained

    from summary as s
    left join accounts as a on s.account_id = a.account_id
)

select * from features