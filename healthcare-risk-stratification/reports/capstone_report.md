# Healthcare Analytics Capstone — Findings

## Executive summary

The course dataset contains 200 patient records, 10 diagnosis categories, 200 lab records, and 3 recorded outcomes. The outcomes are fairly evenly split: 69 Deceased (34.5%), 68 Complicated (34.0%), and 63 Recovered (31.5%). These are counts in the provided sample and do not explain causes.

Average recorded stay ranges from 18.0 days for Kidney Disease (10 records) to 41.6 days for Arthritis (17 records) and 41.1 days for Stroke (23 records). Treatment-cost averages range across diagnoses, but the source does not define currency or units, so those values should not be compared as financial amounts without clarification.

The logistic-regression model barely separates the course labels: cross-validated ROC AUC is 0.536 versus 0.500 for a constant majority baseline, and balanced accuracy is 50.6% versus 50.0%. At the 0.50 threshold, the model recognizes only 6.3% of recovered labels. It is not useful for real patient decisions.

## Data quality

- No duplicate patient or lab IDs were found.
- No missing patient ages or admission/discharge dates were found.
- All patient diagnosis/outcome references and lab-to-patient references matched.
- No discharge dates preceded admission dates.
- Every lab test label has six distinct reference-range strings. Units and definitions need confirmation before any lab interpretation.

## Workflow

1. Load the four course CSVs into a local SQLite database, dropping patient names.
2. Use SQL to validate IDs and joins, then summarize outcomes, stay length, cost, and lab coverage.
3. Review the aggregate Excel workbook and charts.
4. Extract age, gender, diagnosis, and a clearly defined target from joined SQL tables.
5. Evaluate logistic regression with stratified 5-fold cross-validation against a majority-class baseline.
6. Run the local Streamlit demo with the saved model.

## Model definition and limitations

The positive label is a recorded outcome of Complicated or Deceased; Recovered is the negative label. The model uses age, gender, and diagnosis. It excludes treatment cost, discharge date, and stay length because they are not available at admission; it excludes lab values because the source's units and ranges are unresolved.

Only 200 records are available, with 137 positive and 63 negative labels. The label definition is a teaching assumption, not a clinical standard. Cross-validation on this dataset does not show how the model will perform on future or external data, and its output is not calibrated as a medical probability. Do not use it to make or recommend care decisions.
