-- Duration <=12, >12-24, >24 months: composition and outcome context, not causal adjustment.
WITH summary AS (
    SELECT employment_duration, COUNT(*) AS total_records,
           SUM(CASE WHEN duration_months <= 12 THEN 1 ELSE 0 END) AS short_records,
           SUM(CASE WHEN duration_months <= 12 THEN is_bad ELSE 0 END) AS short_bad,
           SUM(CASE WHEN duration_months > 12 AND duration_months <= 24 THEN 1 ELSE 0 END) AS medium_records,
           SUM(CASE WHEN duration_months > 12 AND duration_months <= 24 THEN is_bad ELSE 0 END) AS medium_bad,
           SUM(CASE WHEN duration_months > 24 THEN 1 ELSE 0 END) AS long_records,
           SUM(CASE WHEN duration_months > 24 THEN is_bad ELSE 0 END) AS long_bad
    FROM credit_reporting GROUP BY employment_duration
)
SELECT l.category_code AS employment_code, l.category_label AS employment_label,
       COALESCE(s.total_records, 0) AS total_records,
       COALESCE(s.short_records, 0) AS short_total_records, COALESCE(s.short_bad, 0) AS short_bad_records,
       ROUND(100.0 * s.short_records / NULLIF(s.total_records, 0), 2) AS short_mix_pct,
       ROUND(100.0 * s.short_bad / NULLIF(s.short_records, 0), 2) AS short_bad_share_pct,
       CASE WHEN COALESCE(s.short_records, 0) < 30 THEN 1 ELSE 0 END AS short_sparse_flag,
       COALESCE(s.medium_records, 0) AS medium_total_records, COALESCE(s.medium_bad, 0) AS medium_bad_records,
       ROUND(100.0 * s.medium_records / NULLIF(s.total_records, 0), 2) AS medium_mix_pct,
       ROUND(100.0 * s.medium_bad / NULLIF(s.medium_records, 0), 2) AS medium_bad_share_pct,
       CASE WHEN COALESCE(s.medium_records, 0) < 30 THEN 1 ELSE 0 END AS medium_sparse_flag,
       COALESCE(s.long_records, 0) AS long_total_records, COALESCE(s.long_bad, 0) AS long_bad_records,
       ROUND(100.0 * s.long_records / NULLIF(s.total_records, 0), 2) AS long_mix_pct,
       ROUND(100.0 * s.long_bad / NULLIF(s.long_records, 0), 2) AS long_bad_share_pct,
       CASE WHEN COALESCE(s.long_records, 0) < 30 THEN 1 ELSE 0 END AS long_sparse_flag,
       CASE WHEN COALESCE(s.total_records, 0) < 30 THEN 1 ELSE 0 END AS sparse_flag
FROM category_lookup AS l LEFT JOIN summary AS s ON s.employment_duration = l.category_code
WHERE l.variable_name = 'employment_duration' ORDER BY l.display_order;
