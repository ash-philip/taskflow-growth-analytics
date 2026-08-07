with source as (

    select * from {{ source('taskflow_raw', 'subscription_summary') }}

),

renamed as (

    select
        account_id,
        months_retained,
        cast(final_seats as int) as final_seats,
        churned,
        upgrade_path,
        plan

    from source

)

select * from renamed