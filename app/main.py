from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import random
from pathlib import Path

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

@app.post("/api/predict")
async def predict(payload: PredictInput):
    """Simple prediction endpoint. Replace the implementation with your real model call."""
    # Placeholder model: random result in realistic range
    predicted_ppgi = random.uniform(40.0, 110.0)

    return JSONResponse({
        "ppgi": round(predicted_ppgi, 2),
        "input_summary": payload.dict()
    })

@app.get("/", response_class=FileResponse)
async def index():
    """Return the static index page."""
    # Serve the static/index.html file
    fp = Path(__file__).parent.parent / "static" / "index.html"
    return FileResponse(fp)
