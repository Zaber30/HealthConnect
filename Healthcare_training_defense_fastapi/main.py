# ============================================================
#  🏥  Healthcare ML — FastAPI Pure API (Sequential Mapping)
#  Frontend is served by Laravel — this is a JSON API only.
#  No static/ or templates/ directories required.
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from typing import Optional
import joblib
import numpy as np
import os
import warnings

warnings.filterwarnings("ignore")

# ── Model directory ──────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

# ── Global model store ───────────────────────────────────────
MODELS: dict | None = None


# ── Load all artefacts once at startup ───────────────────────
def load_models() -> dict | None:
    try:
        m = {
            "disease_model":  joblib.load(f"{MODEL_DIR}/disease_model.pkl"),
            "le_disease":     joblib.load(f"{MODEL_DIR}/le_disease.pkl"),
            "le_gender":      joblib.load(f"{MODEL_DIR}/le_gender.pkl"),
            "le_blood":       joblib.load(f"{MODEL_DIR}/le_blood.pkl"),
            "le_division":    joblib.load(f"{MODEL_DIR}/le_division.pkl"),
            "symptom_cols":   joblib.load(f"{MODEL_DIR}/symptom_columns.pkl"),
            "feature_cols":   joblib.load(f"{MODEL_DIR}/feature_columns.pkl"),
            "specialist_map": joblib.load(f"{MODEL_DIR}/disease_specialist_map.pkl"),
        }

        scaler_path = f"{MODEL_DIR}/scaler.pkl"
        m["scaler"] = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

        name_path = f"{MODEL_DIR}/best_model_name.pkl"
        m["best_model_name"] = (
            joblib.load(name_path) if os.path.exists(name_path) else "Random Forest"
        )

        print(f"✅ Models loaded — using: {m['best_model_name']}")
        return m

    except FileNotFoundError as e:
        print(f"❌ Model file not found: {e}")
        return None


# ── Lifespan: load models once before accepting requests ─────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODELS
    MODELS = load_models()
    yield


# ── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="Healthcare ML API",
    description="AI-powered symptom → disease → specialist prediction. "
                "Frontend served by Laravel; this is a pure JSON API.",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS — allow Laravel (any origin in dev) ─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Pydantic schemas ─────────────────────────────────────────
class PredictRequest(BaseModel):
    symptoms:    list[str]     = Field(..., min_length=1, description="List of symptom strings")
    age:         int           = Field(..., ge=1, le=150,  description="Patient age")
    gender:      str           = Field(...,                description="'Male' or 'Female'")
    blood_group: Optional[str] = Field("O+",              description="ABO blood group e.g. 'O+'")
    division:    Optional[str] = Field("Dhaka",           description="Administrative division")
    top_n:       Optional[int] = Field(3, ge=1, le=10,    description="Top N predictions to return")


class PredictionItem(BaseModel):
    rank:               int
    disease:            str
    disease_confidence: float
    specialist:         str
    urgency:            str


class PatientInfo(BaseModel):
    age:         int
    gender:      str
    blood_group: str


class PredictResponse(BaseModel):
    success:     bool
    patient:     PatientInfo
    matched:     list[str]
    model_used:  str
    predictions: list[PredictionItem]


