"""AI-assisted chat service with OpenAI/Google/Groq support and graceful local fallback."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv

    current_dir = Path(__file__).resolve().parent
    load_dotenv(current_dir.parent / ".env")
    load_dotenv(current_dir / ".env")
except Exception:
    pass


OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _is_summary_request(message: str) -> bool:
    message_lower = message.lower()
    summary_markers = ["summar", "summary", "overview", "project summary", "summarise", "summarize", "सार", "सारांश"]
    return any(marker in message_lower for marker in summary_markers)


def _build_feature_context_text(feature_context: dict[str, Any] | None) -> str:
    """Convert feature_context dict into readable text for the system prompt."""
    if not feature_context:
        return ""

    sections = []

    # Soil analysis (ChatGPT)
    sa = feature_context.get("soil_analysis")
    if sa:
        inputs = sa.get("inputs", {})
        lines = []
        if inputs:
            for key, val in inputs.items():
                if val is not None:
                    lines.append(f"  {key}: {val}")
        snippet = sa.get("ai_report_summary", "")
        sections.append(
            f"[AI Soil Analysis — via {sa.get('report_source', 'ChatGPT')}]\n"
            + ("\n".join(lines) if lines else "")
            + (f"\nReport excerpt: {snippet}" if snippet else "")
        )

    # Soil health (heuristic)
    sh = feature_context.get("soil_health")
    if sh:
        sections.append(
            f"[Soil Health — heuristic]\n"
            f"  Status: {sh.get('health_status', 'N/A')}, Score: {sh.get('score', 'N/A')}/100\n"
            f"  Reasons: {'; '.join(sh.get('reasons', []))}\n"
            f"  Solutions: {'; '.join(sh.get('solutions', []))}\n"
            f"  Suggested crops: {', '.join(sh.get('suggested_crops', []))}"
        )

    # Crop analysis
    ca = feature_context.get("analyze")
    if ca:
        sections.append(
            f"[Crop Disease Analysis]\n"
            f"  Disease: {ca.get('disease', 'N/A')}\n"
            f"  Confidence: {ca.get('confidence', 'N/A')}\n"
            f"  Recommendations: {ca.get('recommendations', 'N/A')}"
        )

    # Weather
    wc = feature_context.get("weather")
    if wc:
        sections.append(
            f"[Current Weather]\n"
            f"  Condition: {wc.get('condition')}, Temp: {wc.get('temperature_c')}°C\n"
            f"  Humidity: {wc.get('humidity')}%, Rain chance: {wc.get('precipitation_probability')}%\n"
            f"  Disease risk: {wc.get('disease_risk', 'N/A')}"
        )

    if not sections:
        return ""

    return "\n\n--- USER'S CURRENT FARM DATA ---\n" + "\n\n".join(sections) + "\n--- END FARM DATA ---"


def _build_system_prompt(lang: str, weather: dict[str, Any] | None, feature_context: dict[str, Any] | None = None) -> str:
    weather_text = ""
    if weather:
        weather_text = (
            f"\n\nCurrent weather: {weather.get('condition')}, temperature {weather.get('temperature_c')}°C, "
            f"humidity {weather.get('humidity')}%, wind {weather.get('wind_kph')} km/h, rain chance "
            f"{weather.get('precipitation_probability')}%. Field advice: {weather.get('advice')}"
        )

    farm_data = _build_feature_context_text(feature_context)

    # Language configuration — expandable to any language
    LANG_CONFIG = {
        "en": {"name": "English", "respond_instruction": ""},
        "hi": {"name": "Hindi (हिन्दी)", "respond_instruction": "\n\n⚠️ IMPORTANT: You MUST respond entirely in Hindi (हिन्दी) using Devanagari script. Do NOT respond in English."},
        "mr": {"name": "Marathi (मराठी)", "respond_instruction": "\n\n⚠️ IMPORTANT: You MUST respond entirely in Marathi (मराठी) using Devanagari script. Do NOT respond in English or Hindi."},
        "ta": {"name": "Tamil (தமிழ்)", "respond_instruction": "\n\n⚠️ IMPORTANT: You MUST respond entirely in Tamil (தமிழ்) using Tamil script. Do NOT respond in English."},
        "te": {"name": "Telugu (తెలుగు)", "respond_instruction": "\n\n⚠️ IMPORTANT: You MUST respond entirely in Telugu (తెలుగు) using Telugu script. Do NOT respond in English."},
        "kn": {"name": "Kannada (ಕನ್ನಡ)", "respond_instruction": "\n\n⚠️ IMPORTANT: You MUST respond entirely in Kannada (ಕನ್ನಡ) using Kannada script. Do NOT respond in English."},
        "pa": {"name": "Punjabi (ਪੰਜਾਬੀ)", "respond_instruction": "\n\n⚠️ IMPORTANT: You MUST respond entirely in Punjabi (ਪੰਜਾਬੀ) using Gurmukhi script. Do NOT respond in English."},
        "gu": {"name": "Gujarati (ગુજરાતી)", "respond_instruction": "\n\n⚠️ IMPORTANT: You MUST respond entirely in Gujarati (ગુજરાતી) using Gujarati script. Do NOT respond in English."},
        "bn": {"name": "Bengali (বাংলা)", "respond_instruction": "\n\n⚠️ IMPORTANT: You MUST respond entirely in Bengali (বাংলা) using Bengali script. Do NOT respond in English."},
    }

    lang_info = LANG_CONFIG.get(lang, {"name": lang, "respond_instruction": f"\n\n⚠️ IMPORTANT: Respond in the language with code '{lang}'. Do NOT respond in English unless the user writes in English."})
    respond_instruction = lang_info["respond_instruction"]

    base_prompt = (
        "You are AgroVision's expert agricultural advisor — an AI-powered crop monitoring platform.\n\n"
        "Your role:\n"
        "• Answer agriculture-related questions with detailed, practical, and accurate advice\n"
        "• Cover crop diseases, pest control, soil health, fertilizers, irrigation, market advice, weather, seeds, organic farming, and more\n"
        "• When the user's farm data is available below, reference it to give personalized recommendations\n"
        "• Use emoji, bullet points, numbered steps, and clear formatting for readability\n"
        "• Only refuse truly non-agricultural topics (e.g. politics, entertainment)\n\n"
        "ACCURACY RULES (CRITICAL — follow strictly):\n"
        "• NEVER fabricate data, statistics, percentages, or research citations\n"
        "• NEVER invent product names, brand names, or chemical formulations you are not sure about\n"
        "• If you are unsure about something, say 'I'm not certain about this — please verify with a local agronomist'\n"
        "• Base your advice ONLY on well-established agricultural science and common farming practices\n"
        "• When referencing the user's farm data below, quote the ACTUAL values — do not round or alter them\n"
        "• Do NOT make up soil test results, weather data, or crop yields — only reference what is provided\n"
        "• Keep advice general and safe — recommend consulting local extension services for specific chemical dosages\n\n"
        "AgroVision features: AI crop disease detection, soil analysis (ChatGPT + heuristic scoring), "
        "weather panel, farm zone map, profit estimator, field journal, and multilingual assistant."
        + respond_instruction + weather_text + farm_data
    )

    return base_prompt


def _fallback_with_context(chatbot, message: str, lang: str, weather: dict[str, Any] | None) -> tuple[str, str]:
    if _is_summary_request(message):
        response = chatbot.get_project_summary(lang)
    else:
        response = chatbot.get_response(message, lang)

    if weather:
        if lang == "hi":
            response += (
                f"\n\nमौसम संकेत: अभी {weather.get('condition').lower()} है, तापमान {weather.get('temperature_c')}°C "
                f"और बारिश की संभावना {weather.get('precipitation_probability')}% है। {weather.get('advice')}"
            )
        else:
            response += (
                f"\n\nWeather note: It is currently {weather.get('condition').lower()} with {weather.get('temperature_c')}°C "
                f"and a {weather.get('precipitation_probability')}% rain chance. {weather.get('advice')}"
            )
    return response, "local"


def _extract_google_text(body: dict[str, Any]) -> str:
    candidates = body.get("candidates", [])
    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts", [])
    text_chunks = [part.get("text", "").strip() for part in parts if part.get("text")]
    return "\n".join(chunk for chunk in text_chunks if chunk).strip()


def _request_openai_response(message: str, lang: str, weather: dict[str, Any] | None, feature_context: dict[str, Any] | None = None) -> str:
    """Use OpenAI GPT-4o-mini for high-quality responses."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    api_url = os.getenv("OPENAI_CHAT_URL", OPENAI_API_URL)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _build_system_prompt(lang, weather, feature_context)},
            {"role": "user", "content": message},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }

    request = Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=25) as response:
        body = json.loads(response.read().decode("utf-8"))

    return body.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


