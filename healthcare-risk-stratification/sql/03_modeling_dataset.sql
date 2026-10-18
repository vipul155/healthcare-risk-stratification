-- Admission-time features and a clearly defined course-project target.
-- Positive class: any recorded outcome other than Recovered.
-- Deliberately excludes names, patient IDs, lab values with unresolved units,
-- treatment cost, discharge date, and length of stay.
SELECT
    p.age AS age,
    p.gender AS gender,
    d.diagnosis_name AS diagnosis,
    CASE
        WHEN LOWER(TRIM(o.outcome_name)) = 'recovered' THEN 0
        ELSE 1
    END AS high_risk
FROM patients AS p
JOIN diagnoses AS d ON d.diagnosis_id = p.diagnosis_id
JOIN outcomes AS o ON o.outcome_id = p.outcome_id;
