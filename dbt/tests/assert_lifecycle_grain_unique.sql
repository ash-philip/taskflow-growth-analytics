select
    account_id,
    month_number,
    count(*) as row_count
from {{ ref('stg_subscription_lifecycle') }}
    group by account_id, month_number
    having count(*) > 1