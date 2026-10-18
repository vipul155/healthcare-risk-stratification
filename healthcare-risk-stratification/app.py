#!/usr/bin/env python3
"""Local Streamlit demo for the course outcome-classification model."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "data" / "processed" / "high_risk_model.joblib"

st.set_page_config(page_title="Healthcare Risk Demo", page_icon="📊", layout="centered")
st.title("Healthcare Risk Stratification — Learning Demo")
st.caption("TuteDude Data Analytics capstone project")
st.warning(
    "Educational demonstration only. This model is trained on a small course dataset and is not a clinical tool. "
    "Do not use its score to make patient-care decisions.",
    icon="⚠️",
)

if not MODEL_PATH.exists():
    st.error("The model has not been trained yet. From the project folder, run: python3 src/train_model.py")
    st.stop()

bundle = joblib.load(MODEL_PATH)
pipeline = bundle["pipeline"]
threshold = float(bundle["threshold"])

with st.form("risk_demo_form"):
    st.subheader("Enter the three modeled features")
    age = st.number_input(
        f"Age (training range: {bundle['age_min']}–{bundle['age_max']})",
        min_value=int(bundle["age_min"]),
        max_value=int(bundle["age_max"]),
        value=min(60, int(bundle["age_max"])),
        step=1,
    )
    gender = st.selectbox("Gender", bundle["gender_options"])
    diagnosis = st.selectbox("Diagnosis", bundle["diagnosis_options"])
    submitted = st.form_submit_button("Estimate course-dataset label")

if submitted:
    sample = pd.DataFrame([{"age": age, "gender": gender, "diagnosis": diagnosis}])
    probability = float(pipeline.predict_proba(sample)[0, 1])
    predicted_label = "High-risk label" if probability >= threshold else "Recovered label"
    st.metric("Model-estimated high-risk score", f"{probability:.1%}")
    st.write(f"At the course-project threshold of {threshold:.0%}, the predicted class is **{predicted_label}**.")
    st.caption(
        "High-risk label means Complicated or Deceased in the historical course data. "
        "The score is not a calibrated medical probability."
    )

with st.expander("How this demo works"):
    st.write(
        "The model uses age, gender, and diagnosis. It excludes names, IDs, lab results with unresolved "
        "reference ranges, treatment cost, and discharge information. Evaluation uses stratified 5-fold "
        "cross-validation and is summarized in reports/model_evaluation.md."
    )
