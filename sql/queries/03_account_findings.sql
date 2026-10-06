-- Validate the three main EDA account comparisons; include documented empty levels.
WITH categories AS (
    SELECT 'checking_status' AS variable_name, checking_status AS code, is_bad FROM credit_reporting
    UNION ALL SELECT 'credit_history', credit_history, is_bad FROM credit_reporting
    UNION ALL SELECT 'savings', savings, is_bad FROM credit_reporting
), summary AS (
    SELECT variable_name, code, COUNT(*) AS total_records, SUM(is_bad) AS bad_records
    FROM categories GROUP BY variable_name, code
)
SELECT l.variable_name, l.category_code, l.category_label,
       COALESCE(s.total_records, 0) AS total_records, COALESCE(s.bad_records, 0) AS bad_records,
       ROUND(100.0 * s.bad_records / NULLIF(s.total_records, 0), 2) AS bad_share_pct,
       CASE WHEN COALESCE(s.total_records, 0) < 30 THEN 1 ELSE 0 END AS sparse_flag
FROM category_lookup AS l
LEFT JOIN summary AS s ON s.variable_name = l.variable_name AND s.code = l.category_code
WHERE l.variable_name IN ('checking_status', 'credit_history', 'savings')
ORDER BY CASE l.variable_name WHEN 'checking_status' THEN 1 WHEN 'credit_history' THEN 2 ELSE 3 END, l.display_order;
