# Educational risk-classification model

## Question and target

This course exercise estimates whether a record belongs to the **high-risk label**: `1` for a recorded outcome of Complicated or Deceased, and `0` for Recovered. It is a retrospective classification exercise, not a clinical definition of patient risk.

## Method

- Records: 200
- Target counts: 137 high-risk labels and 63 recovered labels
- Features available at the modeled prediction point: age, gender, and diagnosis
- Model: logistic regression with scaling for age and one-hot encoding for categories
- Evaluation: stratified 5-fold cross-validation; each reported prediction is made for a fold not used to fit that fold's model
- Comparison: a majority-class baseline
- Decision threshold for class metrics: 0.50

Treatment cost, discharge date, and length of stay are excluded because they are known after admission or may reflect later care. Lab values are excluded until units and reference-range definitions are verified.

## Cross-validated results

| Metric | Logistic regression | Majority baseline |
|---|---:|---:|
| Accuracy | 0.670 | 0.685 |
| Balanced accuracy | 0.506 | 0.500 |
| High-risk recall | 0.949 | 1.000 |
| Recovered specificity | 0.063 | 0.000 |
| ROC AUC | 0.536 | 0.500 |
| Average precision | 0.689 | 0.685 |

## Interpretation and limits

The dataset is small (200 records), class proportions are uneven, and the source data and label definitions have not been clinically validated. Cross-validation provides an educational estimate on this sample; it does not demonstrate performance on new hospitals or future patients. The displayed model score is not a calibrated medical probability and must not be used to make care decisions.

The trained pipeline is saved locally at `data/processed/high_risk_model.joblib`. No names or patient IDs are used as model features.
