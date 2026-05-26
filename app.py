from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "drug-model.pkl"
DATA_PATH = BASE_DIR / "drug200(DT).csv"

app = Flask(__name__)

model = joblib.load(MODEL_PATH)
dataset = pd.read_csv(DATA_PATH)

SEX_MAP = {"F": 0, "M": 1}
BP_MAP = {"HIGH": 0, "LOW": 1, "NORMAL": 2}
CHOL_MAP = {"HIGH": 0, "NORMAL": 1}

DRUG_CLASS_MAP = {
    0: "drugA",
    1: "drugB",
    2: "drugC",
    3: "drugX",
    4: "drugY",
}

feature_columns = ["Age", "Sex", "BP", "Cholesterol", "Na_to_K"]


def build_explanation(payload: dict, confidence: float) -> str:
    highlights: list[str] = []

    if payload["BP"] == "HIGH":
        highlights.append("high blood pressure")
    elif payload["BP"] == "LOW":
        highlights.append("low blood pressure")

    if payload["Cholesterol"] == "HIGH":
        highlights.append("elevated cholesterol")

    if payload["Na_to_K"] >= 20:
        highlights.append("a high sodium-to-potassium ratio")
    elif payload["Na_to_K"] <= 10:
        highlights.append("a low sodium-to-potassium ratio")

    if payload["Age"] >= 50:
        highlights.append("higher age profile")

    if not highlights:
        highlights.append("balanced vitals across major features")

    explanation = ", ".join(highlights)
    return (
        f"The model recommendation is primarily influenced by {explanation}. "
        f"Current confidence is {confidence:.1f}% based on learned decision-tree patterns."
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/feature-importance")
def feature_importance():
    importances = model.feature_importances_.tolist()
    return jsonify(
        {
            "features": feature_columns,
            "importances": [round(float(x), 6) for x in importances],
        }
    )


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True)

        age = int(data["age"])
        sex = str(data["sex"]).upper()
        bp = str(data["bp"]).upper()
        cholesterol = str(data["cholesterol"]).upper()
        na_to_k = float(data["na_to_k"])

        if sex not in SEX_MAP or bp not in BP_MAP or cholesterol not in CHOL_MAP:
            return jsonify({"error": "Invalid categorical input values."}), 400

        row = pd.DataFrame(
            [
                {
                    "Age": age,
                    "Sex": SEX_MAP[sex],
                    "BP": BP_MAP[bp],
                    "Cholesterol": CHOL_MAP[cholesterol],
                    "Na_to_K": na_to_k,
                }
            ]
        )

        pred_class = int(model.predict(row)[0])
        drug = DRUG_CLASS_MAP.get(pred_class, f"class_{pred_class}")

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(row)[0]
            confidence = float(np.max(proba) * 100)
            confidence_breakdown = {
                DRUG_CLASS_MAP.get(idx, f"class_{idx}"): round(float(prob) * 100, 2)
                for idx, prob in zip(model.classes_, proba)
            }
        else:
            confidence = 0.0
            confidence_breakdown = {}

        payload = {
            "Age": age,
            "Sex": sex,
            "BP": bp,
            "Cholesterol": cholesterol,
            "Na_to_K": na_to_k,
        }

        explanation = build_explanation(payload, confidence)

        return jsonify(
            {
                "recommended_drug": drug,
                "confidence": round(confidence, 2),
                "explanation": explanation,
                "confidence_breakdown": confidence_breakdown,
                "patient_summary": payload,
            }
        )

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True)
