select
    account_id,
    week_number_post_trial,
    count(*) as row_count

from {{ ref('stg_free_account_weekly_usage') }}

group by account_id, week_number_post_trial

having count(*) > 1