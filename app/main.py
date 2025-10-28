from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional
import io
import csv
from datetime import datetime

import numpy as np
import pandas as pd

app = FastAPI(title="PPGI FastAPI")

# Serve the static frontend from the "static" directory (reverted to relative for Railway)
app.mount("/static", StaticFiles(directory="static"), name="static")

class PredictInput(BaseModel):
    age: float = 30.0
    weight: float = 70.0
    height_cm: Optional[float] = None
    waist_circumference: float = 80.0
    food_item: str = ""
    carb: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    dietary_fiber: float = 0.0
    # Portion of the food (grams) consumed in this serving
    portion_g: float = 100.0
    # If true, the nutrient numbers provided (carb/protein/fat/fiber)
    # are for the serving (the value is per-serving). When set, server
    # will convert them to per-100g before passing to the model.
    nutrients_per_serving: bool = False

_rf_model: Optional[object] = None
_feature_columns: Optional[list] = None
_is_pipeline: bool = False
_last_result: Optional[dict] = None
_target_encoder: Optional[object] = None

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

    # Interactions with Age (to mirror training features like nutrient_x_Age)
    nutrient_cols = ['Carb(g/100g)', 'Protien(g/100g)', 'Fat(g/100g)', 'Dietary Fiber(g/100g)']
    if 'Age' in df.columns:
        for nutrient in nutrient_cols:
            df[f'{nutrient}_x_Age'] = df[nutrient] * df['Age']

    # Interactions with BMI when available (to mirror training nutrient_x_BMI)
    if 'BMI(kg/m2)' in df.columns:
        for nutrient in nutrient_cols:
            df[f'{nutrient}_x_BMI'] = df[nutrient] * df['BMI(kg/m2)']

    # Interactions with WC/HC
    for nutrient in nutrient_cols:
        df[f'WC/HC_x_{nutrient}'] = df['WC/HC'] * df[nutrient]

    return df

def _load_rf_model():
    """Lazy-load Random Forest model from joblib, and optional target encoder.

    Captures feature columns if available and attempts to load a saved
    target encoder (target_encoder.joblib) to reproduce training preprocessing
    for categorical variables when not using a full Pipeline.
    """
    global _rf_model, _feature_columns, _is_pipeline, _target_encoder
    if _rf_model is not None:
        return _rf_model

    try:
        import joblib  # scikit-learn models are typically saved with joblib
    except Exception as e:
        raise RuntimeError("joblib is required to load the RandomForest model.") from e

    # Model path preference: prefer full Pipeline if available, otherwise RF model.
    root = Path(__file__).parent.parent
    # Ensure custom training modules (e.g., ml_pipeline.py) are importable when loading a Pipeline
    try:
        import sys as _sys
        nb_dir = root / 'NoteBooks'
        if nb_dir.exists():
            p = str(nb_dir)
            if p not in _sys.path:
                _sys.path.insert(0, p)
    except Exception:
        pass
    candidates = [
        root / 'NoteBooks' / 'out' / 'final_iauc_pipeline.joblib',
        root / 'random_forest_model.joblib',
        root / 'NoteBooks' / 'random_forest_model.joblib',
    ]
    # Attempt to load a saved target encoder if present
    try:
        if _target_encoder is None:
            enc_cands = [
                root / 'target_encoder.joblib',
                root / 'NoteBooks' / 'out' / 'target_encoder.joblib',
                root / 'NoteBooks' / 'target_encoder.joblib',
            ]
            for ec in enc_cands:
                if ec.exists():
                    try:
                        _target_encoder = joblib.load(str(ec))
                        break
                    except Exception:
                        continue
    except Exception:
        pass
    last_err: Optional[Exception] = None
    for c in candidates:
        if not c.exists():
            continue
        try:
            model = joblib.load(str(c))
        except ModuleNotFoundError as e:
            # If the pipeline refers to a custom module (e.g., ml_pipeline) that's not
            # present in the server environment, skip this candidate and try next.
            last_err = e
            continue
        except Exception as e:
            last_err = e
            continue

        # Loaded successfully; determine model type and feature info
        try:
            from sklearn.pipeline import Pipeline  # type: ignore
            if isinstance(model, Pipeline):
                _is_pipeline = True
                _rf_model = model
                return _rf_model
            if hasattr(model, 'feature_names_in_'):
                _feature_columns = list(model.feature_names_in_)
            elif isinstance(model, tuple) and len(model) == 2:
                m, cols = model
                _rf_model = m
                _feature_columns = list(cols)
                return _rf_model
        except Exception:
            _feature_columns = None

        _rf_model = model
        return _rf_model

    # If we got here, nothing loaded; surface a helpful message
    if last_err is not None:
        raise RuntimeError(
            "Failed to load model. If using a saved Pipeline, ensure any custom modules used in training (e.g., ml_pipeline) are available at runtime; otherwise provide the bare RandomForest model artifact."
        ) from last_err
    raise FileNotFoundError('Model not found. Expected final_iauc_pipeline.joblib (NoteBooks/out/) or random_forest_model.joblib (project root/NoteBooks/)')

