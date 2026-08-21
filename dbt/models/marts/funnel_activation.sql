with accounts as (
    select * from {{ ref('stg_accounts') }}
),

activation as (
    select * from {{ ref('stg_activation') }}
),

conversion as (
    select * from {{ ref('stg_trials_and_conversion') }}
),

funnel as (
    select
        a.account_id,
        a.signup_date,
        a.signup_channel,
        a.company_size_bucket,

        true as did_signup,  -- every account in stg_accounts has signed up by definition
        act.activated as did_activate,
        conv.converted as did_convert

    from accounts as a
    left join activation as act on a.account_id = act.account_id
    left join conversion as conv on a.account_id = conv.account_id
)

select * from funnel