# ── Core ML prediction logic ──────────────────────────────────
def run_prediction(
    symptoms_list: list[str],
    age:           int,
    gender:        str,
    blood_group:   str = "O+",
    division:      str = "Dhaka",
    top_n:         int = 3,
) -> dict:
    if MODELS is None:
        raise RuntimeError("Models not loaded")

    m            = MODELS
    symptom_cols = m["symptom_cols"]

    vec     = {s: 0 for s in symptom_cols}
    matched = []
    for s in symptoms_list:
        key = s.lower().strip().replace(" ", "_")
        if key in vec:
            vec[key] = 1
            matched.append(key)

    if not matched:
        raise ValueError("None of the provided symptoms were recognised.")

    def safe_encode(encoder, value: str, fallback: int = 0) -> int:
        try:
            return int(encoder.transform([value])[0])
        except Exception:
            return fallback

    g_enc = safe_encode(m["le_gender"],   gender)
    b_enc = safe_encode(m["le_blood"],    blood_group)
    d_enc = safe_encode(m["le_division"], division)

    feature_vec = [vec[s] for s in symptom_cols] + [age, g_enc, b_enc, d_enc]
    X = np.array(feature_vec, dtype=float).reshape(1, -1)
    X = np.nan_to_num(X)

    if m["scaler"] is not None:
        X = m["scaler"].transform(X)

    d_probs = m["disease_model"].predict_proba(X)[0]
    d_top   = np.argsort(d_probs)[::-1][:top_n]

    predictions = []
    for rank, d_idx in enumerate(d_top, 1):
        d_name     = m["le_disease"].classes_[d_idx]
        d_conf     = float(d_probs[d_idx])
        specialist = m["specialist_map"].get(d_name, "General Physician")

        predictions.append({
            "rank":               rank,
            "disease":            d_name,
            "disease_confidence": round(d_conf * 100, 1),
            "specialist":         specialist,
            "urgency": (
                "HIGH"   if d_conf > 0.70 else
                "MEDIUM" if d_conf > 0.40 else
                "LOW"
            ),
        })

    return {
        "patient":     {"age": age, "gender": gender, "blood_group": blood_group},
        "matched":     matched,
        "model_used":  m["best_model_name"],
        "predictions": predictions,
    }


# ── Shared handlers ───────────────────────────────────────────
def _symptoms_response() -> JSONResponse:
    if MODELS is None:
        raise HTTPException(status_code=503, detail="Models not loaded — check server logs")
    return JSONResponse({
        "symptoms": sorted(MODELS["symptom_cols"]),
        "count":    len(MODELS["symptom_cols"]),
    })


def _predict_response(payload: PredictRequest) -> dict:
    if MODELS is None:
        raise HTTPException(status_code=503, detail="Models not loaded — check server logs")
    try:
        result = run_prediction(
            symptoms_list=payload.symptoms,
            age=payload.age,
            gender=payload.gender,
            blood_group=payload.blood_group or "O+",
            division=payload.division    or "Dhaka",
            top_n=payload.top_n          or 3,
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health check ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health():
    """Quick health check — confirms the API is running and models are loaded."""
    return {
        "status":       "ok",
        "models_ready": MODELS is not None,
        "model_used":   MODELS["best_model_name"] if MODELS else None,
        "docs":         "http://localhost:5000/docs",
    }


# ── GET /symptoms  (called by frontend JS) ───────────────────
@app.get("/symptoms", tags=["Data"], summary="List all symptoms")
async def get_symptoms():
    """Returns the sorted list of symptoms the model was trained on."""
    return _symptoms_response()


# ── GET /api/symptoms  (canonical) ───────────────────────────
@app.get("/api/symptoms", tags=["Data"], summary="List all symptoms (canonical)")
async def get_symptoms_api():
    return _symptoms_response()


# ── POST /predict  (called by frontend JS) ───────────────────
@app.post("/predict", response_model=PredictResponse, tags=["Prediction"],
          summary="Predict disease & specialist")
async def predict(payload: PredictRequest):
    """
    Main prediction endpoint called by the frontend.
    Accepts { symptoms, age, gender } — returns top-N diseases
    with specialist, confidence %, and urgency level.
    """
    return _predict_response(payload)


# ── POST /api/predict  (canonical) ───────────────────────────
@app.post("/api/predict", response_model=PredictResponse, tags=["Prediction"],
          summary="Predict disease & specialist (canonical)")
async def predict_api(payload: PredictRequest):
    return _predict_response(payload)


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 55)
    print("  🏥  Healthcare ML API  (FastAPI)")
    print("=" * 55)
    print("  Health  →  http://localhost:5000/")
    print("  Predict →  POST http://localhost:5000/predict")
    print("  Swagger →  http://localhost:5000/docs")
    print("  ReDoc   →  http://localhost:5000/redoc")
    print("=" * 55 + "\n")

    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)