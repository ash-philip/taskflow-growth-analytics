with activation as (
    select * from {{ ref('stg_activation') }}
),

eligible as (
    select
        account_id,
        exp1_variant as variant,
        activated as did_activate

    from activation
    where exp1_eligible = true      -- keep only accounts that were in the experiment
)

select * from eligible