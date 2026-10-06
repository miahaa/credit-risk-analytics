-- Descriptive drilldown, not an underwriting policy or individual risk score.
SELECT record_id, duration_months, credit_amount AS recorded_credit_amount,
       checking_status_label, credit_history_label, purpose_label, credit_risk_label,
       COUNT(*) OVER () AS segment_total_records,
       SUM(is_bad) OVER () AS segment_bad_records,
       ROUND(100.0 * SUM(is_bad) OVER () / COUNT(*) OVER (), 2) AS segment_bad_share_pct,
       CASE WHEN COUNT(*) OVER () < 30 THEN 1 ELSE 0 END AS sparse_flag
FROM credit_reporting
WHERE duration_months > 24 AND checking_status IN (1, 2)
ORDER BY duration_months DESC, credit_amount DESC, record_id;