def _build_feature_frame(payload: PredictInput) -> pd.DataFrame:
    # Build the input dataframe
    hip_circ = 95.0  # Assumed hip circumference if not collected
    wc = float(payload.waist_circumference or 0.0)
    wth_ratio = (wc / hip_circ) if hip_circ else 0.0

    if _is_pipeline:
        # For full Pipeline models: provide raw features, let the pipeline handle encoding/FE
        # Compute BMI if height is provided
        h_cm = float(payload.height_cm) if (getattr(payload, 'height_cm', None) not in (None, "")) else None
        bmi = float(payload.weight) / ((h_cm/100.0)**2) if (h_cm and h_cm > 0) else np.nan
        df_raw = pd.DataFrame([{
            # We keep minimal UI; set stable defaults for categorical fields used in training
            'Gender': 'Male',
            'Age': float(payload.age or 0.0),
            'Weight(kg)': float(payload.weight or 0.0),
            'Height(cm)': h_cm if h_cm else np.nan,
            'BMI(kg/m2)': bmi,
            'Waist circumference': wc,
            'Hip circumference': hip_circ,
            'WC/HC': wth_ratio,
            'Family history diabetics': 'No',
            'Physical activity': 'Light',
            'Health Problem': 'None',
            'Alcoholic': 'No',
            'Blood Group': 'Unknown',
            'Carb(g/100g)': float(payload.carb or 0.0),
            'Protien(g/100g)': float(payload.protein or 0.0),
            'Fat(g/100g)': float(payload.fat or 0.0),
            'Dietary Fiber(g/100g)': float(payload.dietary_fiber or 0.0),
        }])
        return df_raw
    else:
        # For bare RF models: do local feature engineering matching training as closely as feasible
        # Compute BMI if height is provided
        h_cm = float(payload.height_cm) if (getattr(payload, 'height_cm', None) not in (None, "")) else None
        bmi = float(payload.weight) / ((h_cm/100.0)**2) if (h_cm and h_cm > 0) else np.nan
        df = pd.DataFrame([{
            'Age': float(payload.age or 0.0),
            'Weight(kg)': float(payload.weight or 0.0),
            'Height(cm)': h_cm if h_cm else np.nan,
            'Waist circumference': wc,
            'Hip circumference': hip_circ,
            'BMI(kg/m2)': bmi,
            'WC/HC': wth_ratio,
            'Carb(g/100g)': float(payload.carb or 0.0),
            'Protien(g/100g)': float(payload.protein or 0.0),
            'Fat(g/100g)': float(payload.fat or 0.0),
            'Dietary Fiber(g/100g)': float(payload.dietary_fiber or 0.0),
            # Categorical columns present during training; use stable defaults
            'Gender': 'Male',
            'Family history diabetics': 'No',
            'Physical activity': 'Light',
            'Health Problem': 'None',
            'Alcoholic': 'No',
            'Blood Group': 'Unknown',
        }])

        # Feature engineering similar to notebook
        df_eng = _engineer_features(df)

        # If a target encoder was saved and loaded, apply it now (transform only)
        # NOTE: Encoder was fitted BEFORE dropping 'WC/HC' and 'BMI(kg/m2)' in the notebook,
        # so preserve those columns for transform and drop them afterwards.
        if _target_encoder is not None:
            try:
                df_enc = _target_encoder.transform(df_eng)
                if isinstance(df_enc, pd.DataFrame):
                    df_eng = df_enc
            except Exception:
                # If encoding fails, fall back to unencoded dataframe
                pass

        # Drop columns that were dropped at train time if present (post-encoding)
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
    """Predict GI (PPGI) as 100 * IAUC(food) / IAUC(glucose-ref).

    Notes:
    - Model inputs are always treated as per-100g nutritional values (labels: g/100g).
    - User can specify a portion size (grams). Portion is NOT fed to the model,
      but is used to compute Glycemic Load (GL) based on GI and carbs-per-serving.
    - Glucose reference is defined as a 100g portion with 100g carbohydrate and
      0 protein/fat/fiber.
    """

    global _last_result

    def _frame_with_override_nutrients(base: PredictInput, carb: float, prot: float, fat: float, fiber: float) -> pd.DataFrame:
        """Helper to override only nutrient fields while keeping user metadata constant."""
        temp_dict = base.dict()
        temp_dict.update({
            'carb': carb,
            'protein': prot,
            'fat': fat,
            'dietary_fiber': fiber,
        })
        temp = PredictInput(**temp_dict)
        return _build_feature_frame(temp)

    def _prepare_X(df: pd.DataFrame) -> pd.DataFrame:
        """Align/features and coerce to numeric to satisfy the RandomForest input.

        - If the model exposes feature_names_in_, add any missing columns with 0 and order columns.
        - Then coerce all values to numeric (non-numeric become NaN) and fill NaN with 0.0 to
          avoid string-to-float errors.
        """
        global _feature_columns
        if _feature_columns:
            for col in _feature_columns:
                if col not in df.columns:
                    df[col] = 0.0
            # Drop any extra columns not used by the model
            df = df[_feature_columns]
        # Ensure purely numeric matrix and no NaNs
        df = df.apply(pd.to_numeric, errors='coerce').fillna(0.0)
        return df

    try:
        model = _load_rf_model()

        # Determine how to interpret the user-provided nutrient fields.
        # If nutrients_per_serving=True, payload.carb/protein/fat/fiber are per-serving
        # and must be converted to per-100g before feeding the model.
        if getattr(payload, 'nutrients_per_serving', False):
            # Validate portion for per-serving conversion
            if float(payload.portion_g or 0.0) <= 0:
                return JSONResponse(
                    {"detail": "Invalid portion_g for per-serving nutrients: must be > 0 grams."},
                    status_code=400,
                )
            # Convert per-serving -> per-100g
            portion = float(payload.portion_g)
            carb_per_100g = float(payload.carb) * 100.0 / portion
            protein_per_100g = float(payload.protein) * 100.0 / portion
            fat_per_100g = float(payload.fat) * 100.0 / portion
            fiber_per_100g = float(payload.dietary_fiber) * 100.0 / portion

            # Build a temporary PredictInput with converted per-100g nutrients
            temp = PredictInput(**{**payload.dict(), 'carb': carb_per_100g, 'protein': protein_per_100g, 'fat': fat_per_100g, 'dietary_fiber': fiber_per_100g})
            X_food = _build_feature_frame(temp)
        else:
            # Payload nutrients are already per-100g
            X_food = _build_feature_frame(payload)
        if not _is_pipeline:
            X_food = _prepare_X(X_food)
        iauc_food = float(model.predict(X_food)[0])

        # IAUC for 100g glucose reference (100g carb, others 0)
        X_glu = _frame_with_override_nutrients(payload, carb=100.0, prot=0.0, fat=0.0, fiber=0.0)
        if not _is_pipeline:
            X_glu = _prepare_X(X_glu)
        iauc_glu = float(model.predict(X_glu)[0])

        # Guard against zero/negative reference
        if iauc_glu <= 0:
            raise ValueError(f"Invalid glucose reference IAUC: {iauc_glu}")

        # GI calculation
        ppgi_val = 100.0 * iauc_food / iauc_glu

        # Compute carbs per serving. If the user provided nutrients per-serving,
        # payload.carb already represents carbs_per_serving; otherwise derive from per-100g
        if getattr(payload, 'nutrients_per_serving', False):
            carbs_per_serving = float(payload.carb or 0.0)
            carb_per_100g_value = round((float(payload.carb or 0.0) * 100.0 / float(payload.portion_g or 100.0)), 2) if float(payload.portion_g or 0.0) > 0 else round(float(payload.carb or 0.0), 2)
            protein_per_100g_value = round((float(payload.protein or 0.0) * 100.0 / float(payload.portion_g or 100.0)), 2) if float(payload.portion_g or 0.0) > 0 else round(float(payload.protein or 0.0), 2)
            fat_per_100g_value = round((float(payload.fat or 0.0) * 100.0 / float(payload.portion_g or 100.0)), 2) if float(payload.portion_g or 0.0) > 0 else round(float(payload.fat or 0.0), 2)
            fiber_per_100g_value = round((float(payload.dietary_fiber or 0.0) * 100.0 / float(payload.portion_g or 100.0)), 2) if float(payload.portion_g or 0.0) > 0 else round(float(payload.dietary_fiber or 0.0), 2)
        else:
            carbs_per_serving = float(payload.carb or 0.0) * float(payload.portion_g or 0.0) / 100.0
            carb_per_100g_value = round(float(payload.carb or 0.0), 2)
            protein_per_100g_value = round(float(payload.protein or 0.0), 2)
            fat_per_100g_value = round(float(payload.fat or 0.0), 2)
            fiber_per_100g_value = round(float(payload.dietary_fiber or 0.0), 2)
        gl_val = (ppgi_val * carbs_per_serving) / 100.0

        result = {
            "ppgi": round(ppgi_val, 2),
            "gl": round(gl_val, 2),
            "carbs_per_serving": round(carbs_per_serving, 2),
            "carb_per_100g": carb_per_100g_value,
            "protein_per_100g": protein_per_100g_value,
            "fat_per_100g": fat_per_100g_value,
            "dietary_fiber_per_100g": fiber_per_100g_value,
            "iauc_food": round(iauc_food, 4),
            "iauc_glucose_ref": round(iauc_glu, 4),
            "input_summary": payload.dict(),
            "source": 'pipeline' if _is_pipeline else 'random_forest',
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

        # Cache last result in-memory
        _last_result = result
        return JSONResponse(result)

    except Exception as e:
        # Production behavior: do not generate synthetic predictions; return an error
        return JSONResponse(
            {
                "detail": "Prediction failed. Please try again later.",
                "error": str(e),
                "error_class": e.__class__.__name__,
            },
            status_code=500,
        )

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
        'age','weight','height_cm','waist_circumference','food_item',
        'carb','protein','fat','dietary_fiber','portion_g',
        'carb_per_100g','protein_per_100g','fat_per_100g','dietary_fiber_per_100g',
        'carbs_per_serving','ppgi','gl','iauc_food','iauc_glucose_ref','source','timestamp'
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
