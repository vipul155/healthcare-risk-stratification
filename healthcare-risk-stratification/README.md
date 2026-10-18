# Healthcare Analytics Capstone

A beginner-friendly data analytics project based on the TuteDude course dataset. It covers data loading, SQL quality checks and summaries, Excel visualization, a baseline machine-learning model, and a local Streamlit demo.

## Project question

How do recorded outcomes, average hospital stay, and treatment cost vary in this course dataset? Can a simple model classify a recorded outcome using features available at the start of an admission?

This is an educational exercise, not a clinical tool. The model has weak performance on this small dataset and must not be used to guide patient care.

## Project files

- `sql/00_create_tables.sql` — SQLite table definitions.
- `sql/01_quality_checks.sql` — completeness, duplicate-key, and join checks.
- `sql/02_analysis_queries.sql` — outcome, stay-length, cost, and lab summaries.
- `sql/03_modeling_dataset.sql` — joined, name-free features and the project target.
- `src/build_database.py` — imports the four CSV files into a local SQLite database and omits patient names.
- `src/train_model.py` — evaluates a logistic-regression baseline with stratified cross-validation and saves the local model.
- `reports/healthcare_analysis.xlsx` — aggregate-only Excel workbook with charts, diagnosis summaries, data checks, and model review.
- `reports/capstone_report.md` — concise findings and project limitations.
- `app.py` — local Streamlit demonstration app.

## Setup and run on macOS

SQLite's command-line tool is already included on this Mac. Python and the course CSV files are also required.

1. From this project folder, create and activate a virtual environment, then install the listed packages:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. Keep `patients.csv`, `diagnoses.csv`, `labs.csv`, and `outcomes.csv` together. If they are in Downloads, load them with:

   ```sh
   python3 src/build_database.py --input-dir "$HOME/Downloads"
   ```

   Or put the four CSVs in `data/raw/` and run `python3 src/build_database.py`. The loader rebuilds `data/processed/healthcare.db`, excludes the source `Name` column, and prints counts only.

3. Run the SQL checks and descriptive queries:

   ```sh
   sqlite3 data/processed/healthcare.db < sql/01_quality_checks.sql
   sqlite3 data/processed/healthcare.db < sql/02_analysis_queries.sql
   ```

   The modeling query is used by the Python training script; avoid printing its individual rows in a shared terminal or report.

4. Train and evaluate the model:

   ```sh
   python3 src/train_model.py
   ```

   This writes a local model under `data/processed/` and aggregate evaluation results to `reports/model_evaluation.md` and `.json`.

5. Launch the demo on your Mac:

   ```sh
   streamlit run app.py
   ```

   Streamlit prints a local address to open in your browser. The app does not ask for names or patient IDs.

## Modeling choices

- Positive label: `1` for Complicated or Deceased; `0` for Recovered. This is a course-project definition, not a medical risk standard.
- Features: age, gender, and diagnosis.
- Excluded fields: name and patient ID are direct identifiers; treatment cost, discharge date, and stay length occur after admission; lab units and reference ranges need verification.
- Evaluation: stratified 5-fold out-of-fold evaluation compared with a majority-class baseline. Read `reports/model_evaluation.md` before interpreting the model.

## Data privacy and limits

The original patient CSV contains names and health-related fields. Keep all source CSVs and generated database/model files local; `data/raw/` and `data/processed/` are excluded by `.gitignore`. The Excel workbook contains grouped results only, without patient names, patient IDs, or individual-level rows. Check the course's data-use terms before sharing even aggregate findings.

The dataset has only 200 patient records. Each of the six lab test labels has multiple distinct reference-range strings, and the source does not establish the units or definitions. Lab values are therefore not used in the model. Treatment-cost currency/units are also not provided.
