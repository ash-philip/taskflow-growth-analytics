-- converted should be populated if and only if trial_observed = true.
-- Mirrors the activation_date/activated check -- same underlying pattern
-- from how Phase 1's simulate_subscriptions.py set this column.

select account_id, trial_observed, converted
from {{ ref('stg_trials_and_conversion') }}
where (trial_observed = true and converted is null)
   or (trial_observed = false and converted is not null)
