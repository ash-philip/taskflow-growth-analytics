with source as (

    select * from {{ source('taskflow_raw', 'accounts') }}

),

renamed as (

    select
        account_id,
        company_name,
        cast(signup_date as date) as signup_date,
        signup_channel,
        company_size_bucket

    from source

)

select * from renamed
