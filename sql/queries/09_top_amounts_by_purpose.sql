-- Three highest recorded amounts per observed purpose, deterministic ties.
-- This is a record drilldown, not a risk ranking; amounts are transformed.
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY purpose ORDER BY credit_amount DESC, record_id) AS amount_rank,
           COUNT(*) OVER (PARTITION BY purpose) AS purpose_total_records,
           SUM(is_bad) OVER (PARTITION BY purpose) AS purpose_bad_records
    FROM credit_reporting
)
SELECT purpose, purpose_label, amount_rank, record_id,
       credit_amount AS recorded_credit_amount, duration_months, checking_status_label, credit_risk_label,
       purpose_total_records, purpose_bad_records,
       ROUND(100.0 * purpose_bad_records / purpose_total_records, 2) AS purpose_bad_share_pct,
       CASE WHEN purpose_total_records < 30 THEN 1 ELSE 0 END AS sparse_flag
FROM ranked WHERE amount_rank <= 3 ORDER BY purpose, amount_rank;
