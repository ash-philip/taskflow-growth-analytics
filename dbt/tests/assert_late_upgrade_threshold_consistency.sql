select
    account_id,
    crossed_threshold,
    threshold_crossed_date
from {{ ref('stg_free_account_late_upgrade') }}
where (crossed_threshold = true and threshold_crossed_date is null)
   or (crossed_threshold = false and threshold_crossed_date is not null)