def _request_google_response(message: str, lang: str, weather: dict[str, Any] | None, feature_context: dict[str, Any] | None = None) -> str:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY")
    if not api_key:
        return ""

    model = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
    api_url = os.getenv("GOOGLE_API_URL", GOOGLE_API_URL).rstrip("/")
    request_url = f"{api_url}/{model}:generateContent?key={api_key}"

    payload = {
        "system_instruction": {"parts": [{"text": _build_system_prompt(lang, weather, feature_context)}]},
        "contents": [{"role": "user", "parts": [{"text": message}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 800,
        },
    }

    request = Request(
        request_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=25) as response:
        body = json.loads(response.read().decode("utf-8"))

    return _extract_google_text(body)


def _request_groq_response(message: str, lang: str, weather: dict[str, Any] | None, feature_context: dict[str, Any] | None = None) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ""

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    api_url = os.getenv("GROQ_API_URL", GROQ_API_URL)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _build_system_prompt(lang, weather, feature_context)},
            {"role": "user", "content": message},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }

    request = Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=25) as response:
        body = json.loads(response.read().decode("utf-8"))

    return body.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


def get_ai_chat_response(
    chatbot,
    message: str,
    lang: str = "en",
    weather: dict[str, Any] | None = None,
    feature_context: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Try AI providers in order: OpenAI → Google → Groq → local fallback."""

    is_summary = _is_summary_request(message)

    if is_summary:
        message = (
            "Give a concise summary of the AgroVision project with features, architecture, and how farmers use it. "
            "If user farm data is available, also summarize their latest results."
            if lang == "en"
            else "AgroVision प्रोजेक्ट का संक्षिप्त सार दें: फीचर्स, आर्किटेक्चर और किसान उपयोग। यदि उपयोगकर्ता का फार्म डेटा उपलब्ध है, तो उसका भी सारांश दें।"
        )

    # 1. Try OpenAI (GPT-4o-mini) — best quality, user already has a key
    try:
        content = _request_openai_response(message, lang, weather, feature_context)
        if content:
            return content, "ai"
    except Exception:
        pass

    # 2. Try Google Gemini
    try:
        content = _request_google_response(message, lang, weather, feature_context)
        if content:
            return content, "ai"
    except Exception:
        pass

    # 3. Try Groq
    try:
        content = _request_groq_response(message, lang, weather, feature_context)
        if content:
            return content, "ai"
    except Exception:
        pass

    # 4. Local rule-based fallback
    return _fallback_with_context(chatbot, message, lang, weather)
