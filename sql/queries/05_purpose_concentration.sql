-- Rank by Bad counts, not by unstable rates from tiny purposes.
WITH summary AS (
    SELECT purpose, COUNT(*) AS total_records, SUM(is_bad) AS bad_records
    FROM credit_reporting GROUP BY purpose
), complete AS (
    SELECT l.category_code, l.category_label, l.display_order,
           COALESCE(s.total_records, 0) AS total_records, COALESCE(s.bad_records, 0) AS bad_records
    FROM category_lookup AS l LEFT JOIN summary AS s ON s.purpose = l.category_code
    WHERE l.variable_name = 'purpose'
)
SELECT category_code AS purpose_code, category_label AS purpose_label,
       total_records, bad_records,
       ROUND(100.0 * bad_records / NULLIF(total_records, 0), 2) AS bad_share_pct,
       ROUND(100.0 * bad_records / NULLIF(SUM(bad_records) OVER (), 0), 2) AS share_of_all_bad_records_pct,
       DENSE_RANK() OVER (ORDER BY bad_records DESC) AS bad_count_rank,
       CASE WHEN total_records < 30 THEN 1 ELSE 0 END AS sparse_flag
FROM complete ORDER BY bad_records DESC, display_order;
