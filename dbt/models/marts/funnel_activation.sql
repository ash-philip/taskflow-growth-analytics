with accounts as (
    select * from {{ ref('stg_accounts') }}
),

activation as (
    select * from {{ ref('stg_activation') }}
),

conversion as (
    select * from {{ ref('stg_trials_and_conversion') }}    -- which staging model has conversion data?
),

funnel as (
    select
        a.account_id,
        a.signup_date,
        a.signup_channel,
        a.company_size_bucket,

        -- everyone in stg_accounts signed up, so this is always true
        true as did_signup,

        -- from the activation table
        act.activated as did_activate,

        -- from the conversion table
        conv.converted as did_convert

    from accounts as a
    left join activation as act on a.account_id = act.account_id
    left join conversion as conv on a.account_id = conv.account_id    -- which alias?

)

select * from funnel