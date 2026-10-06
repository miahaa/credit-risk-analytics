-- Import audit: all issue columns must be zero. Counts are checked against CSV by the loader.
SELECT COUNT(*) AS total_records,
       SUM(is_bad) AS bad_records,
       SUM(1 - is_bad) AS good_records,
       SUM(CASE WHEN checking_status IS NULL OR duration_months IS NULL OR credit_history IS NULL OR purpose IS NULL OR credit_amount IS NULL OR savings IS NULL OR employment_duration IS NULL OR installment_rate IS NULL OR personal_status_sex IS NULL OR other_debtors IS NULL OR residence_duration IS NULL OR property IS NULL OR age IS NULL OR other_installment_plans IS NULL OR housing IS NULL OR number_credits IS NULL OR job IS NULL OR people_liable IS NULL OR telephone IS NULL OR foreign_worker IS NULL OR credit_risk IS NULL OR credit_risk_label IS NULL THEN 1 ELSE 0 END) AS missing_value_rows,
       SUM(CASE WHEN credit_risk NOT IN (0, 1) THEN 1 ELSE 0 END) AS invalid_target_rows,
       SUM(CASE WHEN credit_risk_label <> CASE credit_risk WHEN 0 THEN 'Bad' ELSE 'Good' END THEN 1 ELSE 0 END) AS target_label_mismatches,
       SUM(CASE WHEN checking_status_label IS NULL OR credit_history_label IS NULL OR purpose_label IS NULL OR savings_label IS NULL OR employment_duration_label IS NULL OR installment_rate_label IS NULL OR personal_status_sex_label IS NULL OR other_debtors_label IS NULL OR residence_duration_label IS NULL OR property_label IS NULL OR other_installment_plans_label IS NULL OR housing_label IS NULL OR number_credits_label IS NULL OR job_label IS NULL OR people_liable_label IS NULL OR telephone_label IS NULL OR foreign_worker_label IS NULL THEN 1 ELSE 0 END) AS missing_lookup_rows,
       COUNT(*) - COUNT(DISTINCT record_id) AS duplicate_record_ids,
       CASE WHEN MIN(record_id) = 1 AND MAX(record_id) = COUNT(*) THEN 0 ELSE 1 END AS row_position_issues
FROM credit_reporting;
