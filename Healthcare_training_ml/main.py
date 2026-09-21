"""
HealthCare BD — FastAPI Backend
================================
Specialist Recommendation API

Folder structure expected:
  project/
  ├── main.py                  ← this file
  ├── saved_models/
  │   ├── disease_model.pkl
  │   ├── specialist_model.pkl
  │   ├── label_encoder_disease.pkl
  │   ├── label_encoder_specialist.pkl
  │   ├── label_encoder_gender.pkl
  │   ├── label_encoder_blood.pkl
  │   ├── label_encoder_division.pkl
  │   ├── symptom_columns.pkl
  │   ├── feature_columns.pkl
  │   └── disease_specialist_map.pkl
  └── requirements.txt

Install:
  pip install fastapi uvicorn scikit-learn joblib numpy xgboost

Run:
  uvicorn main:app --reload --host 0.0.0.0 --port 8000

Test:
  http://localhost:8000/docs   ← Swagger UI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import numpy as np
import joblib
import os

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────

app = FastAPI(
    title="HealthCare BD — ML API",
    description="Symptom-based specialist recommendation for Bangladesh",
    version="1.0.0",
)

# CORS — Allow your Laravel/Vue frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",   # Laravel dev server
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5173",
        # Add your production domain here e.g. "https://healthcarebd.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Load Models Once at Startup
# ─────────────────────────────────────────────

MODELS_DIR = "saved_models"

def load_model(filename: str):
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise RuntimeError(f"Model file not found: {path}")
    return joblib.load(path)

try:
    disease_model         = load_model("disease_model.pkl")
    specialist_model      = load_model("specialist_model.pkl")
    le_disease            = load_model("label_encoder_disease.pkl")
    le_specialist         = load_model("label_encoder_specialist.pkl")
    le_gender             = load_model("label_encoder_gender.pkl")
    le_blood              = load_model("label_encoder_blood.pkl")
    le_division           = load_model("label_encoder_division.pkl")
    SYMPTOM_COLS          = load_model("symptom_columns.pkl")
    FEATURE_COLS          = load_model("feature_columns.pkl")
    disease_specialist_map = load_model("disease_specialist_map.pkl")
    print("✅ All models loaded successfully")
    print(f"   Symptoms  : {len(SYMPTOM_COLS)}")
    print(f"   Diseases  : {len(le_disease.classes_)}")
    print(f"   Specialists: {len(le_specialist.classes_)}")
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    raise

# ─────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────

class PredictRequest(BaseModel):
    symptoms: List[str] = Field(
        ...,
        min_items=1,
        max_items=85,
        example=["fever", "cough", "headache", "fatigue"],
        description="List of symptom names (snake_case or space-separated)"
    )
    age: int = Field(..., ge=1, le=120, example=28)
    gender: str = Field(..., example="Male", description="'Male' or 'Female'")
    blood_group: Optional[str] = Field("O+", example="O+")
    division: Optional[str] = Field("Dhaka", example="Dhaka")
    top_n: Optional[int] = Field(3, ge=1, le=10, description="Number of predictions to return")

    @validator("gender")
    def validate_gender(cls, v):
        if v not in ("Male", "Female"):
            raise ValueError("gender must be 'Male' or 'Female'")
        return v


class SpecialistResult(BaseModel):
    rank: int
    disease: str
    confidence: float
    confidence_pct: str
    specialist: str
    urgency: str   # HIGH / MEDIUM / LOW


class PredictResponse(BaseModel):
    success: bool
    patient: dict
    matched_symptoms: List[str]
    unmatched_symptoms: List[str]
    top_specialist: str          # ← The #1 recommended specialist
    recommendations: List[SpecialistResult]

# ─────────────────────────────────────────────
# Core Prediction Logic
# ─────────────────────────────────────────────

def build_feature_vector(
    symptoms: List[str],
    age: int,
    gender: str,
    blood_group: str,
    division: str,
):
    """
    Convert patient data into the same feature vector used during training.
    Returns (feature_array, matched_symptoms, unmatched_symptoms)
    """
    # Build symptom binary vector
    vec = {s: 0 for s in SYMPTOM_COLS}
    matched, unmatched = [], []

    for s in symptoms:
        s_clean = s.lower().strip().replace(" ", "_")
        if s_clean in vec:
            vec[s_clean] = 1
            matched.append(s_clean)
        else:
            unmatched.append(s_clean)

    # Encode categorical patient attributes
    try:
        g_enc = int(le_gender.transform([gender])[0])
    except Exception:
        g_enc = 0   # default if unseen

    try:
        b_enc = int(le_blood.transform([blood_group])[0])
    except Exception:
        b_enc = 0

    try:
        d_enc = int(le_division.transform([division])[0])
    except Exception:
        d_enc = 0

    # Assemble feature vector: [symptom_cols..., age, gender_enc, blood_enc, division_enc]
    feature_vec = [vec[s] for s in SYMPTOM_COLS] + [age, g_enc, b_enc, d_enc]
    X = np.array(feature_vec, dtype=float).reshape(1, -1)
    X = np.nan_to_num(X)

    return X, matched, unmatched


def run_prediction(request: PredictRequest) -> PredictResponse:
    X, matched, unmatched = build_feature_vector(
        request.symptoms,
        request.age,
        request.gender,
        request.blood_group,
        request.division,
    )

    # Disease prediction probabilities
    probs   = disease_model.predict_proba(X)[0]
    top_idx = np.argsort(probs)[::-1][:request.top_n]

    recommendations = []
    for rank, idx in enumerate(top_idx, 1):
        disease    = le_disease.classes_[idx]
        confidence = float(probs[idx])
        specialist = disease_specialist_map.get(disease, "General Physician")

        if confidence > 0.7:
            urgency = "HIGH"
        elif confidence > 0.4:
            urgency = "MEDIUM"
        else:
            urgency = "LOW"

        recommendations.append(SpecialistResult(
            rank=rank,
            disease=disease,
            confidence=round(confidence, 4),
            confidence_pct=f"{confidence * 100:.1f}%",
            specialist=specialist,
            urgency=urgency,
        ))

    top_specialist = recommendations[0].specialist if recommendations else "General Physician"

    return PredictResponse(
        success=True,
        patient={
            "age":        request.age,
            "gender":     request.gender,
            "blood_group": request.blood_group,
            "division":   request.division,
        },
        matched_symptoms=matched,
        unmatched_symptoms=unmatched,
        top_specialist=top_specialist,
        recommendations=recommendations,
    )

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "running",
        "app":    "HealthCare BD ML API",
        "docs":   "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status":      "ok",
        "diseases":    len(le_disease.classes_),
        "specialists": len(le_specialist.classes_),
        "symptoms":    len(SYMPTOM_COLS),
    }


@app.get("/symptoms", tags=["Meta"])
def get_all_symptoms():
    """Return the full list of supported symptom names."""
    return {
        "count":    len(SYMPTOM_COLS),
        "symptoms": SYMPTOM_COLS,
    }


@app.get("/specialists", tags=["Meta"])
def get_all_specialists():
    """Return all specialist types the model can recommend."""
    specialists = sorted(set(disease_specialist_map.values()))
    return {
        "count":      len(specialists),
        "specialists": specialists,
    }


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
def predict(request: PredictRequest):
    """
    Main prediction endpoint.

    Send patient symptoms + basic info → get specialist recommendation.

    Example curl:
        curl -X POST http://localhost:8000/predict \\
          -H "Content-Type: application/json" \\
          -d '{
            "symptoms": ["fever","cough","headache","fatigue"],
            "age": 28,
            "gender": "Male",
            "blood_group": "O+",
            "division": "Dhaka"
          }'
    """
    if not request.symptoms:
        raise HTTPException(status_code=422, detail="At least one symptom is required.")

    try:
        result = run_prediction(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    return result