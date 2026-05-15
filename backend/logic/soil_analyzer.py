from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class SoilData(BaseModel):
    ph: float = Field(..., ge=1.0, le=14.0)
    ec: float = Field(..., ge=0.0, le=50.0)  # Electrical Conductivity (dS/m)
    organic_carbon: float = Field(..., ge=0.0, le=100.0) # %
    nitrogen: float = Field(..., ge=0.0, le=2000.0) # kg/ha
    phosphorus: float = Field(..., ge=0.0, le=2000.0) # kg/ha
    potassium: float = Field(..., ge=0.0, le=2000.0) # kg/ha
    # Micronutrients (in ppm / mg/kg)
    sulphur: Optional[float] = Field(None, ge=0.0, le=500.0)
    zinc: Optional[float] = Field(None, ge=0.0, le=100.0)
    iron: Optional[float] = Field(None, ge=0.0, le=500.0)
    copper: Optional[float] = Field(None, ge=0.0, le=100.0)
    manganese: Optional[float] = Field(None, ge=0.0, le=500.0)
    boron: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    exchangeable_sodium_percentage: Optional[float] = Field(None, ge=0.0, le=100.0) # ESP %
    cation_exchange_capacity: Optional[float] = Field(None, ge=0.0, le=200.0) # CEC meq/100g

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
    # Stage 1: Granular Physics Classification & Cation Kinetics
    # -----------------------------------------------------------------
    
    # 1. Determine granular pH classification
    if data.ph < 4.0:
        ph_str = "Extremely Acidic"
    elif 4.0 <= data.ph < 5.5:
        ph_str = "Strongly Acidic"
    elif 5.5 <= data.ph < 6.5:
        ph_str = "Moderately / Slightly Acidic"
    elif 6.5 <= data.ph <= 7.5:
        ph_str = "Neutral (Ideal Range)"
    elif 7.5 < data.ph <= 8.5:
        ph_str = "Moderately Alkaline"
    else:
        ph_str = "Strongly Alkaline / Usar Land"
        
    # 2. Determine granular EC classification
    ec_str = ""
    if data.ec > 4.0:
        ec_str = " (Highly Saline)"
    elif 2.0 < data.ec <= 4.0:
        ec_str = " (Injurious to Sensitive Crops)"
    elif 1.0 < data.ec <= 2.0:
        ec_str = " (Critical for Germination)"
        
    soil_type = ph_str + ec_str
    
    # 3. Kinematic Engine (Reclamation Math)
    esp = data.exchangeable_sodium_percentage if data.exchangeable_sodium_percentage else 0
    cec = data.cation_exchange_capacity if data.cation_exchange_capacity else 15.0
    
    if data.ph > 8.5 or esp > 15.0:
        issues.append("high_alkalinity")
        issues.append("soil_dispersion_collapsed_pores")
        
        # ICAR Optimized Displacement Equation: GR = (CEC * (ESP - 10) / 100 * 1.72) * 50% Optimization
        # Note: 1.72 factor yields tonnes/hectare. Divide by 2.47 to get tonnes/acre.
        delta_esp = max(0, esp - 10.0)
        gr_tonnes_hectare = (cec * (delta_esp / 100.0) * 1.72) * 0.5
        gr_tonnes_acre = round(gr_tonnes_hectare / 2.47, 2)
        
        if gr_tonnes_acre <= 0:
            gr_tonnes_acre = 2.0 # Fallback baseline
            
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
            CropSuggestion(name="cotton", suitability="moderate", reason="tolerant_alkalinity"),
            CropSuggestion(name="sorghum", suitability="moderate", reason="tolerant_sodic"),
            CropSuggestion(name="sugarcane", suitability="moderate", reason="tolerant_alkalinity"),
            CropSuggestion(name="castor", suitability="moderate", reason="tolerant_alkalinity")
        ])
        
    elif data.ph < 6.0:
        issues.append("low_ph")
        
        # Agronomic Liming Factor Equation: (6.5 - pH) * 1.5
        ph_deficit = max(0, 6.5 - data.ph)
        lime_tonnes_acre = round(ph_deficit * 1.5, 2)
        
        if lime_tonnes_acre <= 0:
            lime_tonnes_acre = 1.0 # Baseline floor
            
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
            CropSuggestion(name="oats", suitability="moderate", reason="tolerant_acidic"),
            CropSuggestion(name="sweet_potato", suitability="high", reason="tolerant_acidic")
        ])
        
    elif data.ec > 4.0 and data.ph <= 8.5:
        issues.append("high_salinity")
        probability -= 15
        
        recommendations.append(Recommendation(
            category="reclamation",
            action="leach_salts",
            quantity="Continuous Leaching",
            reason="flush_salts_root_zone",
            cost_estimate_inr=0.0
        ))
        crops.extend([
            CropSuggestion(name="sugar_beet", suitability="high", reason="tolerant_salinity"),
            CropSuggestion(name="barley", suitability="high", reason="tolerant_salinity"),
            CropSuggestion(name="pearl_millet", suitability="moderate", reason="tolerant_salinity"),
            CropSuggestion(name="ragi", suitability="high", reason="tolerant_salinity"),
            CropSuggestion(name="sunflower", suitability="moderate", reason="tolerant_salinity")
        ])
        
    else:
        crops.extend([
            CropSuggestion(name="wheat", suitability="high", reason="ideal_ph"),
            CropSuggestion(name="mustard", suitability="high", reason="ideal_ph"),
            CropSuggestion(name="soybean", suitability="high", reason="ideal_ph"),
            CropSuggestion(name="gram", suitability="high", reason="ideal_ph"),
            CropSuggestion(name="maize", suitability="moderate", reason="ideal_ph")
        ])

    # -----------------------------------------------------------------
    # Stage 2: Calculating Carbon Deficit (Using Organic Carbon %)
    # -----------------------------------------------------------------
    target_oc = 0.75
    if data.organic_carbon < target_oc:
        issues.append("low_oc")
        
        # Dynamic parameter-based step function according to ICAR INM guidelines
        if data.organic_carbon < 0.4:
            annual_dose = 5.0  # Severe Deficit: Intensive rebuild dose
        elif data.organic_carbon < 0.6:
            annual_dose = 3.0  # Moderate Deficit: Standard recovery dose
        else:
            annual_dose = 1.5  # Mild Deficit: Routine maintenance dose
            
        compost_cost = annual_dose * 1000 # ₹1000 per tonne
        total_cost += compost_cost
        
        recommendations.append(Recommendation(
            category="nutrient",
            action="apply_compost",
            quantity=f"{annual_dose} tonnes/acre",
            reason="fym_deficit_rebuild",
            cost_estimate_inr=compost_cost
        ))
        probability -= 5

    # -----------------------------------------------------------------
    # Stage 2.5: The Biological Engine (Microbial & Green Manure)
    # -----------------------------------------------------------------
    if data.nitrogen < 280 or data.organic_carbon < 0.5:
        # Green Manuring
        recommendations.append(Recommendation(
            category="biological",
            action="grow_dhaincha",
            quantity="45 Days Growth",
            reason="narrow_cn_ratio_nitrogen_fix",
            cost_estimate_inr=500 # Cost of Dhaincha seeds
        ))
        total_cost += 500

    if data.phosphorus < 25:
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
    # Stage 2.8: Micronutrient Deficiency Engine
    # -----------------------------------------------------------------
    if data.sulphur is not None and data.sulphur < 10.0:
        issues.append("low_sulphur")
        recommendations.append(Recommendation(
            category="fertilizer", action="apply_sulphur", quantity="10 kg/acre", reason="sulphur_reason", cost_estimate_inr=500
        ))
        total_cost += 500
        
    if data.zinc is not None and data.zinc < 0.6:
        issues.append("low_zinc")
        recommendations.append(Recommendation(
            category="fertilizer", action="apply_zinc", quantity="10 kg/acre", reason="zinc_reason", cost_estimate_inr=600
        ))
        total_cost += 600
        
    if data.iron is not None and data.iron < 4.5:
        issues.append("low_iron")
        recommendations.append(Recommendation(
            category="fertilizer", action="apply_iron", quantity="20 kg/acre", reason="iron_reason", cost_estimate_inr=400
        ))
        total_cost += 400
        
    if data.copper is not None and data.copper < 0.2:
        issues.append("low_copper")
        recommendations.append(Recommendation(
            category="fertilizer", action="apply_copper", quantity="2 kg/acre", reason="copper_reason", cost_estimate_inr=300
        ))
        total_cost += 300
        
    if data.manganese is not None and data.manganese < 2.0:
        issues.append("low_manganese")
        recommendations.append(Recommendation(
            category="fertilizer", action="apply_manganese", quantity="5 kg/acre", reason="manganese_reason", cost_estimate_inr=400
        ))
        total_cost += 400
        
    if data.boron is not None and data.boron < 0.5:
        issues.append("low_boron")
        recommendations.append(Recommendation(
            category="fertilizer", action="apply_boron", quantity="4 kg/acre", reason="boron_reason", cost_estimate_inr=350
        ))
        total_cost += 350

    # -----------------------------------------------------------------
    # Stage 3 & 4: Computing Nutrients & Commercial Fertilizer Mapping
    # -----------------------------------------------------------------
    # Target: Wheat (Yield = 40 quintals/hectare)
    # STCR Standard Coefficients for Wheat
    # FN = (4.0 * Y) - (0.4 * Soil N)
    # FP = (2.5 * Y) - (0.5 * Soil P)
    # FK = (2.5 * Y) - (0.2 * Soil K)
    target_yield_ha = 40.0
    
    fn_required_ha = (4.0 * target_yield_ha) - (0.4 * data.nitrogen)
    fp_required_ha = (2.5 * target_yield_ha) - (0.5 * data.phosphorus)
    fk_required_ha = (2.5 * target_yield_ha) - (0.2 * data.potassium)
    
    # Convert kg/hectare to kg/acre (divide by 2.47)
    fn_required = max(0, fn_required_ha / 2.47)
    fp_required = max(0, fp_required_ha / 2.47)
    fk_required = max(0, fk_required_ha / 2.47)
    
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
