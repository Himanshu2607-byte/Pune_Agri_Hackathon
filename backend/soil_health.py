"""Soil health analysis helpers with optional AI-generated report text."""

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


GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

METRIC_CONFIG: dict[str, dict[str, Any]] = {
    "nitrogen": {
        "ideal": (40.0, 120.0),
        "tolerance": 90.0,
        "weight": 0.18,
        "label": {"en": "Nitrogen (N)", "hi": "नाइट्रोजन (N)"},
        "unit": "kg/ha",
    },
    "phosphorus": {
        "ideal": (20.0, 60.0),
        "tolerance": 45.0,
        "weight": 0.14,
        "label": {"en": "Phosphorus (P)", "hi": "फॉस्फोरस (P)"},
        "unit": "kg/ha",
    },
    "potassium": {
        "ideal": (120.0, 280.0),
        "tolerance": 130.0,
        "weight": 0.18,
        "label": {"en": "Potassium (K)", "hi": "पोटाशियम (K)"},
        "unit": "kg/ha",
    },
    "ph": {
        "ideal": (6.0, 7.5),
        "tolerance": 1.8,
        "weight": 0.28,
        "label": {"en": "Soil pH", "hi": "मिट्टी pH"},
        "unit": "",
    },
    "moisture": {
        "ideal": (35.0, 65.0),
        "tolerance": 32.0,
        "weight": 0.22,
        "label": {"en": "Moisture", "hi": "नमी"},
        "unit": "%",
    },
    "organic_carbon": {
        "ideal": (0.5, 1.5),
        "tolerance": 1.0,
        "weight": 0.10,
        "label": {"en": "Organic Carbon", "hi": "जैविक कार्बन"},
        "unit": "%",
    },
    "ec": {
        "ideal": (0.2, 1.5),
        "tolerance": 1.4,
        "weight": 0.10,
        "label": {"en": "Electrical Conductivity", "hi": "विद्युत चालकता"},
        "unit": "dS/m",
    },
    "phosphorus_ppm": {
        "ideal": (25.0, 35.0),
        "tolerance": 10.0,
        "weight": 0.06,
        "label": {"en": "Phosphorus (P) - ppm", "hi": "फॉस्फोरस (P) - ppm"},
        "unit": "ppm",
    },
    "sulfur": {
        "ideal": (7.0, 15.0),
        "tolerance": 8.0,
        "weight": 0.04,
        "label": {"en": "Sulfur (S)", "hi": "सल्फर (S)"},
        "unit": "ppm",
    },
    "zinc": {
        "ideal": (1.0, 3.0),
        "tolerance": 2.0,
        "weight": 0.05,
        "label": {"en": "Zinc (Zn)", "hi": "जिंक (Zn)"},
        "unit": "ppm",
    },
    "iron": {
        "ideal": (10.0, 20.0),
        "tolerance": 10.0,
        "weight": 0.05,
        "label": {"en": "Iron (Fe)", "hi": "लोहा (Fe)"},
        "unit": "ppm",
    },
    "manganese": {
        "ideal": (8.0, 11.0),
        "tolerance": 3.0,
        "weight": 0.04,
        "label": {"en": "Manganese (Mn)", "hi": "मैंगनीज (Mn)"},
        "unit": "ppm",
    },
    "copper": {
        "ideal": (0.8, 1.0),
        "tolerance": 0.2,
        "weight": 0.04,
        "label": {"en": "Copper (Cu)", "hi": "तांबा (Cu)"},
        "unit": "ppm",
    },
    "potassium_ppm": {
        "ideal": (165.0, 220.0),
        "tolerance": 55.0,
        "weight": 0.06,
        "label": {"en": "Potassium (K) - ppm", "hi": "पोटाशियम (K) - ppm"},
        "unit": "ppm",
    },
    "calcium": {
        "ideal": (1400.0, 999999.0),
        "tolerance": 500.0,
        "weight": 0.06,
        "label": {"en": "Calcium (Ca)", "hi": "कैल्शियम (Ca)"},
        "unit": "ppm",
    },
    "magnesium": {
        "ideal": (100.0, 999999.0),
        "tolerance": 200.0,
        "weight": 0.05,
        "label": {"en": "Magnesium (Mg)", "hi": "मैग्नीशियम (Mg)"},
        "unit": "ppm",
    },
    "sodium": {
        "ideal": (80.0, 120.0),
        "tolerance": 40.0,
        "weight": 0.04,
        "label": {"en": "Sodium (Na)", "hi": "सोडियम (Na)"},
        "unit": "ppm",
    },
}

