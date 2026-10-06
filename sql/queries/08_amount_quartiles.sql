-- NTILE(4) ranks recorded amounts; record_id makes ties deterministic.
-- Equal credit amounts can be split across quartiles. No exposure/value sums.
WITH ranked AS (
    SELECT *, NTILE(4) OVER (ORDER BY credit_amount, record_id) AS amount_quartile
    FROM credit_reporting
)
SELECT amount_quartile, COUNT(*) AS total_records, SUM(is_bad) AS bad_records,
       MIN(credit_amount) AS min_recorded_amount, MAX(credit_amount) AS max_recorded_amount,
       ROUND(100.0 * SUM(is_bad) / COUNT(*), 2) AS bad_share_pct,
       SUM(CASE WHEN duration_months <= 12 THEN 1 ELSE 0 END) AS duration_le_12_records,
       SUM(CASE WHEN duration_months > 12 AND duration_months <= 24 THEN 1 ELSE 0 END) AS duration_13_24_records,
       SUM(CASE WHEN duration_months > 24 THEN 1 ELSE 0 END) AS duration_gt_24_records,
       ROUND(100.0 * SUM(CASE WHEN duration_months > 24 THEN 1 ELSE 0 END) / COUNT(*), 2) AS duration_gt_24_share_pct,
       CASE WHEN COUNT(*) < 30 THEN 1 ELSE 0 END AS sparse_flag
FROM ranked GROUP BY amount_quartile ORDER BY amount_quartile;
