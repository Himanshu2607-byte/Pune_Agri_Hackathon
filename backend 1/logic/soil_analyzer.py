from pydantic import BaseModel
from typing import List, Dict, Optional

class SoilData(BaseModel):
    ph: float
    ec: float  # Electrical Conductivity (dS/m)
    organic_carbon: float # %
    nitrogen: float # kg/ha
    phosphorus: float # kg/ha
    potassium: float # kg/ha
    zinc: Optional[float] = None # ppm
    iron: Optional[float] = None # ppm
    manganese: Optional[float] = None # ppm
    exchangeable_sodium_percentage: Optional[float] = None # ESP %
    cation_exchange_capacity: Optional[float] = None # CEC meq/100g

class Recommendation(BaseModel):
    category: str
    action: str
    quantity: str
    reason: str
    cost_estimate_inr: float = 0.0

class CropSuggestion(BaseModel):
    name: str
    suitability: str
    reason: str

class AnalysisResult(BaseModel):
    health_score: float
    fertility_level: str
    soil_type: str
    issues: List[str]
    recommendations: List[Recommendation]
    crops: List[CropSuggestion]
    total_cost_inr: float
    recovery_probability: float

def analyze_soil(data: SoilData, ml_health_score: float) -> AnalysisResult:
    issues = []
    recommendations = []
    crops = []
    total_cost = 0.0
    probability = 95.0
    
    # -----------------------------------------------------------------
    # Stage 1: The Physics & Chemistry Engine (Cation Kinetics)
    # -----------------------------------------------------------------
    soil_type = "Normal"
    
    # Check for Sodic Dispersed Soil
    esp = data.exchangeable_sodium_percentage if data.exchangeable_sodium_percentage else 0
    cec = data.cation_exchange_capacity if data.cation_exchange_capacity else 15.0
    
    if data.ph > 8.5 or esp > 15.0:
        soil_type = "Sodic / Usar Soil (Dispersed)"
        issues.append("high_alkalinity")
        issues.append("soil_dispersion_collapsed_pores")
        
        # The Exact Displacement Equation: GR = CEC * (ESP - 10) / 100 * 1.72
        # Target safe ESP is 10.0
        delta_esp = max(0, esp - 10.0)
        gr_tonnes_acre = round((cec * (delta_esp / 100.0) * 1.72), 2)
        
        if gr_tonnes_acre <= 0:
            gr_tonnes_acre = 2.0 # Fallback baseline
            
        # Cost: ₹1500 per tonne
        cost = gr_tonnes_acre * 1500 
        total_cost += cost
        
        recommendations.append(Recommendation(
            category="reclamation",
            action="apply_gypsum",
            quantity=f"{gr_tonnes_acre} tonnes/acre",
            reason="displace_sodium_flocculate_clay",
            cost_estimate_inr=cost
        ))
        
        probability -= delta_esp * 2
        crops.extend([
            CropSuggestion(name="barley", suitability="high", reason="tolerant_sodic"),
            CropSuggestion(name="cotton", suitability="moderate", reason="tolerant_alkalinity")
        ])
        
    elif data.ph < 6.0:
        soil_type = "Acidic / Laterite Soil"
        issues.append("low_ph")
        
        # Simplified Liming Factor: 1.5 tonnes per acre if pH < 6.0
        lime_tonnes_acre = 1.5
        lime_cost = lime_tonnes_acre * 2000 # ₹2000 per tonne
        total_cost += lime_cost
        
        recommendations.append(Recommendation(
            category="reclamation",
            action="apply_lime",
            quantity=f"{lime_tonnes_acre} tonnes/acre",
            reason="neutralize_acidity",
            cost_estimate_inr=lime_cost
        ))
        crops.extend([
            CropSuggestion(name="paddy", suitability="high", reason="tolerant_acidic"),
            CropSuggestion(name="oats", suitability="moderate", reason="tolerant_acidic")
        ])
    elif data.ec > 4.0 and data.ph < 8.5:
        soil_type = "Saline Soil"
        issues.append("high_salinity")
        probability -= 15
        
        recommendations.append(Recommendation(
            category="reclamation",
            action="leach_salts",
            quantity="Continuous Leaching",
            reason="flush_salts_root_zone",
            cost_estimate_inr=0.0
        ))
        crops.append(CropSuggestion(name="sugar_beet", suitability="moderate", reason="tolerant_salinity"))
    else:
        soil_type = "Normal"
        crops.extend([
            CropSuggestion(name="wheat", suitability="high", reason="ideal_ph"),
            CropSuggestion(name="mustard", suitability="high", reason="ideal_ph")
        ])

    # -----------------------------------------------------------------
    # Stage 2: Calculating Carbon Deficit (Using Organic Carbon %)
    # -----------------------------------------------------------------
    target_oc = 0.75
    if data.organic_carbon < target_oc:
        issues.append("low_oc")
        
        # Pure Carbon Deficit (kg/acre) = (0.75% - Your OC%) * 2,000,000 kg
        deficit_percentage = target_oc - data.organic_carbon
        pure_carbon_deficit = (deficit_percentage / 100.0) * 2000000
        
        # Required FYM (kg/acre) = Pure Carbon Deficit / 0.15
        required_fym_kg = round(pure_carbon_deficit / 0.15)
        required_fym_tonnes = round(required_fym_kg / 1000.0, 1)
        
        compost_cost = required_fym_tonnes * 1000 # ₹1000 per tonne
        total_cost += compost_cost
        
        recommendations.append(Recommendation(
            category="nutrient",
            action="apply_compost",
            quantity=f"{required_fym_tonnes} tonnes/acre",
            reason="fym_deficit_rebuild",
            cost_estimate_inr=compost_cost
        ))
        probability -= 5

    # -----------------------------------------------------------------
    # Stage 2.5: The Biological Engine (Microbial & Green Manure)
    # -----------------------------------------------------------------
    if data.nitrogen < 150 or data.organic_carbon < 0.4:
        # Green Manuring
        recommendations.append(Recommendation(
            category="biological",
            action="grow_dhaincha",
            quantity="45 Days Growth",
            reason="narrow_cn_ratio_nitrogen_fix",
            cost_estimate_inr=500 # Cost of Dhaincha seeds
        ))
        total_cost += 500

    if data.phosphorus < 20:
        # Microbial Acidulation (PSB)
        recommendations.append(Recommendation(
            category="biological",
            action="inoculate_psb",
            quantity="250g PSB + 25kg FYM",
            reason="microbial_acidulation_phosphorus",
            cost_estimate_inr=150 # Cost of Bio-inoculant packet
        ))
        total_cost += 150

    # -----------------------------------------------------------------
    # Stage 3 & 4: Computing Nutrients & Commercial Fertilizer Mapping
    # -----------------------------------------------------------------
    # Target: Wheat (Yield = 40 quintals/acre)
    # STCR Standard Coefficients for Wheat (mock baseline)
    # FN = (4.0 * Y) - (0.4 * Soil N)
    # FP = (2.5 * Y) - (0.5 * Soil P)
    # FK = (2.5 * Y) - (0.2 * Soil K)
    target_yield = 40.0
    
    fn_required = (4.0 * target_yield) - (0.4 * data.nitrogen)
    fp_required = (2.5 * target_yield) - (0.5 * data.phosphorus)
    fk_required = (2.5 * target_yield) - (0.2 * data.potassium)
    
    # Floor at 0
    fn_required = max(0, fn_required)
    fp_required = max(0, fp_required)
    fk_required = max(0, fk_required)
    
    if fn_required > 0 or fp_required > 0 or fk_required > 0:
        import math
        
        # Stage 4: Mapping to Commercial Bags
        dap_kg = fp_required / 0.46
        dap_bags = math.ceil(dap_kg / 50.0)
        
        # DAP contributes 18% Nitrogen. Deduct this from Urea requirement.
        n_from_dap = (dap_bags * 50.0) * 0.18
        remaining_n = max(0, fn_required - n_from_dap)
        
        urea_kg = remaining_n / 0.46
        urea_bags = math.ceil(urea_kg / 45.0)
        
        mop_kg = fk_required / 0.60
        mop_bags = math.ceil(mop_kg / 50.0)
        
        if dap_bags > 0:
            issues.append("low_phosphorus")
            dap_cost = dap_bags * 1350 # ₹1350 per 50kg bag
            total_cost += dap_cost
            recommendations.append(Recommendation(
                category="fertilizer",
                action="apply_dap",
                quantity=f"{dap_bags} bags/acre",
                reason="stcr_phosphorus_mapping",
                cost_estimate_inr=dap_cost
            ))
            
        if urea_bags > 0:
            issues.append("low_nitrogen")
            urea_cost = urea_bags * 266.50 # ₹266.50 per 45kg bag
            total_cost += urea_cost
            recommendations.append(Recommendation(
                category="fertilizer",
                action="apply_urea",
                quantity=f"{urea_bags} bags/acre",
                reason="stcr_nitrogen_mapping",
                cost_estimate_inr=urea_cost
            ))
            
        if mop_bags > 0:
            issues.append("low_potassium")
            mop_cost = mop_bags * 1700 # ₹1700 per 50kg bag
            total_cost += mop_cost
            recommendations.append(Recommendation(
                category="fertilizer",
                action="apply_mop",
                quantity=f"{mop_bags} bags/acre",
                reason="stcr_potassium_mapping",
                cost_estimate_inr=mop_cost
            ))

    if ml_health_score > 75:
        fertility_level = "high"
    elif ml_health_score > 50:
        fertility_level = "medium"
    else:
        fertility_level = "low"
        
    probability = max(10.0, min(99.0, round(probability, 1)))
        
    return AnalysisResult(
        health_score=ml_health_score,
        fertility_level=fertility_level,
        soil_type=soil_type,
        issues=issues,
        recommendations=recommendations,
        crops=crops,
        total_cost_inr=round(total_cost, 2),
        recovery_probability=probability
    )
