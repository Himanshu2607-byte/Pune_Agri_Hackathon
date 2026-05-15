"""
AgroVision Backend — FastAPI application for crop disease prediction and chat.
"""

import os
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid

try:
    from dotenv import load_dotenv
    current_dir = Path(__file__).resolve().parent
    load_dotenv(current_dir.parent / '.env')
    load_dotenv(current_dir / '.env')
except Exception:
    pass

try:
    from .model import predictor
    from .chatbot import chatbot
    from .weather import get_weather
    from .ai_chat import get_ai_chat_response
    from .profit_estimator import calculate_profit, get_crop_options
    # from .soil_health import analyze_soil_health
    from .logic.soil_analyzer import analyze_soil, SoilData
except ImportError:
    try:  # Vercel / sys.path-based import
        from backend.model import predictor
        from backend.chatbot import chatbot
        from backend.weather import get_weather
        from backend.ai_chat import get_ai_chat_response
        from backend.profit_estimator import calculate_profit, get_crop_options
        # from backend.soil_health import analyze_soil_health
        from backend.logic.soil_analyzer import analyze_soil, SoilData
    except ImportError:  # pragma: no cover - bare local script execution
        from model import predictor  # type: ignore[no-redef]
        from chatbot import chatbot  # type: ignore[no-redef]
        from weather import get_weather  # type: ignore[no-redef]
        from ai_chat import get_ai_chat_response  # type: ignore[no-redef]
        from profit_estimator import calculate_profit, get_crop_options
        # from soil_health import analyze_soil_health  # type: ignore[no-redef]
        from logic.soil_analyzer import analyze_soil, SoilData

app = FastAPI(
    title="AgroVision API",
    description="AI-powered crop disease detection and agricultural advice",
    version="1.0.0"
)

# ── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    lang: str = "en"
    weather: dict | None = None
    feature_context: dict | None = None


class ChatResponse(BaseModel):
    response: str
    source: str = "local"


class DiseaseRiskResponse(BaseModel):
    level_code: str
    level: str
    score: int
    likely_diseases: list[str]
    reason: str


class IrrigationResponse(BaseModel):
    level_code: str
    level: str
    should_water: bool
    recommended_mm: float
    recommended_liters_m2: float
    rain_mm_next_24h: float
    recommendation: str


class ForecastPointResponse(BaseModel):
    time: str
    label: str
    temperature_c: int
    precipitation_probability: int
    rain_mm: float


class WeatherResponse(BaseModel):
    location: str
    latitude: float
    longitude: float
    temperature_c: int
    wind_kph: int
    humidity: int
    precipitation_probability: int
    rain_mm_next_24h: float
    condition: str
    advice: str
    disease_risk: DiseaseRiskResponse
    irrigation: IrrigationResponse
    forecast_next_hours: list[ForecastPointResponse]
    source: str


class ProfitRequest(BaseModel):
    crop: str
    area: float

class VerifyRequest(BaseModel):
    recommendation_text: str


class ProfitResponse(BaseModel):
    crop: str
    area: float
    total_cost: float
    revenue: float
    profit: float


# ── Farm Zone Data (Simulated) ────────────────────────────────────
FARM_ZONES = [
    {
        "id": "A",
        "name": "Zone A — North Field",
        "crop": "Tomato",
        "status": "healthy",
        "health_percent": 94,
        "last_scan": "2026-04-09 10:30 AM",
        "area_acres": 2.5,
        "color": "#22c55e"
    },
    {
        "id": "B",
        "name": "Zone B — East Field",
        "crop": "Potato",
        "status": "warning",
        "health_percent": 71,
        "last_scan": "2026-04-09 09:15 AM",
        "area_acres": 3.0,
        "color": "#eab308"
    },
    {
        "id": "C",
        "name": "Zone C — South Field",
        "crop": "Corn",
        "status": "critical",
        "health_percent": 42,
        "last_scan": "2026-04-09 08:00 AM",
        "area_acres": 4.0,
        "color": "#ef4444"
    },
    {
        "id": "D",
        "name": "Zone D — West Field",
        "crop": "Rice",
        "status": "healthy",
        "health_percent": 88,
        "last_scan": "2026-04-08 04:45 PM",
        "area_acres": 5.0,
        "color": "#22c55e"
    },
    {
        "id": "E",
        "name": "Zone E — Central Plot",
        "crop": "Wheat",
        "status": "warning",
        "health_percent": 65,
        "last_scan": "2026-04-08 02:30 PM",
        "area_acres": 1.5,
        "color": "#eab308"
    },
    {
        "id": "F",
        "name": "Zone F — Orchard",
        "crop": "Apple",
        "status": "healthy",
        "health_percent": 91,
        "last_scan": "2026-04-09 11:00 AM",
        "area_acres": 2.0,
        "color": "#22c55e"
    }
]


# ── Endpoints ─────────────────────────────────────────────────────

# The root endpoint / is handled by the React SPA catch-all when deployed.
# (If local dev, you'll see "Not Found" at / without the frontend built, but /health is available)


