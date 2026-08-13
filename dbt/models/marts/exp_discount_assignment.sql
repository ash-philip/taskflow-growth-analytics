with trials as (
    select * from {{ ref('stg_trials_and_conversion') }}
),

eligible as (
    select
        account_id,
        exp2_variant as variant,
        billing_cycle = 'annual' as chose_annual,
        trial_period_task_count

    from trials
    where exp2_eligible = true
      and converted = true-- must have converted to be in the outcome population
)

select * from eligible