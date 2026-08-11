with weekly_usage as (
    select * from {{ ref('stg_free_account_weekly_usage') }}
),

first_week as (
    select
        account_id,
        week_date as cohort_week_date,
        week_number_post_trial

    from weekly_usage

    -- keep only each account's FIRST weekly row
    qualify row_number() over (
        partition by account_id
        order by week_date
    ) = 1
)

select
    account_id,
    cohort_week_date
from first_week