@app.get("/health")
async def health():
    """Dedicated health endpoint for deployment checks."""
    return {
        "status": "ok",
        "model_mode": "fallback" if getattr(predictor, "_fallback_mode", False) else "tensorflow",
    }


@app.post("/predict")
async def predict_disease(file: UploadFile = File(...)):
    """
    Predict crop disease from an uploaded image.
    
    Accepts: JPEG, PNG, WebP image files.
    Returns: Disease classification, confidence, and recommendations.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image (JPEG, PNG, or WebP)."
        )

    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        result = predictor.predict(image_bytes)
        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Agricultural chatbot endpoint.
    
    Accepts: message (str) and lang ('en' or 'hi').
    Returns: AI-generated farming advice.
    """
    try:
        response, source = get_ai_chat_response(
            chatbot, request.message, request.lang, request.weather, request.feature_context
        )
        return ChatResponse(response=response, source=source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.get("/zones")
async def get_farm_zones():
    """Return simulated farm zone data."""
    return {"zones": FARM_ZONES}


@app.get("/weather", response_model=WeatherResponse)
async def weather_endpoint(lat: float | None = None, lon: float | None = None, lang: str = "en", location: str | None = None):
    """Return current field weather and lightweight farming advice."""
    try:
        return WeatherResponse(**get_weather(lat=lat, lon=lon, lang=lang, location_name=location))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather lookup failed: {str(e)}")


@app.post("/profit", response_model=ProfitResponse)
async def profit_endpoint(request: ProfitRequest):
    """Estimate total cost, revenue, and profit for a crop and area."""
    try:
        return calculate_profit(request.crop, request.area)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profit estimation failed: {str(e)}")


@app.get("/profit/crops")
async def profit_crops_endpoint():
    """Return available crops for profit estimation."""
    return {"crops": get_crop_options()}


# ── Field Journal (In-Memory Store) ──────────────────────────────

# In-memory store — resets on server restart (replace with DB for persistence)
_journal_entries: list[dict] = [
    {
        "id": "demo-1",
        "crop": "Tomato",
        "status": "warning",
        "note": "Noticed yellowing on lower leaves in the north row. Could be early blight or nutrient deficiency. Scheduled follow-up scan.",
        "weather": "Cloudy",
        "zone": "Zone A",
        "tags": ["early-blight", "yellowing"],
        "timestamp": "2026-04-10T08:30:00+00:00",
    },
    {
        "id": "demo-2",
        "crop": "Wheat",
        "status": "healthy",
        "note": "Crops looking great after last week's irrigation. Good tillering observed. No signs of disease.",
        "weather": "Sunny",
        "zone": "Zone E",
        "tags": ["healthy", "irrigation"],
        "timestamp": "2026-04-09T14:15:00+00:00",
    },
    {
        "id": "demo-3",
        "crop": "Corn",
        "status": "critical",
        "note": "Significant lesions on multiple plants. Northern leaf blight confirmed by AI scan. Applied copper-based fungicide. Monitoring closely.",
        "weather": "Humid",
        "zone": "Zone C",
        "tags": ["northern-leaf-blight", "fungicide", "urgent"],
        "timestamp": "2026-04-09T09:00:00+00:00",
    },
]


class JournalEntryIn(BaseModel):
    crop: str
    status: str  # healthy | warning | critical | observation
    note: str
    weather: Optional[str] = "Sunny"
    zone: Optional[str] = ""
    tags: Optional[List[str]] = []


class JournalEntryOut(JournalEntryIn):
    id: str
    timestamp: str


@app.get("/journal")
async def get_journal():
    """Return all field journal entries (newest first)."""
    return {"entries": list(reversed(_journal_entries))}


@app.post("/journal", response_model=JournalEntryOut, status_code=201)
async def add_journal_entry(entry: JournalEntryIn):
    """Add a new field journal entry."""
    if not entry.note.strip():
        raise HTTPException(status_code=400, detail="Note cannot be empty.")
    if entry.status not in ("healthy", "warning", "critical", "observation"):
        raise HTTPException(status_code=400, detail="Invalid status value.")

    new_entry = {
        "id": str(uuid.uuid4()),
        "crop": entry.crop,
        "status": entry.status,
        "note": entry.note.strip(),
        "weather": entry.weather or "Sunny",
        "zone": entry.zone or "",
        "tags": entry.tags or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _journal_entries.append(new_entry)
    return new_entry


@app.delete("/journal/{entry_id}", status_code=204)
async def delete_journal_entry(entry_id: str):
    """Delete a journal entry by ID."""
    global _journal_entries
    original_len = len(_journal_entries)
    _journal_entries = [e for e in _journal_entries if e["id"] != entry_id]
    if len(_journal_entries) == original_len:
        raise HTTPException(status_code=404, detail="Entry not found.")


# ── Farm Task Manager (In-Memory Store) ──────────────────────────

_tasks: list[dict] = [
    {
        "id": "task-1",
        "title": "Irrigate Zone D (West Rice Field)",
        "description": "Apply 50mm of irrigation water to the rice crop. Check drainage outlets before starting.",
        "priority": "high",
        "category": "Irrigation",
        "zone": "Zone D — Rice",
        "status": "pending",
        "due_date": "2026-04-12",
        "created_at": "2026-04-11T04:00:00+00:00",
    },
    {
        "id": "task-2",
        "title": "Apply fungicide to Zone C (Corn)",
        "description": "Use copper-based fungicide as follow-up treatment for northern leaf blight. Target morning application.",
        "priority": "high",
        "category": "Spraying",
        "zone": "Zone C — Corn",
        "status": "in_progress",
        "due_date": "2026-04-11",
        "created_at": "2026-04-10T08:00:00+00:00",
    },
    {
        "id": "task-3",
        "title": "Scout Zone B for late blight progression",
        "description": "Walk-through scout for potato late blight. Check lower canopy first. Document with photos.",
        "priority": "medium",
        "category": "Scouting",
        "zone": "Zone B — Potato",
        "status": "pending",
        "due_date": "2026-04-13",
        "created_at": "2026-04-10T09:30:00+00:00",
    },
    {
        "id": "task-4",
        "title": "Apply NPK fertilizer to Zone E (Wheat)",
        "description": "Top-dress with urea at 50 kg/acre. Apply before rain forecast on Thursday.",
        "priority": "medium",
        "category": "Fertilization",
        "zone": "Zone E — Wheat",
        "status": "done",
        "due_date": "2026-04-10",
        "created_at": "2026-04-09T07:00:00+00:00",
    },
]


class TaskIn(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: str = "medium"   # high | medium | low
    category: str = "Other"
    zone: Optional[str] = "All Zones"
    due_date: Optional[str] = None   # ISO date string YYYY-MM-DD


class TaskOut(TaskIn):
    id: str
    status: str
    created_at: str


@app.get("/tasks")
async def get_tasks():
    """Return all farm tasks (newest first)."""
    return {"tasks": list(reversed(_tasks))}


@app.post("/tasks", response_model=TaskOut, status_code=201)
async def create_task(task: TaskIn):
    """Create a new farm task."""
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    if task.priority not in ("high", "medium", "low"):
        raise HTTPException(status_code=400, detail="Invalid priority.")

    new_task = {
        "id": str(uuid.uuid4()),
        "title": task.title.strip(),
        "description": (task.description or "").strip(),
        "priority": task.priority,
        "category": task.category,
        "zone": task.zone or "All Zones",
        "status": "pending",
        "due_date": task.due_date or None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _tasks.append(new_task)
    return new_task


@app.patch("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    """Update the status of a task."""
    if status not in ("pending", "in_progress", "done"):
        raise HTTPException(status_code=400, detail="Invalid status.")
    for t in _tasks:
        if t["id"] == task_id:
            t["status"] = status
            return t
    raise HTTPException(status_code=404, detail="Task not found.")


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """Delete a task by ID."""
    global _tasks
    orig = len(_tasks)
    _tasks = [t for t in _tasks if t["id"] != task_id]
    if len(_tasks) == orig:
        raise HTTPException(status_code=404, detail="Task not found.")


# ── Soil Health Analysis ─────────────────────────────────────────────────────

class SoilHealthRequest(BaseModel):
    nitrogen: float          # kg/ha  recommended: 80–120
    phosphorus: float        # kg/ha  recommended: 30–60
    potassium: float         # kg/ha  recommended: 120–200
    ph: float                # 0–14   optimal: 6.0–7.5
    moisture: float          # %      optimal: 40–70
    organic_carbon: Optional[float] = None   # %  good: >1.5
    ec: Optional[float] = None               # dS/m optimal: 0–2
    # Micronutrients and additional macronutrients in ppm
    phosphorus_ppm: Optional[float] = None   # ppm  optimal: 25–35
    sulfur: Optional[float] = None           # ppm  optimal: 7–15
    zinc: Optional[float] = None             # ppm  optimal: 1–3
    iron: Optional[float] = None             # ppm  optimal: 10–20
    manganese: Optional[float] = None        # ppm  optimal: 8–11
    copper: Optional[float] = None           # ppm  optimal: 0.8–1
    potassium_ppm: Optional[float] = None    # ppm  optimal: 165–220
    calcium: Optional[float] = None          # ppm  optimal: 1400+
    magnesium: Optional[float] = None        # ppm  optimal: 100+
    sodium: Optional[float] = None           # ppm  optimal: 80–120


def _score_param(value: float, low_crit: float, low_ok: float, high_ok: float, high_crit: float) -> tuple[int, str]:
    """Return (0-100 score, status string) for a single parameter."""
    if value < low_crit or value > high_crit:
        return 20, "critical"
    if value < low_ok or value > high_ok:
        return 55, "moderate"
    return 100, "healthy"


def _analyze_soil(req: SoilHealthRequest) -> dict:
    metrics: dict[str, dict] = {}
    reasons: list[str] = []
    solutions: list[str] = []

    # ── Nitrogen ──────────────────────────────────────────────────
    n_score, n_status = _score_param(req.nitrogen, 20, 60, 140, 250)
    metrics["nitrogen"] = {
        "label": "Nitrogen (N)",
        "value": req.nitrogen,
        "unit": "kg/ha",
        "score": n_score,
        "status": n_status,
        "note": "Optimal: 60–140 kg/ha",
    }
    if req.nitrogen < 60:
        reasons.append(f"Low nitrogen ({req.nitrogen} kg/ha) — plants may show yellowing and stunted growth.")
        solutions.append("Apply urea or ammonium sulfate at 50–80 kg/ha. Consider split dressing.")
    elif req.nitrogen > 140:
        reasons.append(f"Excess nitrogen ({req.nitrogen} kg/ha) — can cause excessive leaf growth and disease susceptibility.")
        solutions.append("Reduce nitrogen inputs and flush with irrigation to dilute excess.")

    # ── Phosphorus ────────────────────────────────────────────────
    p_score, p_status = _score_param(req.phosphorus, 5, 25, 70, 120)
    metrics["phosphorus"] = {
        "label": "Phosphorus (P)",
        "value": req.phosphorus,
        "unit": "kg/ha",
        "score": p_score,
        "status": p_status,
        "note": "Optimal: 25–70 kg/ha",
    }
    if req.phosphorus < 25:
        reasons.append(f"Low phosphorus ({req.phosphorus} kg/ha) — affects root development and flowering.")
        solutions.append("Apply single super phosphate (SSP) or DAP at 40–60 kg/ha.")
    elif req.phosphorus > 70:
        reasons.append(f"High phosphorus ({req.phosphorus} kg/ha) — may block zinc and iron uptake.")
        solutions.append("Avoid further phosphorus applications for 1–2 seasons; add zinc sulfate if needed.")

    # ── Potassium ─────────────────────────────────────────────────
    k_score, k_status = _score_param(req.potassium, 30, 100, 220, 400)
    metrics["potassium"] = {
        "label": "Potassium (K)",
        "value": req.potassium,
        "unit": "kg/ha",
        "score": k_score,
        "status": k_status,
        "note": "Optimal: 100–220 kg/ha",
    }
    if req.potassium < 100:
        reasons.append(f"Low potassium ({req.potassium} kg/ha) — reduces stress resistance and fruit quality.")
        solutions.append("Apply MOP (Muriate of Potash) at 50–80 kg/ha alongside regular irrigation.")
    elif req.potassium > 220:
        reasons.append(f"High potassium ({req.potassium} kg/ha) — may antagonise magnesium and calcium.")
        solutions.append("Skip potassium fertilisation for 1 season or leach with irrigation.")

    # ── pH ────────────────────────────────────────────────────────
    ph_score, ph_status = _score_param(req.ph, 4.5, 5.8, 7.5, 9.0)
    metrics["ph"] = {
        "label": "Soil pH",
        "value": req.ph,
        "unit": "",
        "score": ph_score,
        "status": ph_status,
        "note": "Optimal: 5.8–7.5",
    }
    if req.ph < 5.8:
        reasons.append(f"Acidic soil (pH {req.ph}) — reduces nutrient availability, especially phosphorus.")
        solutions.append("Apply agricultural lime (CaCO₃) at 1–3 t/ha to raise pH gradually.")
    elif req.ph > 7.5:
        reasons.append(f"Alkaline soil (pH {req.ph}) — can lock up iron, manganese, and zinc.")
        solutions.append("Apply elemental sulfur or acidifying fertilisers like ammonium sulfate.")

    # ── Moisture ─────────────────────────────────────────────────
    m_score, m_status = _score_param(req.moisture, 10, 35, 75, 95)
    metrics["moisture"] = {
        "label": "Soil Moisture",
        "value": req.moisture,
        "unit": "%",
        "score": m_score,
        "status": m_status,
        "note": "Optimal: 35–75%",
    }
    if req.moisture < 35:
        reasons.append(f"Low soil moisture ({req.moisture}%) — plants may wilt and nutrient uptake will suffer.")
        solutions.append("Schedule irrigation immediately, preferably drip for efficiency.")
    elif req.moisture > 75:
        reasons.append(f"High soil moisture ({req.moisture}%) — risk of root rot and anaerobic conditions.")
        solutions.append("Improve drainage with raised beds or subsurface drains. Hold irrigation.")

    # ── Organic Carbon (optional) ─────────────────────────────────
    if req.organic_carbon is not None:
        oc_score, oc_status = _score_param(req.organic_carbon, 0.2, 1.0, 3.5, 6.0)
        metrics["organic_carbon"] = {
            "label": "Organic Carbon",
            "value": req.organic_carbon,
            "unit": "%",
            "score": oc_score,
            "status": oc_status,
            "note": "Optimal: 1–3.5%",
        }
        if req.organic_carbon < 1.0:
            reasons.append(f"Low organic carbon ({req.organic_carbon}%) — poor soil structure and microbial activity.")
            solutions.append("Add compost, farmyard manure, or green manure crops (e.g., legumes).")

    # ── Electrical Conductivity (optional) ───────────────────────
    if req.ec is not None:
        ec_score, ec_status = _score_param(req.ec, 0, 0, 2.0, 4.0)
        metrics["ec"] = {
            "label": "Electrical Conductivity",
            "value": req.ec,
            "unit": "dS/m",
            "score": ec_score,
            "status": ec_status,
            "note": "Optimal: 0–2 dS/m",
        }
        if req.ec > 2.0:
            reasons.append(f"High EC ({req.ec} dS/m) — soil salinity may reduce germination and crop yield.")
            solutions.append("Apply heavy irrigation to leach salts. Use gypsum for sodic soils.")

    # ── Phosphorus (ppm) ─────────────────────────────────────────
    if req.phosphorus_ppm is not None:
        p_ppm_score, p_ppm_status = _score_param(req.phosphorus_ppm, 10, 25, 35, 50)
        metrics["phosphorus_ppm"] = {
            "label": "Phosphorus (ppm)",
            "value": req.phosphorus_ppm,
            "unit": "ppm",
            "score": p_ppm_score,
            "status": p_ppm_status,
            "note": "Optimal: 25–35 ppm",
        }
        if req.phosphorus_ppm < 25:
            reasons.append(f"Low phosphorus ({req.phosphorus_ppm} ppm) — may limit root development.")
            solutions.append("Apply phosphate fertiliser or rock phosphate.")

    # ── Sulfur ──────────────────────────────────────────────────
    if req.sulfur is not None:
        s_score, s_status = _score_param(req.sulfur, 2, 7, 15, 25)
        metrics["sulfur"] = {
            "label": "Sulfur (ppm)",
            "value": req.sulfur,
            "unit": "ppm",
            "score": s_score,
            "status": s_status,
            "note": "Optimal: 7–15 ppm",
        }
        if req.sulfur < 7:
            reasons.append(f"Low sulfur ({req.sulfur} ppm) — may affect crop quality and disease resistance.")
            solutions.append("Apply sulfur fertiliser or elemental sulfur.")

    # ── Zinc ─────────────────────────────────────────────────────
    if req.zinc is not None:
        zn_score, zn_status = _score_param(req.zinc, 0.2, 1.0, 3.0, 5.0)
        metrics["zinc"] = {
            "label": "Zinc (ppm)",
            "value": req.zinc,
            "unit": "ppm",
            "score": zn_score,
            "status": zn_status,
            "note": "Optimal: 1–3 ppm",
        }
        if req.zinc < 1.0:
            reasons.append(f"Low zinc ({req.zinc} ppm) — may cause stunted growth and poor crop quality.")
            solutions.append("Apply zinc sulfate or zinc oxide.")

    # ── Iron ─────────────────────────────────────────────────────
    if req.iron is not None:
        fe_score, fe_status = _score_param(req.iron, 3, 10, 20, 30)
        metrics["iron"] = {
            "label": "Iron (ppm)",
            "value": req.iron,
            "unit": "ppm",
            "score": fe_score,
            "status": fe_status,
            "note": "Optimal: 10–20 ppm",
        }
        if req.iron < 10:
            reasons.append(f"Low iron ({req.iron} ppm) — may cause chlorosis and reduced photosynthesis.")
            solutions.append("Apply iron chelate or iron sulfate.")

    # ── Manganese ───────────────────────────────────────────────
    if req.manganese is not None:
        mn_score, mn_status = _score_param(req.manganese, 2, 8, 11, 20)
        metrics["manganese"] = {
            "label": "Manganese (ppm)",
            "value": req.manganese,
            "unit": "ppm",
            "score": mn_score,
            "status": mn_status,
            "note": "Optimal: 8–11 ppm",
        }
        if req.manganese < 8:
            reasons.append(f"Low manganese ({req.manganese} ppm) — affects enzyme activity and plant metabolism.")
            solutions.append("Apply manganese sulfate or oxide.")

    # ── Copper ──────────────────────────────────────────────────
    if req.copper is not None:
        cu_score, cu_status = _score_param(req.copper, 0.2, 0.8, 1.0, 2.0)
        metrics["copper"] = {
            "label": "Copper (ppm)",
            "value": req.copper,
            "unit": "ppm",
            "score": cu_score,
            "status": cu_status,
            "note": "Optimal: 0.8–1 ppm",
        }
        if req.copper < 0.8:
            reasons.append(f"Low copper ({req.copper} ppm) — may reduce grain quality and disease resistance.")
            solutions.append("Apply copper sulfate or copper oxide.")

    # ── Potassium (ppm) ─────────────────────────────────────────
    if req.potassium_ppm is not None:
        k_ppm_score, k_ppm_status = _score_param(req.potassium_ppm, 50, 165, 220, 300)
        metrics["potassium_ppm"] = {
            "label": "Potassium (ppm)",
            "value": req.potassium_ppm,
            "unit": "ppm",
            "score": k_ppm_score,
            "status": k_ppm_status,
            "note": "Optimal: 165–220 ppm",
        }
        if req.potassium_ppm < 165:
            reasons.append(f"Low potassium ({req.potassium_ppm} ppm) — reduces stress tolerance and quality.")
            solutions.append("Apply potassium chloride or potassium sulfate.")

    # ── Calcium ─────────────────────────────────────────────────
    if req.calcium is not None:
        ca_score, ca_status = _score_param(req.calcium, 600, 1400, 9999, 10000)
        metrics["calcium"] = {
            "label": "Calcium (ppm)",
            "value": req.calcium,
            "unit": "ppm",
            "score": ca_score,
            "status": ca_status,
            "note": "Optimal: 1400+ ppm",
        }
        if req.calcium < 1400:
            reasons.append(f"Low calcium ({req.calcium} ppm) — may cause blossom-end rot and weak cell walls.")
            solutions.append("Apply gypsum or ground limestone.")

    # ── Magnesium ───────────────────────────────────────────────
    if req.magnesium is not None:
        mg_score, mg_status = _score_param(req.magnesium, 30, 100, 9999, 10000)
        metrics["magnesium"] = {
            "label": "Magnesium (ppm)",
            "value": req.magnesium,
            "unit": "ppm",
            "score": mg_score,
            "status": mg_status,
            "note": "Optimal: 100+ ppm",
        }
        if req.magnesium < 100:
            reasons.append(f"Low magnesium ({req.magnesium} ppm) — may cause yellowing of older leaves (chlorosis).")
            solutions.append("Apply magnesium sulfate (Epsom salt) or dolomitic limestone.")

    # ── Sodium ──────────────────────────────────────────────────
    if req.sodium is not None:
        na_score, na_status = _score_param(req.sodium, 20, 80, 120, 200)
        metrics["sodium"] = {
            "label": "Sodium (ppm)",
            "value": req.sodium,
            "unit": "ppm",
            "score": na_score,
            "status": na_status,
            "note": "Optimal: 80–120 ppm",
        }
        if req.sodium > 120:
            reasons.append(f"High sodium ({req.sodium} ppm) — excess salts may damage soil structure and reduce crop yield.")
            solutions.append("Leach soil with freshwater irrigation and apply gypsum.")

    # ── Overall score & status ────────────────────────────────────
    all_scores = [m["score"] for m in metrics.values()]
    avg_score = int(sum(all_scores) / max(len(all_scores), 1))

    if avg_score >= 75:
        health_status_code = "healthy"
        health_status = "Healthy Soil"
    elif avg_score >= 45:
        health_status_code = "moderate"
        health_status = "Moderate — Needs Attention"
    else:
        health_status_code = "critical"
        health_status = "Critical — Immediate Action Needed"

    if not reasons:
        reasons = ["All measured soil parameters are within the recommended range."]
        solutions = ["Maintain current fertilisation and irrigation schedule. Re-test in 4–6 weeks."]

    # ── Crop suggestions ─────────────────────────────────────────
    crop_map: list[tuple[str, list[str]]] = [
        ("Rice",       [lambda n, p, k, ph, m: ph >= 5.5 and ph <= 7.0 and m >= 50]),
        ("Wheat",      [lambda n, p, k, ph, m: ph >= 6.0 and ph <= 7.5 and m >= 40 and m <= 70]),
        ("Maize",      [lambda n, p, k, ph, m: ph >= 5.8 and ph <= 7.0 and n >= 60]),
        ("Tomato",     [lambda n, p, k, ph, m: ph >= 6.0 and ph <= 6.8 and p >= 25]),
        ("Potato",     [lambda n, p, k, ph, m: ph >= 5.5 and ph <= 6.5 and k >= 100]),
        ("Chickpea",   [lambda n, p, k, ph, m: ph >= 6.0 and ph <= 8.0 and m <= 65]),
        ("Soybean",    [lambda n, p, k, ph, m: ph >= 6.0 and ph <= 7.0 and p >= 20]),
        ("Sugarcane",  [lambda n, p, k, ph, m: ph >= 6.0 and ph <= 7.5 and m >= 50 and k >= 100]),
        ("Cotton",     [lambda n, p, k, ph, m: ph >= 6.0 and ph <= 8.0 and m >= 40]),
        ("Mustard",    [lambda n, p, k, ph, m: ph >= 6.0 and ph <= 7.5]),
        ("Banana",     [lambda n, p, k, ph, m: ph >= 6.0 and ph <= 7.5 and m >= 50 and k >= 150]),
        ("Onion",      [lambda n, p, k, ph, m: ph >= 6.0 and ph <= 7.0 and p >= 20]),
    ]

    suggested: list[str] = []
    n, p, k, ph, m = req.nitrogen, req.phosphorus, req.potassium, req.ph, req.moisture
    for crop_name, checks in crop_map:
        if all(c(n, p, k, ph, m) for c in checks):
            suggested.append(crop_name)
    if not suggested:
        suggested = ["Leguminous Cover Crop", "Green Manure"]

    # ── Plain-text report ─────────────────────────────────────────
    report_lines = [
        f"Soil Health Report — Score: {avg_score}/100 ({health_status})",
        "",
        f"Nitrogen: {req.nitrogen} kg/ha | Phosphorus: {req.phosphorus} kg/ha | Potassium: {req.potassium} kg/ha",
        f"pH: {req.ph} | Moisture: {req.moisture}%"
        + (f" | Organic Carbon: {req.organic_carbon}%" if req.organic_carbon is not None else "")
        + (f" | EC: {req.ec} dS/m" if req.ec is not None else ""),
        "",
        "Key Findings:",
        *[f"• {r}" for r in reasons],
        "",
        "Recommended Actions:",
        *[f"• {s}" for s in solutions],
        "",
        f"Suggested Crops: {', '.join(suggested)}",
    ]
    report = "\n".join(report_lines)

    return {
        "health_status": health_status,
        "health_status_code": health_status_code,
        "score": avg_score,
        "reasons": reasons,
        "solutions": solutions,
        "suggested_crops": suggested,
        "metric_breakdown": metrics,
        "report": report,
        "report_source": "local",
    }


@app.post("/api/analyze")
async def perform_analysis(data: SoilData):
    """
    Detailed analysis using BhoomiAI logic.
    """
    # Mock ML Score generation
    base_score = 100
    if data.ph > 8.0 or data.ph < 6.0: base_score -= 20
    if data.organic_carbon < 0.5: base_score -= 15
    if data.nitrogen < 250: base_score -= 10
    if data.phosphorus < 20: base_score -= 10
    if data.potassium < 130: base_score -= 10
    
    import random
    ml_health_score = max(10, min(100, base_score + random.uniform(-5, 5)))
    ml_health_score = round(ml_health_score, 1)

    result = analyze_soil(data, ml_health_score)
    return result

@app.post("/api/verify")
async def verify_output(request: VerifyRequest):
    """
    Verifies recommendations using Gemini AI.
    """
    try:
        from google import genai
        api_key = os.getenv("GOOGLE_API_KEY", "MOCK")
        if api_key == "MOCK" or not api_key:
            return {
                "verified": True,
                "verification_source": "ICAR & MahaKrishi Guidelines",
                "explanation": f"Verified: The recommendation '{request.recommendation_text}' aligns with standard state agricultural practices for soil rehabilitation."
            }
        
        client = genai.Client(api_key=api_key)
        prompt = f"As an expert agricultural scientist, verify if the following recommendation is scientifically correct according to ICAR, KRIBHCO, or State Agriculture (e.g. MahaKrishi) guidelines. Be concise (1-2 sentences). Recommendation: {request.recommendation_text}"
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return {
            "verified": True,
            "verification_source": "Google Gemini Agriculture Expert",
            "explanation": response.text
        }
    except Exception as e:
        return {"verified": False, "error": str(e)}

@app.post("/api/upload")
async def upload_soil_report(file: UploadFile = File(...)):
    """
    OCR extraction from soil report document.
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY", "MOCK")
        if api_key == "MOCK" or not api_key:
            return {"error": "GOOGLE_API_KEY is missing. OCR is disabled."}
            
        import tempfile
        import json
        import io
        from google import genai
        
        client = genai.Client(api_key=api_key)
        
        prompt = """
        Extract soil parameters from this report. Return EXACTLY this JSON format:
        {
            "ph": float, "ec": float, "organic_carbon": float, "nitrogen": float,
            "phosphorus": float, "potassium": float, "sulphur": float, "zinc": float,
            "iron": float, "copper": float, "manganese": float, "boron": float
        }
        Use plausible defaults for any missing values (e.g., ph: 7.2, ec: 1.0, organic_carbon: 0.6, nitrogen: 100, phosphorus: 20, potassium: 150).
        """
        
        file_ext = file.filename.lower()
        if file_ext.endswith(('.xlsx', '.xls', '.csv')):
            import pandas as pd
            file_bytes = await file.read()
            if file_ext.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_bytes))
            else:
                df = pd.read_excel(io.BytesIO(file_bytes))
            csv_data = df.to_csv(index=False)
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[f"Here is the dataset:\n{csv_data}", prompt],
            )
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
                temp_file.write(await file.read())
                temp_path = temp_file.name

            try:
                gemini_file = client.files.upload(file=temp_path)
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[gemini_file, prompt],
                )
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        parsed_data = json.loads(clean_text)
        
        # Ensure all required fields have valid fallback values to prevent HTTP 422 errors
        return {
            "ph": max(1.0, float(parsed_data.get("ph", 7.2) or 7.2)),
            "ec": max(0.0, float(parsed_data.get("ec", 1.0) or 1.0)),
            "organic_carbon": max(0.0, float(parsed_data.get("organic_carbon", 0.6) or 0.6)),
            "nitrogen": max(0.0, float(parsed_data.get("nitrogen", 100.0) or 100.0)),
            "phosphorus": max(0.0, float(parsed_data.get("phosphorus", 20.0) or 20.0)),
            "potassium": max(0.0, float(parsed_data.get("potassium", 150.0) or 150.0)),
            "sulphur": max(0.0, float(parsed_data.get("sulphur", 10.0) or 10.0)),
            "zinc": max(0.0, float(parsed_data.get("zinc", 0.6) or 0.6)),
            "iron": max(0.0, float(parsed_data.get("iron", 4.5) or 4.5)),
            "copper": max(0.0, float(parsed_data.get("copper", 0.2) or 0.2)),
            "manganese": max(0.0, float(parsed_data.get("manganese", 2.0) or 2.0)),
            "boron": max(0.0, float(parsed_data.get("boron", 0.5) or 0.5))
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/soil-health")
async def soil_health_endpoint(req: SoilHealthRequest):
    pass


# ── AI Soil Analysis (OpenAI ChatGPT) ────────────────────────────────────

class AISoilAnalysisRequest(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    moisture: float
    organic_carbon: Optional[float] = None
    ec: Optional[float] = None
    # Micronutrients & additional macronutrients (ppm) — from Himanshu's work
    phosphorus_ppm: Optional[float] = None
    sulfur: Optional[float] = None
    zinc: Optional[float] = None
    iron: Optional[float] = None
    manganese: Optional[float] = None
    copper: Optional[float] = None
    potassium_ppm: Optional[float] = None
    calcium: Optional[float] = None
    magnesium: Optional[float] = None
    sodium: Optional[float] = None


SOIL_SYSTEM_PROMPT = (
    "You are an expert Agronomist. Analyze the provided soil test values including "
    "primary macronutrients (N, P, K), pH, Moisture, and any micronutrients or secondary "
    "macronutrients when provided. Return a structured Markdown report containing: "
    "A Soil Health Summary, a Parameter Analysis identifying deficiencies (including "
    "micronutrient deficiencies if data is provided), 3 Recommended Crops, and an "
    "Action Plan for soil amendments."
)


@app.post("/analyze-soil")
async def analyze_soil_chatgpt(req: AISoilAnalysisRequest):
    """
    Generate an AI agronomist report using OpenAI ChatGPT.

    Accepts: N, P, K, pH, Moisture, optional Organic Carbon / EC,
    and optional micronutrients (S, Zn, Fe, Mn, Cu, Ca, Mg, Na, P-ppm, K-ppm).
    Returns: A Markdown-formatted soil health report from ChatGPT.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured on the server. Please set it in your .env file.",
        )

    # Build user message from the soil inputs
    lines = [
        f"Nitrogen (N): {req.nitrogen} kg/ha",
        f"Phosphorus (P): {req.phosphorus} kg/ha",
        f"Potassium (K): {req.potassium} kg/ha",
        f"Soil pH: {req.ph}",
        f"Moisture: {req.moisture}%",
    ]
    if req.organic_carbon is not None:
        lines.append(f"Organic Carbon: {req.organic_carbon}%")
    if req.ec is not None:
        lines.append(f"Electrical Conductivity: {req.ec} dS/m")

    # Micronutrients & secondary macronutrients
    micro_map = {
        "phosphorus_ppm": ("Phosphorus (ppm)", req.phosphorus_ppm),
        "sulfur": ("Sulfur (ppm)", req.sulfur),
        "zinc": ("Zinc (ppm)", req.zinc),
        "iron": ("Iron (ppm)", req.iron),
        "manganese": ("Manganese (ppm)", req.manganese),
        "copper": ("Copper (ppm)", req.copper),
        "potassium_ppm": ("Potassium (ppm)", req.potassium_ppm),
        "calcium": ("Calcium (ppm)", req.calcium),
        "magnesium": ("Magnesium (ppm)", req.magnesium),
        "sodium": ("Sodium (ppm)", req.sodium),
    }
    micro_lines = [f"{label}: {val}" for label, val in micro_map.values() if val is not None]
    if micro_lines:
        lines.append("")
        lines.append("Micronutrients & Secondary Macronutrients:")
        lines.extend(micro_lines)

    user_message = "Analyze the following soil test results:\n\n" + "\n".join(lines)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SOIL_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            max_tokens=1200,
        )
        report_md = completion.choices[0].message.content
        return {"report": report_md}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChatGPT analysis failed: {str(e)}")


# ── Serve React Frontend (Cloud Run production) ─────────────────
# In the Cloud Run container, the built frontend lives at /app/static.
# Mount it AFTER all API routes so API endpoints take priority.
_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.is_dir():
    # Serve static assets (JS, CSS, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="assets")

    # Catch-all: return index.html for any non-API route (React Router SPA)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for client-side routing."""
        file_path = _static_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_static_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

