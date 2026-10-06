-- Average the middle one/two positions, handling odd and even group sizes.
WITH ordered AS (
    SELECT credit_risk, credit_risk_label, duration_months,
           ROW_NUMBER() OVER (PARTITION BY credit_risk ORDER BY duration_months, record_id) AS position,
           COUNT(*) OVER (PARTITION BY credit_risk) AS total_records
    FROM credit_reporting
)
SELECT credit_risk, credit_risk_label, MAX(total_records) AS total_records,
       AVG(1.0 * duration_months) AS median_duration_months
FROM ordered
WHERE position IN ((total_records + 1) / 2, (total_records + 2) / 2)
GROUP BY credit_risk, credit_risk_label
ORDER BY credit_risk;
