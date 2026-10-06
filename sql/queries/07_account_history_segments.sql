-- Account condition = checking_status IN (1, 2).
-- History condition = credit_history IN (0, 1).
-- These descriptive flags are not a score or a lending recommendation.
WITH flagged AS (
    SELECT CASE WHEN checking_status IN (1, 2) THEN 1 ELSE 0 END AS account_condition,
           CASE WHEN credit_history IN (0, 1) THEN 1 ELSE 0 END AS history_condition, is_bad
    FROM credit_reporting
), definitions(account_condition, history_condition, segment_label) AS (
    VALUES (0, 0, 'Neither condition'), (1, 0, 'Account condition only'),
           (0, 1, 'History condition only'), (1, 1, 'Both conditions')
), summary AS (
    SELECT account_condition, history_condition, COUNT(*) AS total_records, SUM(is_bad) AS bad_records
    FROM flagged GROUP BY account_condition, history_condition
)
SELECT d.account_condition, d.history_condition, d.segment_label,
       COALESCE(s.total_records, 0) AS total_records, COALESCE(s.bad_records, 0) AS bad_records,
       ROUND(100.0 * s.bad_records / NULLIF(s.total_records, 0), 2) AS bad_share_pct,
       CASE WHEN COALESCE(s.total_records, 0) < 30 THEN 1 ELSE 0 END AS sparse_flag
FROM definitions AS d LEFT JOIN summary AS s
  ON s.account_condition = d.account_condition AND s.history_condition = d.history_condition
ORDER BY CASE d.segment_label WHEN 'Neither condition' THEN 1 WHEN 'Account condition only' THEN 2 WHEN 'History condition only' THEN 3 ELSE 4 END;
