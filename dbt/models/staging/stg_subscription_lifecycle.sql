with source as (
    select * from {{ source('taskflow_raw','subscription_lifecycle') }}
),
renamed as (
    select
        account_id,
        month_number,
        cast(month_date as date) as month_date,
        cast(seats as int) as seats,
        churned_this_month
    from source
)
select * from renamed