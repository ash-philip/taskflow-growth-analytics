select
    cohort_month,
    week_number_post_trial,
    count(*) as row_count

from {{ ref('retention_cohorts') }}

group by cohort_month, week_number_post_trial

having count(*) > 1