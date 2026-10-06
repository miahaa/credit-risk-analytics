-- Requires SQLite >= 3.37 for STRICT tables. No source values are recoded.
CREATE TABLE credit_records (
    record_id INTEGER PRIMARY KEY CHECK (record_id >= 1),
    checking_status INTEGER NOT NULL CHECK (checking_status IN (1, 2, 3, 4)),
    duration_months INTEGER NOT NULL CHECK (duration_months > 0),
    credit_history INTEGER NOT NULL CHECK (credit_history IN (0, 1, 2, 3, 4)),
    purpose INTEGER NOT NULL CHECK (purpose IN (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)),
    credit_amount INTEGER NOT NULL CHECK (credit_amount > 0),
    savings INTEGER NOT NULL CHECK (savings IN (1, 2, 3, 4, 5)),
    employment_duration INTEGER NOT NULL CHECK (employment_duration IN (1, 2, 3, 4, 5)),
    installment_rate INTEGER NOT NULL CHECK (installment_rate IN (1, 2, 3, 4)),
    personal_status_sex INTEGER NOT NULL CHECK (personal_status_sex IN (1, 2, 3, 4)),
    other_debtors INTEGER NOT NULL CHECK (other_debtors IN (1, 2, 3)),
    residence_duration INTEGER NOT NULL CHECK (residence_duration IN (1, 2, 3, 4)),
    property INTEGER NOT NULL CHECK (property IN (1, 2, 3, 4)),
    age INTEGER NOT NULL CHECK (age > 0),
    other_installment_plans INTEGER NOT NULL CHECK (other_installment_plans IN (1, 2, 3)),
    housing INTEGER NOT NULL CHECK (housing IN (1, 2, 3)),
    number_credits INTEGER NOT NULL CHECK (number_credits IN (1, 2, 3, 4)),
    job INTEGER NOT NULL CHECK (job IN (1, 2, 3, 4)),
    people_liable INTEGER NOT NULL CHECK (people_liable IN (1, 2)),
    telephone INTEGER NOT NULL CHECK (telephone IN (1, 2)),
    foreign_worker INTEGER NOT NULL CHECK (foreign_worker IN (1, 2)),
    credit_risk INTEGER NOT NULL CHECK (credit_risk IN (0, 1)),
    credit_risk_label TEXT NOT NULL CHECK (credit_risk_label IN ('Bad', 'Good')),
    CHECK (credit_risk_label = CASE credit_risk WHEN 0 THEN 'Bad' WHEN 1 THEN 'Good' END)
) STRICT;

CREATE TABLE category_lookup (
    variable_name TEXT NOT NULL,
    category_code INTEGER NOT NULL,
    category_label TEXT NOT NULL,
    display_order INTEGER NOT NULL CHECK (display_order > 0),
    PRIMARY KEY (variable_name, category_code)
) STRICT;

CREATE VIEW credit_reporting AS
SELECT r.*,
    CASE WHEN r.credit_risk = 0 THEN 1 ELSE 0 END AS is_bad,
    CASE WHEN r.duration_months <= 12 THEN 1 WHEN r.duration_months <= 24 THEN 2 WHEN r.duration_months <= 36 THEN 3 ELSE 4 END AS duration_band_order,
    CASE WHEN r.duration_months <= 12 THEN '<=12 months' WHEN r.duration_months <= 24 THEN '>12-24 months' WHEN r.duration_months <= 36 THEN '>24-36 months' ELSE '>36 months' END AS duration_band,
    c0.category_label AS checking_status_label,
    c1.category_label AS credit_history_label,
    c2.category_label AS purpose_label,
    c3.category_label AS savings_label,
    c4.category_label AS employment_duration_label,
    c5.category_label AS installment_rate_label,
    c6.category_label AS personal_status_sex_label,
    c7.category_label AS other_debtors_label,
    c8.category_label AS residence_duration_label,
    c9.category_label AS property_label,
    c10.category_label AS other_installment_plans_label,
    c11.category_label AS housing_label,
    c12.category_label AS number_credits_label,
    c13.category_label AS job_label,
    c14.category_label AS people_liable_label,
    c15.category_label AS telephone_label,
    c16.category_label AS foreign_worker_label
FROM credit_records AS r
LEFT JOIN category_lookup AS c0 ON c0.variable_name = 'checking_status' AND c0.category_code = r.checking_status
LEFT JOIN category_lookup AS c1 ON c1.variable_name = 'credit_history' AND c1.category_code = r.credit_history
LEFT JOIN category_lookup AS c2 ON c2.variable_name = 'purpose' AND c2.category_code = r.purpose
LEFT JOIN category_lookup AS c3 ON c3.variable_name = 'savings' AND c3.category_code = r.savings
LEFT JOIN category_lookup AS c4 ON c4.variable_name = 'employment_duration' AND c4.category_code = r.employment_duration
LEFT JOIN category_lookup AS c5 ON c5.variable_name = 'installment_rate' AND c5.category_code = r.installment_rate
LEFT JOIN category_lookup AS c6 ON c6.variable_name = 'personal_status_sex' AND c6.category_code = r.personal_status_sex
LEFT JOIN category_lookup AS c7 ON c7.variable_name = 'other_debtors' AND c7.category_code = r.other_debtors
LEFT JOIN category_lookup AS c8 ON c8.variable_name = 'residence_duration' AND c8.category_code = r.residence_duration
LEFT JOIN category_lookup AS c9 ON c9.variable_name = 'property' AND c9.category_code = r.property
LEFT JOIN category_lookup AS c10 ON c10.variable_name = 'other_installment_plans' AND c10.category_code = r.other_installment_plans
LEFT JOIN category_lookup AS c11 ON c11.variable_name = 'housing' AND c11.category_code = r.housing
LEFT JOIN category_lookup AS c12 ON c12.variable_name = 'number_credits' AND c12.category_code = r.number_credits
LEFT JOIN category_lookup AS c13 ON c13.variable_name = 'job' AND c13.category_code = r.job
LEFT JOIN category_lookup AS c14 ON c14.variable_name = 'people_liable' AND c14.category_code = r.people_liable
LEFT JOIN category_lookup AS c15 ON c15.variable_name = 'telephone' AND c15.category_code = r.telephone
LEFT JOIN category_lookup AS c16 ON c16.variable_name = 'foreign_worker' AND c16.category_code = r.foreign_worker;
