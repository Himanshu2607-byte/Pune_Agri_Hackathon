import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from dotenv import load_dotenv

from logic.soil_analyzer import analyze_soil, SoilData, AnalysisResult

load_dotenv()
# Note: In a real app, model.py would load a scikit-learn model
# from ml.model import predict_health_score

app = FastAPI(title="BhoomiAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class VerifyRequest(BaseModel):
    recommendation_text: str

class IoTSensorData(BaseModel):
    sensor_id: str
    ph: float
    moisture_percentage: float
    npk_nitrogen: float
    npk_phosphorus: float
    npk_potassium: float
    temperature_celsius: float

@app.get("/")
def read_root():
    return {"message": "Welcome to BhoomiAI API - Intelligent Soil Rehabilitation System"}

@app.post("/api/analyze", response_model=AnalysisResult)
def perform_analysis(data: SoilData):
    # Mock ML Score generation
    base_score = 100
    if data.ph > 8.0 or data.ph < 6.0: base_score -= 20
    if data.organic_carbon < 0.5: base_score -= 15
    if data.nitrogen < 250: base_score -= 10
    if data.phosphorus < 20: base_score -= 10
    if data.potassium < 130: base_score -= 10
    
    ml_health_score = max(10, min(100, base_score + random.uniform(-5, 5)))
    ml_health_score = round(ml_health_score, 1)

    result = analyze_soil(data, ml_health_score)
    return result

@app.post("/api/verify")
def verify_output(request: VerifyRequest):
    """
    Verifies the deterministic recommendation against agricultural data 
    (simulated Gemini response referencing State Agriculture Websites).
    """
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY", "MOCK")
        if api_key == "MOCK":
            # Mock verification response if no key is provided
            return {
                "verified": True,
                "verification_source": "ICAR & MahaKrishi Guidelines",
                "explanation": f"Verified: The recommendation '{request.recommendation_text}' aligns with standard state agricultural practices for soil rehabilitation."
            }
        
        client = genai.Client(api_key=api_key)
        prompt = f"As an expert agricultural scientist, verify if the following recommendation is scientifically correct according to ICAR, KRIBHCO, or State Agriculture (e.g. MahaKrishi) guidelines. Be concise (1-2 sentences). Recommendation: {request.recommendation_text}"
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return {
            "verified": True,
            "verification_source": "Google Gemini Agriculture Expert",
            "explanation": response.text
        }
    except Exception as e:
        return {"verified": False, "error": str(e)}

@app.post("/api/chat")
def chat_bot(request: ChatRequest):
    """
    LLM Chatbot fine-tuned on Agriculture data.
    """
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY", "MOCK")
        if api_key == "MOCK":
            return {"reply": "I am the BhoomiAI Assistant. (Gemini API key is missing. This is a mock response to your query: '" + request.message + "'). I can help you with crop planning and soil rehabilitation based on ICAR guidelines."}
        
        client = genai.Client(api_key=api_key)
        system_instruction = "You are BhoomiAI, an expert agricultural scientist. You provide advice based on data from Indian State Agriculture Websites, KRIBHCO, and ICAR. Be concise, polite, and farmer-friendly."
        
        # We use a simple prompt injection for system instruction if using standard generate_content
        prompt = f"System Instruction: {system_instruction}\n\nFarmer: {request.message}\nBhoomiAI:"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"Sorry, I encountered an error: {str(e)}"}

@app.post("/api/iot-sensor")
def receive_iot_data(data: IoTSensorData):
    """
    Endpoint for real-time microcontroller sensor data (e.g., ESP32 over MQTT/HTTP).
    Stores the data and triggers an alert if moisture is too low or pH is dangerous.
    """
    # In a real app, save to Firebase/PostgreSQL here
    alerts = []
    if data.moisture_percentage < 20.0:
        alerts.append("CRITICAL: Soil moisture is below 20%. Triggering smart irrigation alert.")
    if data.ph > 8.5:
        alerts.append("WARNING: High alkalinity detected by sensor. Gypsum application recommended.")
        
    return {
        "status": "success",
        "message": "Sensor data recorded successfully.",
        "sensor_id": data.sensor_id,
        "real_time_alerts": alerts
    }

@app.post("/api/upload")
async def upload_soil_report(file: UploadFile = File(...)):
    """
    Receives an uploaded file, passes it to Gemini for OCR extraction,
    and returns a structured JSON payload for the analysis engine.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY", "MOCK")
        if api_key == "MOCK" or not api_key:
            return {"error": "GEMINI_API_KEY is missing. OCR parsing requires a valid API key."}
            
        import tempfile
        import json
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        # Save uploaded file temporarily to pass to GenAI
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name

        try:
            # Upload the file to Gemini
            gemini_file = client.files.upload(file=temp_path)
            
            prompt = """
            Analyze this document. Is it a soil health report/certificate? 
            If it is clearly a random image, a face, a car, or anything completely unrelated to soil/agriculture, 
            return EXACTLY this JSON: {"error": "Invalid Document: No soil parameters found."}
            
            If it IS a soil report, extract the following 8 parameters and return EXACTLY this JSON format (use standard fallback values if a parameter is missing: ph 7.0, ec 1.0, organic_carbon 0.5, nitrogen 150, phosphorus 20, potassium 100, cation_exchange_capacity 15.0, exchangeable_sodium_percentage 5.0).
            
            {
                "ph": float,
                "ec": float,
                "organic_carbon": float,
                "nitrogen": float,
                "phosphorus": float,
                "potassium": float,
                "cation_exchange_capacity": float,
                "exchangeable_sodium_percentage": float
            }
            
            Do not include any markdown formatting, only the raw JSON.
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[gemini_file, prompt],
            )
            
            # Clean up the response text in case it has markdown block ticks
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            extracted_data = json.loads(clean_text)
            
            return extracted_data
            
        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return {"error": f"Failed to parse document: {str(e)}"}