HI_TO_MR_REPLACEMENTS = [
    ("मिट्टी", "माती"),
    ("नाइट्रोजन", "नायट्रोजन"),
    ("फॉस्फोरस", "फॉस्फरस"),
    ("पोटाशियम", "पोटॅशियम"),
    ("नमी", "आर्द्रता"),
    ("जैविक", "जैविक"),
    ("विद्युत चालकता", "विद्युत वहनक्षमता"),
    ("स्वस्थ", "निरोगी"),
    ("मध्यम", "मध्यम"),
    ("गंभीर", "गंभीर"),
    ("उत्तम", "उत्तम"),
    ("कम", "कमी"),
    ("अधिक", "जास्त"),
    ("फसल", "पीक"),
    ("पोषक", "पोषण"),
    ("खाद", "खत"),
    ("सिंचाई", "सिंचन"),
    ("सुझाई गई", "सुचवलेली"),
    ("सुझाव", "सल्ला"),
    ("कारण", "कारणे"),
    ("आदर्श", "आदर्श"),
    ("सल्फर", "गंधक"),
    ("जिंक", "जिंक"),
    ("लोहा", "लोह"),
    ("मैंगनीज", "मँगनीज"),
    ("तांबा", "तांबे"),
    ("कैल्शियम", "कॅल्शियम"),
    ("मैग्नीशियम", "मॅग्नेशियम"),
    ("सोडियम", "सोडियम"),
]


def _to_marathi_text(input_text: str) -> str:
    output = input_text
    for source, target in HI_TO_MR_REPLACEMENTS:
        output = output.replace(source, target)
    return output


def _pick_localized_text(texts: dict[str, str], lang: str) -> str:
    if lang == "hi":
        return texts["hi"]
    if lang == "mr":
        return _to_marathi_text(texts["hi"])
    return texts["en"]


def _metric_label(metric: str, lang: str) -> str:
    return _pick_localized_text(METRIC_CONFIG[metric]["label"], lang)


def _status_label(status_code: str, lang: str) -> str:
    labels = {
        "healthy": {"en": "Healthy", "hi": "स्वस्थ"},
        "moderate": {"en": "Moderate", "hi": "मध्यम"},
        "critical": {"en": "Critical", "hi": "गंभीर"},
        "optimal": {"en": "Optimal", "hi": "उत्तम"},
        "low": {"en": "Low", "hi": "कम"},
        "high": {"en": "High", "hi": "अधिक"},
    }
    return _pick_localized_text(labels[status_code], lang)


def _metric_score(value: float, low: float, high: float, tolerance: float) -> tuple[int, str]:
    if low <= value <= high:
        return 100, "optimal"

    if value < low:
        distance = low - value
        score = max(0, int(round(100 - (distance / max(tolerance, 1e-6)) * 100)))
        return score, "low"

    distance = value - high
    score = max(0, int(round(100 - (distance / max(tolerance, 1e-6)) * 100)))
    return score, "high"


def _metric_note(metric: str, state: str, value: float, lang: str) -> str:
    low, high = METRIC_CONFIG[metric]["ideal"]
    label = _metric_label(metric, lang)

    if state == "optimal":
        if lang in {"hi", "mr"}:
            text = f"{label} संतुलित सीमा ({low:g}-{high:g}) में है।"
            return _to_marathi_text(text) if lang == "mr" else text
        return f"{label} is within the balanced range ({low:g}-{high:g})."

    if state == "low":
        if lang in {"hi", "mr"}:
            text = f"{label} आदर्श सीमा से कम है ({value:g})."
            return _to_marathi_text(text) if lang == "mr" else text
        return f"{label} is below the ideal range ({value:g})."

    if lang in {"hi", "mr"}:
        text = f"{label} आदर्श सीमा से अधिक है ({value:g})."
        return _to_marathi_text(text) if lang == "mr" else text
    return f"{label} is above the ideal range ({value:g})."


