-- Extend the EDA joint table with contribution to sampled records and Bad outcomes.
WITH bands(band_order, band_label) AS (
    VALUES (1, '<=12 months'), (2, '>12-24 months'), (3, '>24-36 months'), (4, '>36 months')
), summary AS (
    SELECT checking_status, duration_band_order, COUNT(*) AS total_records, SUM(is_bad) AS bad_records
    FROM credit_reporting GROUP BY checking_status, duration_band_order
), complete AS (
    SELECT l.category_code, l.category_label, b.band_order, b.band_label,
           COALESCE(s.total_records, 0) AS total_records, COALESCE(s.bad_records, 0) AS bad_records
    FROM category_lookup AS l CROSS JOIN bands AS b
    LEFT JOIN summary AS s ON s.checking_status = l.category_code AND s.duration_band_order = b.band_order
    WHERE l.variable_name = 'checking_status'
)
SELECT category_code AS checking_status_code, category_label AS checking_status_label,
       band_label AS duration_band, total_records, bad_records,
       ROUND(100.0 * bad_records / NULLIF(total_records, 0), 2) AS bad_share_pct,
       ROUND(100.0 * total_records / NULLIF(SUM(total_records) OVER (), 0), 2) AS share_of_all_records_pct,
       ROUND(100.0 * bad_records / NULLIF(SUM(bad_records) OVER (), 0), 2) AS share_of_all_bad_records_pct,
       CASE WHEN total_records < 30 THEN 1 ELSE 0 END AS sparse_flag
FROM complete ORDER BY category_code, band_order;
