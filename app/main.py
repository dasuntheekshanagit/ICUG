from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import random
from pathlib import Path
import os
from typing import Optional
import io
import csv
from datetime import datetime

import numpy as np
import pandas as pd

app = FastAPI(title="PPGI FastAPI")

# Serve the static frontend from the "static" directory
app.mount("/static", StaticFiles(directory="static"), name="static")

class PredictInput(BaseModel):
    gender: str = "Male"
    age: float = 30.0
    weight: float = 70.0
    waist_circumference: float = 80.0
    birth_place: str = ""
    blood_group: str = "Unknown"
    family_history: str = "No"
    physical_activity: str = "Sedentary"
    food_item: str = ""
    carb: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    dietary_fiber: float = 0.0

_lgb_model: Optional[object] = None
_feature_columns: Optional[list] = None
_last_result: Optional[dict] = None

def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Total nutrients and proportions
    df['Total_Nutrients'] = (
        df['Carb(g/100g)'] + df['Protien(g/100g)'] + df['Fat(g/100g)'] + df['Dietary Fiber(g/100g)']
    )
    df['Total_Nutrients'] = df['Total_Nutrients'].replace(0, 1e-6)
    df['Carb_Proportion'] = df['Carb(g/100g)'] / df['Total_Nutrients']
    df['Protien_Proportion'] = df['Protien(g/100g)'] / df['Total_Nutrients']
    df['Fat_Proportion'] = df['Fat(g/100g)'] / df['Total_Nutrients']
    df['Dietary_Fiber_Proportion'] = df['Dietary Fiber(g/100g)'] / df['Total_Nutrients']

    # Interactions
    df['Carb_x_Protien'] = df['Carb(g/100g)'] * df['Protien(g/100g)']
    df['Carb_x_Fat'] = df['Carb(g/100g)'] * df['Fat(g/100g)']
    df['Carb_x_Dietary_Fiber'] = df['Carb(g/100g)'] * df['Dietary Fiber(g/100g)']
    df['Protien_x_Fat'] = df['Protien(g/100g)'] * df['Fat(g/100g)']
    df['Protien_x_Dietary_Fiber'] = df['Protien(g/100g)'] * df['Dietary Fiber(g/100g)']
    df['Fat_x_Dietary_Fiber'] = df['Fat(g/100g)'] * df['Dietary Fiber(g/100g)']

    # Polynomials
    df['Carb_sq'] = df['Carb(g/100g)'] ** 2
    df['Protien_sq'] = df['Protien(g/100g)'] ** 2
    df['Fat_sq'] = df['Fat(g/100g)'] ** 2
    df['Dietary_Fiber_sq'] = df['Dietary Fiber(g/100g)'] ** 2

    # Interactions with WC/HC
    nutrient_cols = ['Carb(g/100g)', 'Protien(g/100g)', 'Fat(g/100g)', 'Dietary Fiber(g/100g)']
    for nutrient in nutrient_cols:
        df[f'WC/HC_x_{nutrient}'] = df['WC/HC'] * df[nutrient]

    return df

def _load_lgb_model():
    """Lazy-load LightGBM and the model file.

    Raises a RuntimeError with a helpful message if LightGBM or libgomp is missing.
    """
    global _lgb_model, _feature_columns
    if _lgb_model is not None:
        return _lgb_model

    try:
        import importlib
        lgb = importlib.import_module('lightgbm')
    except Exception as ie:
        raise RuntimeError(
            "LightGBM is unavailable in this environment. If deploying on a minimal Linux image, install libgomp (e.g., apt-get install -y libgomp1 or apk add libgomp) or use the provided Dockerfile."
        ) from ie

    # Model path preference: project root then NoteBooks
    root = Path(__file__).parent.parent
    candidates = [root / 'lightgbm_model.txt', root / 'NoteBooks' / 'lightgbm_model.txt']
    model_path = None
    for c in candidates:
        if c.exists():
            model_path = c
            break
    if model_path is None:
        raise FileNotFoundError('lightgbm_model.txt not found in project root or NoteBooks/')

    try:
        model = lgb.Booster(model_file=str(model_path))
    except Exception as e:
        # Common case: libgomp missing in the OS
        raise RuntimeError(
            "Failed to load LightGBM model. Ensure system dependency libgomp.so.1 is installed (Debian/Ubuntu: libgomp1, Alpine: libgomp)."
        ) from e

    _lgb_model = model

    # If the model has feature_name stored, use it; otherwise will infer later
    try:
        _feature_columns = model.feature_name()
    except Exception:
        _feature_columns = None
    return _lgb_model

def _build_feature_frame(payload: PredictInput) -> pd.DataFrame:
    # Map API fields to the training feature schema
    # We don't have Height; BMI and WC/HC aren’t directly provided in the form.
    # Approximate WC/HC using waist circumference and a default hip circ of 95 cm (assumption).
    hip_circ = 95.0
    wc = float(payload.waist_circumference or 0.0)
    wth_ratio = (wc / hip_circ) if hip_circ else 0.0

    df = pd.DataFrame([{
        'Age': float(payload.age or 0.0),
        'BMI(kg/m2)': np.nan,  # Not available in the form currently
        'WC/HC': wth_ratio,
        'Carb(g/100g)': float(payload.carb or 0.0),
        'Protien(g/100g)': float(payload.protein or 0.0),
        'Fat(g/100g)': float(payload.fat or 0.0),
        'Dietary Fiber(g/100g)': float(payload.dietary_fiber or 0.0),
        'Health Problem': 'None',
        'Blood Group': payload.blood_group or 'Unknown'
    }])

    # Feature engineering similar to notebook
    df_eng = _engineer_features(df)

    # Drop columns that were dropped at train time if present
    for drop_col in ['WC/HC', 'BMI(kg/m2)']:
        if drop_col in df_eng.columns:
            df_eng = df_eng.drop(columns=[drop_col])

    # Align to model features if known; otherwise pass engineered features as-is
    if _feature_columns:
        for col in _feature_columns:
            if col not in df_eng.columns:
                df_eng[col] = 0.0
        df_eng = df_eng[_feature_columns]

    return df_eng

