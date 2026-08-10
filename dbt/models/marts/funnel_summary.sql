with funnel as (
    select * from {{ ref('funnel_activation') }}
),

summary as (
    select
        count(*) as total_signups,
        countif(did_activate) as total_activated,
        countif(did_convert) as total_converted,

        -- activation rate = activated / signups, rounded to 4 decimals
        round(countif(did_activate) / count(*), 4) as activation_rate,

        -- conversion rate among ALL signups = converted / signups
        round(countif(did_convert) / count(*), 4) as conversion_rate_overall,

        -- conversion rate among ACTIVATED only = converted / activated
        round(countif(did_convert) / countif(did_activate), 4) as conversion_rate_of_activated

    from funnel
)

select * from summary