def _build_reason_solution(metric: str, state: str, lang: str) -> tuple[str, str]:
    en = {
        "nitrogen_low": (
            "Nitrogen is low, which can reduce vegetative growth and leaf development.",
            "Apply split nitrogen doses (urea/organic manure) and include legume rotation to rebuild N.",
        ),
        "nitrogen_high": (
            "Nitrogen is high, which can cause soft growth and disease susceptibility.",
            "Reduce nitrogen fertilizer for the next cycle and balance with potash and organic matter.",
        ),
        "phosphorus_low": (
            "Phosphorus is low, limiting root growth and early crop establishment.",
            "Use SSP/DAP in basal dose and consider phosphate-solubilizing biofertilizer.",
        ),
        "phosphorus_high": (
            "Phosphorus is high, which may lock micronutrients like zinc.",
            "Avoid additional phosphatic fertilizer and monitor Zn/Fe in the next soil test.",
        ),
        "potassium_low": (
            "Potassium is low, reducing stress tolerance and grain/fruit quality.",
            "Apply MOP/potash and recycle crop residues to restore available K.",
        ),
        "potassium_high": (
            "Potassium is high and may create nutrient imbalance with Ca/Mg.",
            "Skip potash inputs temporarily and rebalance nutrition with calcium-magnesium sources.",
        ),
        "ph_low": (
            "Soil pH is acidic, which can reduce nutrient availability for many crops.",
            "Apply agricultural lime or dolomite in planned doses and retest soil after correction.",
        ),
        "ph_high": (
            "Soil pH is alkaline, which can limit phosphorus and micronutrient uptake.",
            "Use gypsum/sulfur-based amendments and increase compost to gradually improve pH.",
        ),
        "moisture_low": (
            "Soil moisture is low, increasing crop stress and reducing nutrient movement.",
            "Increase irrigation frequency, use mulch, and improve moisture retention with organic matter.",
        ),
        "moisture_high": (
            "Soil moisture is high, increasing root disease and aeration risk.",
            "Improve field drainage, avoid over-irrigation, and use raised beds in wet patches.",
        ),
        "organic_carbon_low": (
            "Organic carbon is low, reducing soil structure and nutrient buffering.",
            "Add compost/FYM, keep residues, and use cover crops to build organic carbon.",
        ),
        "organic_carbon_high": (
            "Organic carbon is above typical range and may need nutrient balancing.",
            "Keep balanced fertilization and monitor nitrogen availability in the next cycle.",
        ),
        "ec_low": (
            "Electrical conductivity is very low, indicating low dissolved nutrient salts.",
            "Follow balanced fertilization and monitor nutrient response in crop growth.",
        ),
        "ec_high": (
            "Electrical conductivity is high, indicating salinity risk.",
            "Leach salts with good-quality water, improve drainage, and avoid saline irrigation sources.",
        ),
    }

    hi = {
        "nitrogen_low": (
            "नाइट्रोजन कम है, जिससे पत्तियों और पौधों की बढ़वार धीमी हो सकती है।",
            "नाइट्रोजन उर्वरक को विभाजित खुराक में दें और दलहनी फसल चक्र अपनाएं।",
        ),
        "nitrogen_high": (
            "नाइट्रोजन अधिक है, जिससे नरम बढ़वार और रोग का खतरा बढ़ सकता है।",
            "अगले चक्र में नाइट्रोजन कम करें और पोटाश व जैविक पदार्थ संतुलित दें।",
        ),
        "phosphorus_low": (
            "फॉस्फोरस कम है, जिससे जड़ विकास और शुरुआती स्थापना प्रभावित होती है।",
            "SSP/DAP को बेसल डोज में दें और फॉस्फेट घुलनशील जैव उर्वरक उपयोग करें।",
        ),
        "phosphorus_high": (
            "फॉस्फोरस अधिक है, जिससे जिंक जैसे सूक्ष्म पोषक तत्वों का अवशोषण घट सकता है।",
            "फॉस्फेट उर्वरक रोकें और अगली जांच में Zn/Fe स्तर की निगरानी करें।",
        ),
        "potassium_low": (
            "पोटाश कम है, जिससे तनाव सहनशीलता और उपज गुणवत्ता घट सकती है।",
            "MOP/पोटाश दें और फसल अवशेष वापस मिट्टी में मिलाएं।",
        ),
        "potassium_high": (
            "पोटाश अधिक है, जिससे कैल्शियम/मैग्नीशियम असंतुलन हो सकता है।",
            "कुछ समय पोटाश रोकें और कैल्शियम-मैग्नीशियम संतुलन पर ध्यान दें।",
        ),
        "ph_low": (
            "मिट्टी का pH अम्लीय है, जिससे पोषक तत्व उपलब्धता घट सकती है।",
            "कृषि चूना या डोलोमाइट योजना अनुसार दें और सुधार के बाद पुनः परीक्षण करें।",
        ),
        "ph_high": (
            "मिट्टी का pH क्षारीय है, जिससे फॉस्फोरस और सूक्ष्म पोषक तत्वों का अवशोषण घट सकता है।",
            "जिप्सम/सल्फर आधारित सुधारक और जैविक खाद का उपयोग बढ़ाएं।",
        ),
        "moisture_low": (
            "मिट्टी की नमी कम है, जिससे फसल तनाव और पोषक तत्व गमन घटता है।",
            "सिंचाई आवृत्ति बढ़ाएं, मल्चिंग करें और जैविक पदार्थ से नमी धारण क्षमता बढ़ाएं।",
        ),
        "moisture_high": (
            "मिट्टी की नमी अधिक है, जिससे जड़ रोग और वायु संचार समस्या बढ़ती है।",
            "ड्रेनेज सुधारें, अधिक सिंचाई रोकें और गीले हिस्सों में उभरी क्यारियां बनाएं।",
        ),
        "organic_carbon_low": (
            "जैविक कार्बन कम है, जिससे मिट्टी संरचना और पोषक बफर क्षमता कमजोर होती है।",
            "कम्पोस्ट/FYM दें, अवशेष रखें और कवर क्रॉप अपनाएं।",
        ),
        "organic_carbon_high": (
            "जैविक कार्बन सामान्य से अधिक है, इसलिए पोषण संतुलन की निगरानी जरूरी है।",
            "संतुलित उर्वरक प्रबंधन रखें और अगले चक्र में नाइट्रोजन उपलब्धता जांचें।",
        ),
        "ec_low": (
            "विद्युत चालकता बहुत कम है, जो घुलनशील पोषक लवण कम होने का संकेत है।",
            "संतुलित उर्वरक प्रबंधन रखें और फसल प्रतिक्रिया पर निगरानी करें।",
        ),
        "ec_high": (
            "विद्युत चालकता अधिक है, जो लवणता जोखिम दिखाती है।",
            "अच्छे पानी से लवण धुलाई करें, ड्रेनेज सुधारें और खारे पानी से सिंचाई न करें।",
        ),
    }

    key = f"{metric}_{state}"
    if lang == "hi":
        return hi[key]
    if lang == "mr":
        reason, solution = hi[key]
        return _to_marathi_text(reason), _to_marathi_text(solution)
    return en[key]