@app.post("/api/predict")
async def predict(payload: PredictInput):
    """Predict PPGI as 100 * IAUC(food) / IAUC(glucose-ref).

    Glucose reference is defined as a 100g portion with 16.7g carbohydrate and 0 protein/fat/fiber.
    """
    global _last_result

    def _frame_with_override_nutrients(base: PredictInput, carb: float, prot: float, fat: float, fiber: float) -> pd.DataFrame:
        # Build a temporary PredictInput-like dict overriding only nutrients
        temp = PredictInput(**{**base.dict(), 'carb': carb, 'protein': prot, 'fat': fat, 'dietary_fiber': fiber})
        return _build_feature_frame(temp)

    try:
        model = _load_lgb_model()
        # IAUC for the user-entered food
        X_food = _build_feature_frame(payload)
        iauc_food = float(model.predict(X_food)[0])

        # IAUC for 100g glucose reference (16.7g carb, others 0)
        X_glu = _frame_with_override_nutrients(payload, carb=16.7, prot=0.0, fat=0.0, fiber=0.0)
        iauc_glu = float(model.predict(X_glu)[0])

        # Guard against zero/negative reference
        if iauc_glu <= 0:
            raise ValueError(f"Invalid glucose reference IAUC: {iauc_glu}")

        ppgi_val = 100.0 * iauc_food / iauc_glu
        source = 'lightgbm'
        result = {
            "ppgi": round(ppgi_val, 2),
            "iauc_food": round(iauc_food, 4),
            "iauc_glucose_ref": round(iauc_glu, 4),
            "input_summary": payload.dict(),
            "source": source,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        # Cache last result in-memory
        _last_result = result
        return JSONResponse(result)
    except Exception as e:
        # Fallback to a realistic GI-like range and include error for visibility
        predicted_ppgi = random.uniform(40.0, 110.0)
        source = 'fallback_random'
        result = {
            "ppgi": round(predicted_ppgi, 2),
            "input_summary": payload.dict(),
            "source": source,
            "warning": f"Model prediction failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        _last_result = result
        return JSONResponse(result)

# Route for the main prediction page
@app.get("/", response_class=FileResponse)
async def index():
    """Return the static index page (Prediction Form)."""
    fp = Path(__file__).parent.parent / "static" / "index.html"
    return FileResponse(fp)

# Alias to calculator
@app.get("/calculate", response_class=FileResponse)
async def calculate():
    fp = Path(__file__).parent.parent / "static" / "index.html"
    return FileResponse(fp)

# Route for the About Us page
@app.get("/about", response_class=FileResponse)
async def about():
    """Return the static about page."""
    fp = Path(__file__).parent.parent / "static" / "about.html"
    return FileResponse(fp)

# Route for the Documentation page
@app.get("/docs", response_class=FileResponse)
async def docs():
    """Return the static documentation page."""
    fp = Path(__file__).parent.parent / "static" / "docs.html"
    return FileResponse(fp)

# Introduction page
@app.get("/introduction", response_class=FileResponse)
async def introduction():
    fp = Path(__file__).parent.parent / "static" / "introduction.html"
    return FileResponse(fp)

# How-to page
@app.get("/how-to", response_class=FileResponse)
async def how_to():
    fp = Path(__file__).parent.parent / "static" / "howto.html"
    return FileResponse(fp)

# Saved results page
@app.get("/saved", response_class=FileResponse)
async def saved():
    fp = Path(__file__).parent.parent / "static" / "saved.html"
    return FileResponse(fp)

# Last result as JSON
@app.get("/api/last_result")
async def last_result():
    if _last_result is None:
        return JSONResponse({"exists": False})
    return JSONResponse({"exists": True, "result": _last_result})

# Last result as CSV download
@app.get("/api/last_result.csv")
async def last_result_csv():
    if _last_result is None:
        return JSONResponse({"detail": "No result available"}, status_code=404)

    # Flatten payload for CSV
    r = _last_result.copy()
    payload = r.pop("input_summary", {})
    flat = {**payload, **r}

    # Consistent column order
    cols = [
        'gender','age','weight','waist_circumference','birth_place','blood_group',
        'family_history','physical_activity','food_item','carb','protein','fat','dietary_fiber',
        'ppgi','iauc_food','iauc_glucose_ref','source','timestamp'
    ]
    for k in list(flat.keys()):
        if k not in cols:
            cols.append(k)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols)
    writer.writeheader()
    writer.writerow({c: flat.get(c, '') for c in cols})
    buf.seek(0)
    filename = f"ppgi_result_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(buf, media_type='text/csv', headers=headers)

# Lightweight health endpoint for readiness/liveness checks
@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})
