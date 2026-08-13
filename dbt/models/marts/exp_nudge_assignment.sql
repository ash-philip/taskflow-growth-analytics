with late_upgrade as (
    select * from {{ ref('stg_free_account_late_upgrade') }}
),

final as (
    select
        account_id,
        crossed_threshold,
        exp3_nudged,
        late_upgraded

    from late_upgrade
)

select * from final