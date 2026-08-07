with source as (
    select * from {{ source('taskflow_raw', 'free_account_weekly_usage') }}
),
    renamed as (
        select
            account_id,
            week_number_post_trial,
            cast(week_date as date) as week_date,
            task_count,
            active
        from source
    )
select * from renamed