def _crop_suggestions(values: dict[str, float], status_code: str, lang: str) -> list[str]:
    crops: list[str] = []

    ph_val = values["ph"]
    moisture = values["moisture"]
    nitrogen = values["nitrogen"]
    ec_val = values.get("ec")

    if ph_val < 6.0:
        crops.extend(["Potato", "Rice", "Tea"])
    elif ph_val > 7.8:
        crops.extend(["Barley", "Mustard", "Cotton"])

    if moisture < 30:
        crops.extend(["Millet", "Chickpea", "Groundnut"])
    elif moisture > 70:
        crops.extend(["Rice", "Jute", "Taro"])

    if nitrogen < 40:
        crops.extend(["Soybean", "Cowpea", "Green Gram"])

    if ec_val is not None and ec_val > 2.5:
        crops.extend(["Barley", "Cotton", "Sorghum"])

    if status_code == "healthy":
        crops.extend(["Wheat", "Maize", "Tomato", "Soybean"])

    if not crops:
        crops = ["Wheat", "Maize", "Mustard", "Chickpea"]

    unique = list(dict.fromkeys(crops))[:6]
    if lang == "en":
        return unique

    mapping = {
        "Potato": "आलू",
        "Rice": "धान",
        "Tea": "चाय",
        "Barley": "जौ",
        "Mustard": "सरसों",
        "Cotton": "कपास",
        "Millet": "बाजरा",
        "Chickpea": "चना",
        "Groundnut": "मूंगफली",
        "Jute": "जूट",
        "Taro": "अरबी",
        "Soybean": "सोयाबीन",
        "Cowpea": "लोबिया",
        "Green Gram": "मूंग",
        "Sorghum": "ज्वार",
        "Wheat": "गेहूं",
        "Maize": "मक्का",
        "Tomato": "टमाटर",
    }
    localized = [mapping.get(crop, crop) for crop in unique]
    if lang == "hi":
        return localized
    return [_to_marathi_text(crop) for crop in localized]


