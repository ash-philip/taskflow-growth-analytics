with funnel as (
    select * from {{ ref('funnel_activation') }}
),

summary as (
    select
        count(*) as total_signups,
        countif(did_activate) as total_activated,
        countif(did_convert) as total_converted,

        round(countif(did_activate) / count(*), 4) as activation_rate,
        round(countif(did_convert) / count(*), 4) as conversion_rate_overall,
        round(countif(did_convert) / countif(did_activate), 4) as conversion_rate_of_activated
    from funnel
)

select * from summary