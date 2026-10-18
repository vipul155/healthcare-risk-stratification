-- Run after importing the course CSVs into the staging tables.

-- Table sizes
SELECT 'patients' AS table_name, COUNT(*) AS row_count FROM patients
UNION ALL
SELECT 'diagnoses', COUNT(*) FROM diagnoses
UNION ALL
SELECT 'labs', COUNT(*) FROM labs
UNION ALL
SELECT 'outcomes', COUNT(*) FROM outcomes;

-- Duplicate patient IDs
SELECT patient_id, COUNT(*) AS row_count
FROM patients
GROUP BY patient_id
HAVING COUNT(*) > 1;

-- Duplicate lab IDs
SELECT lab_id, COUNT(*) AS row_count
FROM labs
GROUP BY lab_id
HAVING COUNT(*) > 1;

-- Missing or unmatched diagnosis references
SELECT p.patient_id, p.diagnosis_id
FROM patients AS p
LEFT JOIN diagnoses AS d ON d.diagnosis_id = p.diagnosis_id
WHERE p.diagnosis_id IS NULL OR d.diagnosis_id IS NULL;

-- Missing or unmatched outcome references
SELECT p.patient_id, p.outcome_id
FROM patients AS p
LEFT JOIN outcomes AS o ON o.outcome_id = p.outcome_id
WHERE p.outcome_id IS NULL OR o.outcome_id IS NULL;

-- Lab rows that do not match a patient
SELECT l.lab_id, l.patient_id
FROM labs AS l
LEFT JOIN patients AS p ON p.patient_id = l.patient_id
WHERE l.patient_id IS NULL OR p.patient_id IS NULL;

-- Check whether discharge precedes admission after converting dates.
-- Exact date-conversion syntax depends on your SQL database.
