with source as (
    select * from {{ source('taskflow_raw', 'activation') }}
),
renamed as (
    select
        account_id,
	activated,
        cast(activation_date as date) as activation_date,
	exp1_eligible,
	exp1_variant
    from source
)
select * from renamed
