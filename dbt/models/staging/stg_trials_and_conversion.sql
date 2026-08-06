with source as (
    select * from {{ source('taskflow_raw', 'trials_and_conversion') }}
),
renamed as (
    select
        account_id,
        cast(trial_end_date as date) as trial_end_date,
        trial_observed,
        
        case
            when converted = 1.0 then true
            when converted = 0.0 then false
            else null
        end as converted,
        plan,
        cast(seats as int64) as seats,
        billing_cycle,
        mrr,
        exp2_eligible,
        exp2_variant,
        trial_period_task_count
    from source
)
select * from renamed
