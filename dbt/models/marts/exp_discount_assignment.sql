with trials as (
    select * from {{ ref('stg_trials_and_conversion') }}
),

eligible as (
    select
        account_id,
        exp2_variant as variant,
        billing_cycle = 'annual' as chose_annual,
        trial_period_task_count  -- pre-experiment covariate, used for CUPED variance reduction
    from trials
    where exp2_eligible = true
      and converted = true  -- only converted accounts made the annual-vs-monthly choice
)

select * from eligible