def _extract_google_text(body: dict[str, Any]) -> str:
    candidates = body.get("candidates", [])
    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts", [])
    chunks = [part.get("text", "").strip() for part in parts if part.get("text")]
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def _generate_ai_report(
    lang: str,
    score: int,
    health_status: str,
    reasons: list[str],
    solutions: list[str],
    crops: list[str],
    metric_breakdown: dict[str, Any],
) -> str | None:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY")
    if not api_key:
        return None

    model = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
    api_url = os.getenv("GOOGLE_API_URL", GOOGLE_API_URL).rstrip("/")
    request_url = f"{api_url}/{model}:generateContent?key={api_key}"

    if lang == "hi":
        user_prompt = (
            "नीचे दिए गए मिट्टी विश्लेषण के आधार पर किसान के लिए संक्षिप्त रिपोर्ट बनाओ। "
            "रिपोर्ट में 4 हिस्से हों: 1) समग्र स्थिति 2) मुख्य जोखिम 3) सुधार कार्ययोजना (3-5 पॉइंट) "
            "4) सुझाई गई फसलें। रिपोर्ट व्यावहारिक और स्पष्ट हो।\n\n"
            f"डेटा: {json.dumps({'score': score, 'status': health_status, 'reasons': reasons, 'solutions': solutions, 'crops': crops, 'metrics': metric_breakdown}, ensure_ascii=False)}"
        )
        system_text = "आप एक कृषि मृदा विशेषज्ञ हैं। जवाब किसान-हितैषी हिंदी में दें।"
    elif lang == "mr":
        user_prompt = (
            "खाली दिलेल्या माती विश्लेषणावर आधारित शेतकऱ्यासाठी संक्षिप्त अहवाल तयार करा. "
            "अहवालात 4 विभाग असू द्या: 1) एकूण स्थिती 2) मुख्य जोखीम 3) सुधारणा कृती योजना (3-5 मुद्दे) "
            "4) सुचवलेली पिके. अहवाल व्यावहारिक आणि स्पष्ट ठेवा.\n\n"
            f"डेटा: {json.dumps({'score': score, 'status': health_status, 'reasons': reasons, 'solutions': solutions, 'crops': crops, 'metrics': metric_breakdown}, ensure_ascii=False)}"
        )
        system_text = "तुम्ही कृषी मृदा तज्ञ आहात. उत्तर शेतकरी-केंद्रित आणि सोप्या मराठीत द्या."
    else:
        user_prompt = (
            "Create a concise farmer-friendly soil health report from this analysis. "
            "Include 4 sections: 1) overall status 2) key risks 3) improvement action plan (3-5 points) "
            "4) suitable crops. Keep it practical and specific.\n\n"
            f"Data: {json.dumps({'score': score, 'status': health_status, 'reasons': reasons, 'solutions': solutions, 'crops': crops, 'metrics': metric_breakdown}, ensure_ascii=False)}"
        )
        system_text = "You are an agronomy soil expert. Provide practical farmer-focused guidance."

    payload = {
        "system_instruction": {"parts": [{"text": system_text}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": 360,
        },
    }

    request = Request(
        request_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=18) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = _extract_google_text(body)
        return content or None
    except Exception:
        return None


def _local_report(lang: str, score: int, health_status: str, reasons: list[str], solutions: list[str], crops: list[str]) -> str:
    if lang in {"hi", "mr"}:
        reason_lines = "\n".join(f"- {line}" for line in reasons[:4])
        solution_lines = "\n".join(f"- {line}" for line in solutions[:5])
        crop_line = ", ".join(crops)
        text = (
            f"समग्र मिट्टी स्वास्थ्य स्कोर {score}/100 है और स्थिति {health_status} है।\n\n"
            "मुख्य कारण:\n"
            f"{reason_lines}\n\n"
            "सुधार योजना:\n"
            f"{solution_lines}\n\n"
            f"सुझाई गई फसलें: {crop_line}"
        )
        return _to_marathi_text(text) if lang == "mr" else text

    reason_lines = "\n".join(f"- {line}" for line in reasons[:4])
    solution_lines = "\n".join(f"- {line}" for line in solutions[:5])
    crop_line = ", ".join(crops)
    return (
        f"Overall soil health score is {score}/100 with status: {health_status}.\n\n"
        "Key reasons:\n"
        f"{reason_lines}\n\n"
        "Improvement plan:\n"
        f"{solution_lines}\n\n"
        f"Suggested crops: {crop_line}"
    )


def _validate_values(values: dict[str, float]) -> None:
    if not (0 <= values["ph"] <= 14):
        raise ValueError("pH must be between 0 and 14.")
    if not (0 <= values["moisture"] <= 100):
        raise ValueError("Moisture must be between 0 and 100.")

    for key in ("nitrogen", "phosphorus", "potassium"):
        if values[key] < 0:
            raise ValueError(f"{key.title()} cannot be negative.")

    if "organic_carbon" in values and values["organic_carbon"] < 0:
        raise ValueError("Organic carbon cannot be negative.")
    if "ec" in values and values["ec"] < 0:
        raise ValueError("EC cannot be negative.")


def analyze_soil_health(payload: dict[str, Any]) -> dict[str, Any]:
    raw_lang = str(payload.get("lang", "en")).lower()
    lang = raw_lang if raw_lang in {"hi", "mr"} else "en"

    required_metrics = ["nitrogen", "phosphorus", "potassium", "ph", "moisture"]
    values: dict[str, float] = {}

    for metric in required_metrics:
        if payload.get(metric) is None:
            raise ValueError(f"{metric} is required.")
        values[metric] = float(payload[metric])

    if payload.get("organic_carbon") not in (None, ""):
        values["organic_carbon"] = float(payload["organic_carbon"])
    if payload.get("ec") not in (None, ""):
        values["ec"] = float(payload["ec"])

    _validate_values(values)

    reasons: list[str] = []
    solutions: list[str] = []
    metric_breakdown: dict[str, Any] = {}

    weighted_sum = 0.0
    weight_total = 0.0

    for metric, value in values.items():
        config = METRIC_CONFIG[metric]
        low, high = config["ideal"]
        score, state = _metric_score(value, low, high, config["tolerance"])

        weighted_sum += score * float(config["weight"])
        weight_total += float(config["weight"])

        metric_breakdown[metric] = {
            "label": _metric_label(metric, lang),
            "value": round(value, 2),
            "unit": config["unit"],
            "score": score,
            "status_code": state,
            "status": _status_label(state, lang),
            "ideal_range": f"{low:g} - {high:g}",
            "note": _metric_note(metric, state, value, lang),
        }

        if state != "optimal":
            reason, solution = _build_reason_solution(metric, state, lang)
            reasons.append(reason)
            solutions.append(solution)

    final_score = int(round(weighted_sum / max(weight_total, 1e-6)))

    if final_score >= 75:
        status_code = "healthy"
    elif final_score >= 45:
        status_code = "moderate"
    else:
        status_code = "critical"

    status_label = _status_label(status_code, lang)

    if not reasons:
        if lang in {"hi", "mr"}:
            reasons = ["अधिकांश प्रमुख मिट्टी पैरामीटर संतुलित सीमा में हैं।"]
            solutions = [
                "मौजूदा पोषण और सिंचाई प्रबंधन जारी रखें।",
                "हर 45-60 दिन पर नमी और pH की पुनः जांच करें।",
            ]
            if lang == "mr":
                reasons = [_to_marathi_text(reason) for reason in reasons]
                solutions = [_to_marathi_text(solution) for solution in solutions]
        else:
            reasons = ["Most major soil parameters are within the balanced range."]
            solutions = [
                "Continue current nutrient and irrigation management.",
                "Recheck moisture and pH every 45-60 days.",
            ]

    crops = _crop_suggestions(values, status_code, lang)

    ai_report = _generate_ai_report(
        lang=lang,
        score=final_score,
        health_status=status_label,
        reasons=reasons,
        solutions=solutions,
        crops=crops,
        metric_breakdown=metric_breakdown,
    )

    report_text = ai_report or _local_report(lang, final_score, status_label, reasons, solutions, crops)
    report_source = "ai" if ai_report else "local"

    return {
        "health_status_code": status_code,
        "health_status": status_label,
        "score": final_score,
        "reasons": reasons,
        "solutions": solutions,
        "suggested_crops": crops,
        "report": report_text,
        "report_source": report_source,
        "metric_breakdown": metric_breakdown,
    }
