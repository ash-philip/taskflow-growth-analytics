with source as (
    select * from {{ source('taskflow_raw','free_account_late_upgrade')}}
),
renamed as (
    select
        account_id,
        crossed_threshold,
        cast(threshold_crossed_date as date) as threshold_crossed_date,
        exp3_nudged,
        late_upgraded,
        cast(late_upgrade_date as date) as late_upgrade_date
    from source
)
select * from renamed