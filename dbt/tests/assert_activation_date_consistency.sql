-- activation_date should be populated if and only if activated = true.
-- Any rows returned here mean that assumption is broken somewhere.

select account_id, activated, activation_date
from {{ ref('stg_activation') }}
where (activated = true and activation_date is null)
   or (activated = false and activation_date is not null)
