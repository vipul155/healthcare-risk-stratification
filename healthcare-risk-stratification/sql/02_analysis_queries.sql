-- Run these queries in SQLite after importing the data.
-- They answer descriptive questions; they do not establish medical causes.

-- 1. How many records have each recorded outcome?
SELECT o.outcome_name, COUNT(*) AS patient_count
FROM patients AS p
JOIN outcomes AS o ON o.outcome_id = p.outcome_id
GROUP BY o.outcome_name
ORDER BY patient_count DESC;

-- 2. What are the average stay length and treatment cost by diagnosis?
-- Check dates and currency/units before interpreting these values.
SELECT
    d.diagnosis_name,
    COUNT(*) AS patient_count,
    ROUND(AVG(julianday(p.discharge_date) - julianday(p.admission_date)), 1) AS avg_stay_days,
    ROUND(AVG(p.treatment_cost), 2) AS avg_treatment_cost
FROM patients AS p
JOIN diagnoses AS d ON d.diagnosis_id = p.diagnosis_id
WHERE p.admission_date IS NOT NULL
  AND p.discharge_date IS NOT NULL
GROUP BY d.diagnosis_name
ORDER BY patient_count DESC;

-- 3. How do recorded outcomes vary by diagnosis?
SELECT
    d.diagnosis_name,
    o.outcome_name,
    COUNT(*) AS patient_count
FROM patients AS p
JOIN diagnoses AS d ON d.diagnosis_id = p.diagnosis_id
JOIN outcomes AS o ON o.outcome_id = p.outcome_id
GROUP BY d.diagnosis_name, o.outcome_name
ORDER BY d.diagnosis_name, patient_count DESC;

-- 4. How many lab records exist for each test name?
-- Confirm units and whether reference ranges match the test before using results.
SELECT
    test_name,
    COUNT(*) AS lab_record_count,
    COUNT(result) AS non_null_results,
    COUNT(normal_range) AS rows_with_reference_range
FROM labs
GROUP BY test_name
ORDER BY lab_record_count DESC;

-- 5. Check for impossible stay lengths before reporting averages.
SELECT COUNT(*) AS stays_with_discharge_before_admission
FROM patients
WHERE julianday(discharge_date) < julianday(admission_date);
