-- Starter schema for the four course tables.
-- Import only the listed fields; exclude the source patients.csv Name column.
-- These are staging tables: validate keys and data before adding constraints.

CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER,
    age INTEGER,
    gender TEXT,
    diagnosis_id INTEGER,
    admission_date TEXT,
    discharge_date TEXT,
    outcome_id INTEGER,
    treatment_cost DECIMAL(12, 2)
);

CREATE TABLE IF NOT EXISTS diagnoses (
    diagnosis_id INTEGER,
    diagnosis_name TEXT
);

CREATE TABLE IF NOT EXISTS labs (
    lab_id INTEGER,
    patient_id INTEGER,
    test_name TEXT,
    result DECIMAL(12, 3),
    normal_range TEXT
);

CREATE TABLE IF NOT EXISTS outcomes (
    outcome_id INTEGER,
    outcome_name TEXT
);
