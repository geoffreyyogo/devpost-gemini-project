"""
Agrovet Recommendation Service
===============================

Bridges disease/deficiency detection → product recommendations → nearest agrovet
shops → purchase flow.

Pipeline:
  1. Disease/deficiency detected (from CNN, IoT thresholds, or satellite data)
  2. Treatment recommendations looked up (TREATMENT_CATALOG)
  3. Nearest agrovets searched by farmer's sub_county → county
  4. Matching products found with prices + stock
  5. Quantities calculated based on farm size
  6. Purchase option presented (web link / USSD / SMS)

Integrates with:
  - SmartAlertService (consumes disease_context, soil_context)
  - FloraAIService    (system_action triggers agrovet queries)
  - DiseaseDetectionService (classification results)
  - IoTIngestionService (anomaly → deficiency mapping)
"""

import logging
import math
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from database.connection import get_sync_session
    from database.models import (
        AgrovetProduct, AgrovetProfile, AgrovetOrder,
        Farmer, Farm, Transaction,
    )
    from sqlmodel import select, text, or_, and_
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    get_sync_session = None  # type: ignore[assignment]
    AgrovetProduct = None  # type: ignore[assignment,misc]
    AgrovetProfile = None  # type: ignore[assignment,misc]
    AgrovetOrder = None  # type: ignore[assignment,misc]
    Farmer = None  # type: ignore[assignment,misc]
    Farm = None  # type: ignore[assignment,misc]
    Transaction = None  # type: ignore[assignment,misc]
    select = None  # type: ignore[assignment]
    text = None  # type: ignore[assignment]
    or_ = None  # type: ignore[assignment]
    and_ = None  # type: ignore[assignment]
    logger.warning("Database modules not available — AgrovetService disabled")

# ── Gemini for AI-driven treatment plans ───────────────────────────
try:
    from google import genai
    from google.genai import types as genai_types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]
    GENAI_AVAILABLE = False
    logger.info("google-genai not installed — AI treatment plans disabled, using catalog only")


# ═══════════════════════════════════════════════════════════════════════
#  TREATMENT CATALOG — maps diseases/deficiencies → products + doses
# ═══════════════════════════════════════════════════════════════════════

TREATMENT_CATALOG = {
    # ── Diseases (from BloomVisionCNN) ──────────────────────────────
    "leaf_blight": {
        "display_name": "Leaf Blight",
        "display_name_sw": "Ugonjwa wa Majani",
        "description": "Bacterial or fungal blight causing brown/yellow leaf lesions",
        "urgency": "high",
        "treatments": [
            {
                "product_type": "pesticide",
                "product_category": "fungicide",
                "names": ["Mancozeb 80% WP", "Ridomil Gold MZ", "Dithane M-45"],
                "dose_per_acre": "200g",
                "dose_unit": "grams per acre",
                "application": "Foliar spray every 7-10 days",
                "notes": "Apply early morning or late evening. Do NOT apply if rain expected within 6 hours.",
            },
            {
                "product_type": "pesticide",
                "product_category": "copper_fungicide",
                "names": ["Copper Oxychloride", "Kocide 2000"],
                "dose_per_acre": "150g",
                "dose_unit": "grams per acre",
                "application": "Foliar spray as preventive/curative",
                "notes": "Organic-approved option. Safe for most crops.",
            },
        ],
        "cultural_practices": [
            "Remove and burn infected leaves immediately",
            "Improve air circulation by pruning/spacing crops",
            "Avoid overhead irrigation — use drip instead",
            "Rotate crops next season to break disease cycle",
        ],
    },

    "rust": {
        "display_name": "Rust Disease",
        "display_name_sw": "Kutu ya Mimea",
        "description": "Fungal rust causing orange-brown pustules on leaves",
        "urgency": "high",
        "treatments": [
            {
                "product_type": "pesticide",
                "product_category": "systemic_fungicide",
                "names": ["Propiconazole 250 EC", "Score 250 EC", "Tilt 250 EC"],
                "dose_per_acre": "100ml",
                "dose_unit": "ml per acre",
                "application": "Foliar spray at first sign of rust",
                "notes": "Systemic action — absorbed into leaves. Most effective early.",
            },
            {
                "product_type": "pesticide",
                "product_category": "protective_fungicide",
                "names": ["Mancozeb 80% WP", "Antracol"],
                "dose_per_acre": "200g",
                "dose_unit": "grams per acre",
                "application": "Preventive spray before disease onset",
                "notes": "Contact fungicide — re-apply after rain.",
            },
        ],
        "cultural_practices": [
            "Plant rust-resistant varieties (e.g., WH505 for wheat, H614D for maize)",
            "Remove volunteer plants between seasons",
            "Avoid planting same crop in adjacent fields",
        ],
    },

    "aphid_damage": {
        "display_name": "Aphid/Pest Damage",
        "display_name_sw": "Uharibifu wa Wadudu",
        "description": "Insect pest damage — aphids, whiteflies, thrips, or mites",
        "urgency": "medium",
        "treatments": [
            {
                "product_type": "pesticide",
                "product_category": "insecticide",
                "names": ["Imidacloprid 200 SL", "Confidor", "Thunder OD 145"],
                "dose_per_acre": "50ml",
                "dose_unit": "ml per acre",
                "application": "Systemic drench or foliar spray",
                "notes": "Effective against sucking pests. Observe pre-harvest interval.",
            },
            {
                "product_type": "pesticide",
                "product_category": "bio_insecticide",
                "names": ["Neem Oil Extract", "Azadirachtin", "Achook"],
                "dose_per_acre": "200ml",
                "dose_unit": "ml per acre",
                "application": "Foliar spray every 5-7 days",
                "notes": "Organic-approved. Safe for beneficial insects if applied correctly.",
            },
        ],
        "cultural_practices": [
            "Introduce beneficial insects (ladybugs, lacewings)",
            "Use yellow sticky traps for monitoring",
            "Intercrop with repellent plants (marigold, basil)",
            "Remove heavily infested plant parts",
        ],
    },

    "wilting": {
        "display_name": "Wilting / Water Stress",
        "display_name_sw": "Kunyauka kwa Mimea",
        "description": "Plant wilting from water stress, fusarium, or nutrient deficiency",
        "urgency": "high",
        "treatments": [
            {
                "product_type": "fertilizer",
                "product_category": "foliar_feed",
                "names": ["Foliar Feed NPK 20-20-20", "Yara Mila", "Easy Grow"],
                "dose_per_acre": "500g",
                "dose_unit": "grams per acre (dissolved in 200L water)",
                "application": "Foliar spray to boost recovery",
                "notes": "Helps stressed plants recover nutrients quickly.",
            },
            {
                "product_type": "pesticide",
                "product_category": "fungicide",
                "names": ["Carbendazim 50% WP", "Bavisitin"],
                "dose_per_acre": "100g",
                "dose_unit": "grams per acre",
                "application": "Soil drench around plant base if fusarium suspected",
                "notes": "Only if wilting is caused by fusarium wilt (check roots for brown discoloration).",
            },
        ],
        "cultural_practices": [
            "Check soil moisture — irrigate if below 40% field capacity",
            "Mulch around plants to conserve moisture",
            "If fusarium: remove affected plants, do NOT compost",
            "Improve drainage if waterlogging is the cause",
        ],
    },

    # ── Nutrient deficiencies (from IoT soil sensors) ────────────────

    "nitrogen_low": {
        "display_name": "Nitrogen Deficiency",
        "display_name_sw": "Upungufu wa Nitrojeni",
        "description": "Soil nitrogen below optimal range — yellowing lower leaves",
        "urgency": "medium",
        "treatments": [
            {
                "product_type": "fertilizer",
                "product_category": "nitrogen_fertilizer",
                "names": ["CAN (Calcium Ammonium Nitrate)", "Urea 46%", "ASN 26%"],
                "dose_per_acre": "50kg",
                "dose_unit": "kg per acre",
                "application": "Side-dress application along crop rows, 4-6 weeks after planting",
                "notes": "CAN preferred for acidic soils. Urea for neutral/alkaline soils. Apply before rain or irrigate after.",
            },
        ],
        "cultural_practices": [
            "Intercrop with nitrogen-fixing legumes (beans, cowpeas)",
            "Apply well-decomposed farmyard manure (5-10 tonnes/acre)",
            "Green manuring with Crotalaria or Mucuna",
        ],
    },

    "phosphorus_low": {
        "display_name": "Phosphorus Deficiency",
        "display_name_sw": "Upungufu wa Fosforasi",
        "description": "Soil phosphorus below optimal — purple/dark leaves, poor root growth",
        "urgency": "medium",
        "treatments": [
            {
                "product_type": "fertilizer",
                "product_category": "phosphate_fertilizer",
                "names": ["DAP (Di-Ammonium Phosphate)", "TSP (Triple Super Phosphate)", "SSP"],
                "dose_per_acre": "50kg",
                "dose_unit": "kg per acre",
                "application": "Band placement at planting depth, close to seed rows",
                "notes": "Apply at planting. Phosphorus is immobile — must be placed near roots.",
            },
        ],
        "cultural_practices": [
            "Apply bone meal (organic alternative) at 3-5 tonnes/acre",
            "Maintain soil pH 5.5-7.0 for optimal P availability",
            "Mycorrhizal inoculants improve P uptake",
        ],
    },

    "potassium_low": {
        "display_name": "Potassium Deficiency",
        "display_name_sw": "Upungufu wa Potasiamu",
        "description": "Soil potassium below optimal — leaf edge browning, weak stems",
        "urgency": "medium",
        "treatments": [
            {
                "product_type": "fertilizer",
                "product_category": "potash_fertilizer",
                "names": ["MOP (Muriate of Potash)", "SOP (Sulphate of Potash)", "NPK 17-17-17"],
                "dose_per_acre": "40kg",
                "dose_unit": "kg per acre",
                "application": "Base application or side-dress during vegetative growth",
                "notes": "SOP preferred for potassium-sensitive crops (potatoes, tomatoes, coffee).",
            },
        ],
        "cultural_practices": [
            "Apply wood ash (contains 5-10% K2O) at 1-2 tonnes/acre",
            "Compost improves potassium retention in sandy soils",
            "Banana stems/leaves are rich in potassium — use as mulch",
        ],
    },

    "soil_ph_low": {
        "display_name": "Acidic Soil (Low pH)",
        "display_name_sw": "Udongo Wenye Asidi",
        "description": "Soil pH below 5.5 — aluminium toxicity, reduced nutrient availability",
        "urgency": "medium",
        "treatments": [
            {
                "product_type": "fertilizer",
                "product_category": "soil_amendment",
                "names": ["Agricultural Lime (CaCO3)", "Dolomitic Lime", "Calcitic Lime"],
                "dose_per_acre": "1000kg",
                "dose_unit": "kg per acre (1 tonne per acre for severely acidic soils)",
                "application": "Broadcast and incorporate into top 15cm of soil before planting",
                "notes": "Apply 2-3 months before planting. Do NOT apply with fertilizer (N loss). Retest pH after 3 months.",
            },
        ],
        "cultural_practices": [
            "Add organic matter to buffer pH changes",
            "Avoid ammonium-based fertilizers on acidic soils",
            "Test soil pH annually",
        ],
    },

    "soil_ph_high": {
        "display_name": "Alkaline Soil (High pH)",
        "display_name_sw": "Udongo Wenye Alkali",
        "description": "Soil pH above 7.5 — iron/zinc deficiency, poor micronutrient uptake",
        "urgency": "low",
        "treatments": [
            {
                "product_type": "fertilizer",
                "product_category": "soil_amendment",
                "names": ["Elemental Sulphur", "Ammonium Sulphate", "Gypsum"],
                "dose_per_acre": "200kg",
                "dose_unit": "kg per acre",
                "application": "Broadcast and work into soil before planting",
                "notes": "Sulphur is slow-acting (takes 3-6 months). Use ammonium sulphate for quicker results.",
            },
        ],
        "cultural_practices": [
            "Add organic matter (compost, farmyard manure)",
            "Use acidifying fertilizers (ammonium sulphate, urea)",
            "Irrigate with non-saline water",
        ],
    },

    "moisture_low": {
        "display_name": "Low Soil Moisture",
        "display_name_sw": "Upungufu wa Maji Ardhini",
        "description": "Soil moisture below field capacity — drought stress",
        "urgency": "high",
        "treatments": [
            {
                "product_type": "tools",
                "product_category": "irrigation",
                "names": ["Drip Irrigation Kit", "Sprinkler System", "Watering Can (20L)"],
                "dose_per_acre": "1 kit",
                "dose_unit": "per acre",
                "application": "Install drip irrigation for efficient water use",
                "notes": "Drip irrigation uses 30-50% less water than flood irrigation.",
            },
            {
                "product_type": "tools",
                "product_category": "mulch",
                "names": ["Mulching Material", "Black Polythene Mulch"],
                "dose_per_acre": "1 roll",
                "dose_unit": "per acre",
                "application": "Apply 3-5cm layer around plants",
                "notes": "Reduces evaporation by 25-50%. Use organic mulch (grass, straw) or plastic.",
            },
        ],
        "cultural_practices": [
            "Irrigate early morning or late evening to reduce evaporation",
            "Mulch with organic material (3-5cm layer)",
            "Practice water harvesting — collect rainwater",
            "Prioritize critical growth stages (flowering, grain filling)",
        ],
    },

    # ── General pest issues ─────────────────────────────────────────
    "fall_armyworm": {
        "display_name": "Fall Armyworm",
        "display_name_sw": "Viwavi Jeshi",
        "description": "Spodoptera frugiperda — devastating maize pest in Kenya",
        "urgency": "high",
        "treatments": [
            {
                "product_type": "pesticide",
                "product_category": "insecticide",
                "names": ["Emamectin Benzoate", "Ampligo 150 ZC", "Belt Expert"],
                "dose_per_acre": "40ml",
                "dose_unit": "ml per acre",
                "application": "Spray directly into maize whorls, target larvae",
                "notes": "Apply within first 2 weeks of infestation. Scout regularly for egg masses.",
            },
            {
                "product_type": "pesticide",
                "product_category": "bio_pesticide",
                "names": ["Bt (Bacillus thuringiensis)", "Thuricide"],
                "dose_per_acre": "100g",
                "dose_unit": "grams per acre",
                "application": "Spray on leaves — larvae must ingest",
                "notes": "Organic-approved. Most effective on young larvae (L1-L3 instar).",
            },
        ],
        "cultural_practices": [
            "Push-pull technology: plant Brachiaria (push) and Desmodium (pull) around maize",
            "Hand-pick and destroy egg masses and young larvae",
            "Use pheromone traps for monitoring adult moth populations",
            "Plant early with the first rains to establish crops before peak armyworm season",
        ],
    },
}

# ═══════════════════════════════════════════════════════════════════════
#  DEFICIENCY DETECTION FROM SENSOR DATA
# ═══════════════════════════════════════════════════════════════════════

# Thresholds for mapping IoT sensor readings to deficiency conditions
SENSOR_DEFICIENCY_THRESHOLDS = {
    "soil_nitrogen": {"low": 20, "optimal_min": 20, "optimal_max": 60, "high": 80},
    "soil_phosphorus": {"low": 15, "optimal_min": 15, "optimal_max": 45, "high": 60},
    "soil_potassium": {"low": 100, "optimal_min": 100, "optimal_max": 250, "high": 350},
    "soil_ph": {"very_low": 5.0, "low": 5.5, "optimal_min": 5.5, "optimal_max": 7.0, "high": 7.5, "very_high": 8.0},
    "soil_moisture_pct": {"very_low": 25, "low": 40, "optimal_min": 50, "optimal_max": 80, "high": 90},
}


def detect_deficiencies_from_sensors(sensor_data: Dict) -> List[Dict]:
    """
    Analyze IoT sensor readings and return detected deficiencies.

    Args:
        sensor_data: Dict with keys like soil_nitrogen, soil_ph, soil_moisture_pct, etc.

    Returns:
        List of {condition, display_name, value, threshold, severity}
    """
    deficiencies = []

    n = sensor_data.get("soil_nitrogen")
    if n is not None and n < SENSOR_DEFICIENCY_THRESHOLDS["soil_nitrogen"]["low"]:
        deficiencies.append({
            "condition": "nitrogen_low",
            "display_name": "Low Nitrogen",
            "value": n,
            "threshold": SENSOR_DEFICIENCY_THRESHOLDS["soil_nitrogen"]["low"],
            "severity": "warning" if n > 10 else "critical",
        })

    p = sensor_data.get("soil_phosphorus")
    if p is not None and p < SENSOR_DEFICIENCY_THRESHOLDS["soil_phosphorus"]["low"]:
        deficiencies.append({
            "condition": "phosphorus_low",
            "display_name": "Low Phosphorus",
            "value": p,
            "threshold": SENSOR_DEFICIENCY_THRESHOLDS["soil_phosphorus"]["low"],
            "severity": "warning" if p > 8 else "critical",
        })

    k = sensor_data.get("soil_potassium")
    if k is not None and k < SENSOR_DEFICIENCY_THRESHOLDS["soil_potassium"]["low"]:
        deficiencies.append({
            "condition": "potassium_low",
            "display_name": "Low Potassium",
            "value": k,
            "threshold": SENSOR_DEFICIENCY_THRESHOLDS["soil_potassium"]["low"],
            "severity": "warning" if k > 50 else "critical",
        })

    ph = sensor_data.get("soil_ph")
    if ph is not None:
        if ph < SENSOR_DEFICIENCY_THRESHOLDS["soil_ph"]["low"]:
            deficiencies.append({
                "condition": "soil_ph_low",
                "display_name": "Acidic Soil",
                "value": ph,
                "threshold": SENSOR_DEFICIENCY_THRESHOLDS["soil_ph"]["low"],
                "severity": "critical" if ph < 5.0 else "warning",
            })
        elif ph > SENSOR_DEFICIENCY_THRESHOLDS["soil_ph"]["high"]:
            deficiencies.append({
                "condition": "soil_ph_high",
                "display_name": "Alkaline Soil",
                "value": ph,
                "threshold": SENSOR_DEFICIENCY_THRESHOLDS["soil_ph"]["high"],
                "severity": "critical" if ph > 8.0 else "warning",
            })

    moisture = sensor_data.get("soil_moisture_pct")
    if moisture is not None and moisture < SENSOR_DEFICIENCY_THRESHOLDS["soil_moisture_pct"]["low"]:
        deficiencies.append({
            "condition": "moisture_low",
            "display_name": "Low Soil Moisture",
            "value": moisture,
            "threshold": SENSOR_DEFICIENCY_THRESHOLDS["soil_moisture_pct"]["low"],
            "severity": "critical" if moisture < 25 else "warning",
        })

    return deficiencies


# ═══════════════════════════════════════════════════════════════════════
#  AGROVET SERVICE — The core integration class
# ═══════════════════════════════════════════════════════════════════════

class AgrovetRecommendationService:
    """
    Bridges disease/deficiency detection → product recommendations
    → nearest agrovet shops → purchase flow.
    """

    def __init__(self, db_service=None):
        self.db_service = db_service
        self.gemini_client = None
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        # Initialize Gemini for AI treatment plans
        if GENAI_AVAILABLE:
            try:
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
                if use_vertex:
                    project = os.getenv("GOOGLE_CLOUD_PROJECT")
                    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
                    self.gemini_client = genai.Client(vertexai=True, project=project, location=location)
                    logger.info("  ↳ Gemini (Vertex AI) ready for AI treatment plans")
                elif api_key:
                    self.gemini_client = genai.Client(api_key=api_key)
                    logger.info("  ↳ Gemini (API key) ready for AI treatment plans")
            except Exception as e:
                logger.warning(f"Gemini init for treatment plans failed: {e}")

        logger.info("✓ AgrovetRecommendationService initialized")

    # ------------------------------------------------------------------ #
    #  1. Get treatment plan for a condition
    # ------------------------------------------------------------------ #

    def get_treatment_plan(
        self,
        condition: str,
        farm_size_acres: float = 1.0,
        crops: Optional[List[str]] = None,
    ) -> Dict:
        """
        Look up treatment plan from TREATMENT_CATALOG and scale quantities
        to the farmer's actual farm size.

        Args:
            condition: e.g. "leaf_blight", "nitrogen_low", "soil_ph_low"
            farm_size_acres: farmer's farm size for dose calculation
            crops: list of crops grown (for filtering applicable products)

        Returns:
            {
                "condition": "leaf_blight",
                "display_name": "Leaf Blight",
                "urgency": "high",
                "treatments": [...scaled quantities...],
                "cultural_practices": [...],
                "estimated_cost_range_kes": {"min": 500, "max": 2000},
            }
        """
        catalog = TREATMENT_CATALOG.get(condition)
        if not catalog:
            return {
                "condition": condition,
                "display_name": condition.replace("_", " ").title(),
                "urgency": "medium",
                "treatments": [],
                "cultural_practices": ["Consult your local agricultural extension officer"],
                "error": f"No treatment data for '{condition}' in catalog",
            }

        # Scale doses to farm size
        scaled_treatments = []
        for t in catalog["treatments"]:
            dose_str = t["dose_per_acre"]
            try:
                # Parse dose: "200g" → 200, "50ml" → 50, "50kg" → 50
                numeric = float(''.join(c for c in dose_str if c.isdigit() or c == '.'))
                unit = ''.join(c for c in dose_str if c.isalpha())
                scaled_amount = numeric * farm_size_acres
                scaled_dose = f"{scaled_amount:.0f}{unit}"
            except (ValueError, IndexError):
                scaled_dose = f"{dose_str} × {farm_size_acres:.1f} acres"

            scaled_treatments.append({
                **t,
                "dose_for_farm": scaled_dose,
                "farm_size_acres": farm_size_acres,
            })

        return {
            "condition": condition,
            "display_name": catalog["display_name"],
            "display_name_sw": catalog.get("display_name_sw", ""),
            "description": catalog["description"],
            "urgency": catalog["urgency"],
            "treatments": scaled_treatments,
            "cultural_practices": catalog.get("cultural_practices", []),
        }

    # ------------------------------------------------------------------ #
    #  1b. AI-driven treatment plan (Gemini + catalog baseline)
    # ------------------------------------------------------------------ #

    def get_ai_treatment_plan(
        self,
        condition: str,
        farm_size_acres: float = 1.0,
        crops: Optional[List[str]] = None,
        sensor_data: Optional[Dict] = None,
        satellite_data: Optional[Dict] = None,
        cnn_confidence: Optional[float] = None,
        county: Optional[str] = None,
    ) -> Dict:
        """
        Get treatment plan combining:
          1. TREATMENT_CATALOG baseline (deterministic, always available)
          2. Gemini AI refinement (contextual, using sensor/satellite/CNN data)

        Gemini considers:
          - Specific crop being grown
          - IoT sensor readings (pH, NPK, moisture, temperature)
          - Satellite data (NDVI, NDWI, rainfall)
          - CNN classification confidence
          - Kenyan agro-ecological zone (inferred from county)
          - Current season

        Returns:
            Same structure as get_treatment_plan() plus:
            - "ai_enhanced": True/False
            - "ai_analysis": str (Gemini's detailed analysis)
            - "ai_additional_recommendations": list
        """
        # Start with the catalog baseline
        catalog_plan = self.get_treatment_plan(condition, farm_size_acres, crops)

        # If Gemini not available, return catalog plan
        if not self.gemini_client:
            catalog_plan["ai_enhanced"] = False
            catalog_plan["ai_analysis"] = ""
            catalog_plan["ai_additional_recommendations"] = []
            return catalog_plan

        try:
            # Build Gemini prompt with all context
            prompt = self._build_ai_treatment_prompt(
                condition=condition,
                catalog_plan=catalog_plan,
                farm_size_acres=farm_size_acres,
                crops=crops,
                sensor_data=sensor_data,
                satellite_data=satellite_data,
                cnn_confidence=cnn_confidence,
                county=county,
            )

            config = genai_types.GenerateContentConfig(
                temperature=0.3,  # low temp for accuracy
                max_output_tokens=1500,
            )

            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=config,
            )
            raw = (response.text or "").strip()

            # Parse the JSON from Gemini
            ai_result = self._parse_ai_treatment_response(raw)

            # Merge AI insights into catalog plan
            if ai_result.get("analysis"):
                catalog_plan["ai_enhanced"] = True
                catalog_plan["ai_analysis"] = ai_result["analysis"]
                catalog_plan["ai_additional_recommendations"] = ai_result.get("additional_recommendations", [])
                catalog_plan["ai_urgency_override"] = ai_result.get("urgency_override", "")
                catalog_plan["ai_dosage_adjustments"] = ai_result.get("dosage_adjustments", [])
                catalog_plan["ai_warnings"] = ai_result.get("warnings", [])
                catalog_plan["ai_alternative_treatments"] = ai_result.get("alternative_treatments", [])

                # Override urgency if AI recommends higher urgency
                ai_urgency = ai_result.get("urgency_override", "")
                if ai_urgency and self._urgency_rank(ai_urgency) > self._urgency_rank(catalog_plan.get("urgency", "")):
                    catalog_plan["urgency"] = ai_urgency

                # Add AI-recommended dosage adjustments as notes on treatments
                for adj in ai_result.get("dosage_adjustments", []):
                    product_name = adj.get("product", "").lower()
                    for t in catalog_plan.get("treatments", []):
                        if any(product_name in n.lower() for n in t.get("names", [])):
                            t["ai_dose_note"] = adj.get("note", "")
                            if adj.get("adjusted_dose"):
                                t["ai_adjusted_dose"] = adj["adjusted_dose"]

                logger.info(f"AI treatment plan generated for {condition}")
            else:
                catalog_plan["ai_enhanced"] = False
                catalog_plan["ai_analysis"] = ""
                catalog_plan["ai_additional_recommendations"] = []

        except Exception as e:
            logger.warning(f"AI treatment plan failed for {condition}: {e} — using catalog")
            catalog_plan["ai_enhanced"] = False
            catalog_plan["ai_analysis"] = ""
            catalog_plan["ai_additional_recommendations"] = []

        return catalog_plan

    def _build_ai_treatment_prompt(
        self,
        condition: str,
        catalog_plan: Dict,
        farm_size_acres: float,
        crops: Optional[List[str]],
        sensor_data: Optional[Dict],
        satellite_data: Optional[Dict],
        cnn_confidence: Optional[float],
        county: Optional[str],
    ) -> str:
        """Build a detailed Gemini prompt for AI treatment plan refinement."""

        # Determine season
        month = datetime.now().month
        if month in (3, 4, 5):
            season = "Long rains season (March-May)"
        elif month in (6, 7, 8):
            season = "Cool dry season (June-August)"
        elif month in (10, 11, 12):
            season = "Short rains season (October-December)"
        else:
            season = "Hot dry season (January-February)"

        prompt = f"""You are an expert Kenyan agricultural extension officer and plant pathologist.
A farmer needs a treatment plan for: **{catalog_plan.get('display_name', condition)}**

## Context
- **Farm size:** {farm_size_acres} acres
- **Crops grown:** {', '.join(crops) if crops else 'Not specified'}
- **County:** {county or 'Not specified'}
- **Season:** {season}
- **CNN confidence:** {f'{cnn_confidence:.1%}' if cnn_confidence else 'N/A'}

"""

        if sensor_data:
            prompt += "## IoT Sensor Readings\n"
            sensor_labels = {
                "soil_nitrogen": ("Soil Nitrogen", "mg/kg"),
                "soil_phosphorus": ("Soil Phosphorus", "mg/kg"),
                "soil_potassium": ("Soil Potassium", "mg/kg"),
                "soil_ph": ("Soil pH", ""),
                "soil_moisture_pct": ("Soil Moisture", "%"),
                "temperature": ("Temperature", "°C"),
                "humidity": ("Humidity", "%"),
            }
            for key, val in sensor_data.items():
                if val is not None:
                    label, unit = sensor_labels.get(key, (key.replace("_", " ").title(), ""))
                    prompt += f"- {label}: {val}{unit}\n"
            prompt += "\n"

        if satellite_data:
            prompt += "## Satellite Data\n"
            sat_labels = {
                "ndvi": "NDVI (vegetation index)",
                "ndwi": "NDWI (water index)",
                "rainfall_mm": "Recent rainfall (mm)",
                "lst_celsius": "Land Surface Temperature (°C)",
            }
            for key, val in satellite_data.items():
                if val is not None:
                    label = sat_labels.get(key, key.replace("_", " ").title())
                    prompt += f"- {label}: {val}\n"
            prompt += "\n"

        # Include catalog baseline
        prompt += "## Catalog Baseline Treatment Plan\n"
        for t in catalog_plan.get("treatments", []):
            prompt += f"- **{t['names'][0]}**: {t.get('dose_for_farm', t['dose_per_acre'])} — {t['application']}\n"
        prompt += "\n"

        prompt += """## Your Task
Based on ALL the above context (sensor data, satellite data, crop type, location, season), provide an ACCURATE treatment recommendation.

Respond ONLY with valid JSON (no markdown code block):
{
    "analysis": "2-3 sentence expert analysis of the situation considering all telemetry data",
    "urgency_override": "low|medium|high|critical (only if different from catalog)",
    "dosage_adjustments": [
        {"product": "product name", "adjusted_dose": "new dose for this farm", "note": "reason for adjustment"}
    ],
    "additional_recommendations": [
        "recommendation 1 specific to the sensor/satellite context",
        "recommendation 2"
    ],
    "alternative_treatments": [
        {"name": "alternative product name", "reason": "why this might be better given the context"}
    ],
    "warnings": [
        "any warnings based on sensor data (e.g., do NOT apply if soil is too wet)"
    ]
}

Important:
- Dosages must be for the ENTIRE farm ({farm_size_acres} acres), not per-acre
- Consider Kenyan market availability and pricing
- Factor in sensor readings for interaction effects (e.g., low pH affects fertilizer efficacy)
- If satellite shows recent rainfall, warn about pesticide wash-off
- If CNN confidence is low (<60%), suggest visual re-inspection"""

        return prompt

    def _parse_ai_treatment_response(self, raw_text: str) -> Dict:
        """Parse Gemini's JSON response, handling edge cases."""
        # Strip markdown code blocks if present
        text_clean = raw_text.strip()
        if text_clean.startswith("```"):
            text_clean = text_clean.split("\n", 1)[-1]
        if text_clean.endswith("```"):
            text_clean = text_clean.rsplit("```", 1)[0]
        text_clean = text_clean.strip()

        try:
            return json.loads(text_clean)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', text_clean)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            # Fallback: use the raw text as analysis
            return {"analysis": raw_text[:500] if raw_text else "", "additional_recommendations": []}

    @staticmethod
    def _urgency_rank(level: str) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(level.lower(), 0)

    # ------------------------------------------------------------------ #
    #  2. Find nearest agrovets with matching products
    # ------------------------------------------------------------------ #

    def find_nearest_agrovets(
        self,
        county: str,
        sub_county: Optional[str] = None,
        product_names: Optional[List[str]] = None,
        category: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict]:
        """
        Search for agrovets near the farmer, prioritizing:
          1. Same sub-county
          2. Same county
          3. Neighboring area

        If product_names provided, filters to agrovets stocking those items.

        Returns list of agrovet dicts with products, prices, contact info.
        """
        if not DB_AVAILABLE:
            return []

        try:
            with get_sync_session() as session:  # type: ignore[misc]
                # Find agrovet profiles in the same county/sub_county
                stmt = (
                    select(AgrovetProfile, Farmer)
                    .join(Farmer, AgrovetProfile.user_id == Farmer.id)  # type: ignore[arg-type]
                    .where(AgrovetProfile.active == True)  # noqa: E712
                )

                # Prioritize sub_county match, fall back to county
                if sub_county:
                    stmt_sub = stmt.where(AgrovetProfile.shop_sub_county == sub_county)
                    results = session.exec(stmt_sub).all()
                    if not results:
                        # Fall back to county level
                        stmt_county = stmt.where(AgrovetProfile.shop_county == county)
                        results = session.exec(stmt_county.limit(limit)).all()
                else:
                    stmt_county = stmt.where(AgrovetProfile.shop_county == county)
                    results = session.exec(stmt_county.limit(limit)).all()

                agrovets = []
                for profile, farmer in results:
                    # Get products stocked by this agrovet
                    products_stmt = (
                        select(AgrovetProduct)
                        .where(AgrovetProduct.agrovet_id == farmer.id)
                        .where(AgrovetProduct.active == True)
                        .where(AgrovetProduct.in_stock == True)
                    )

                    if category:
                        products_stmt = products_stmt.where(AgrovetProduct.category == category)

                    products = session.exec(products_stmt).all()

                    # If specific product names requested, filter to matching
                    matching_products = []
                    if product_names:
                        name_lower = [n.lower() for n in product_names]
                        for p in products:
                            if any(n in p.name.lower() for n in name_lower):
                                matching_products.append(p)
                    else:
                        matching_products = list(products)

                    agrovets.append({
                        "agrovet_id": profile.id,
                        "user_id": farmer.id,
                        "shop_name": profile.shop_name,
                        "shop_county": profile.shop_county,
                        "shop_sub_county": profile.shop_sub_county,
                        "shop_address": profile.shop_address,
                        "phone": farmer.phone,
                        "mpesa_till": profile.mpesa_till_number,
                        "mpesa_paybill": profile.mpesa_paybill,
                        "is_verified": profile.is_verified,
                        "average_rating": profile.average_rating,
                        "products": [
                            {
                                "id": p.id,
                                "name": p.name,
                                "name_sw": p.name_sw,
                                "category": p.category,
                                "price_kes": float(p.price_kes),
                                "unit": p.unit,
                                "in_stock": p.in_stock,
                                "stock_quantity": p.stock_quantity,
                            }
                            for p in matching_products[:10]
                        ],
                        "total_products": len(matching_products),
                    })

                # Sort: sub_county match first, then by rating
                if sub_county:
                    agrovets.sort(key=lambda a: (
                        0 if a["shop_sub_county"] == sub_county else 1,
                        -(a["average_rating"] or 0),
                    ))

                return agrovets[:limit]

        except Exception as e:
            logger.error(f"Agrovet search error: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  3. Search products across all agrovets by name/category
    # ------------------------------------------------------------------ #

    def search_products(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        county: Optional[str] = None,
        sub_county: Optional[str] = None,
        crop: Optional[str] = None,
        max_results: int = 20,
    ) -> List[Dict]:
        """
        Search for specific products across all agrovets, optionally filtered
        by location. Returns products sorted: sub_county → county → all.
        """
        if not DB_AVAILABLE:
            return []

        try:
            with get_sync_session() as session:
                stmt = (
                    select(AgrovetProduct)
                    .where(AgrovetProduct.active == True)
                    .where(AgrovetProduct.in_stock == True)
                )

                if category:
                    stmt = stmt.where(AgrovetProduct.category == category)
                if county:
                    stmt = stmt.where(AgrovetProduct.supplier_county == county)

                products = session.exec(stmt.limit(100)).all()

                # Filter by name query
                if query:
                    q_lower = query.lower()
                    products = [p for p in products if q_lower in p.name.lower()
                                or (p.description and q_lower in p.description.lower())]

                # Filter by applicable crop
                if crop:
                    products = [p for p in products if p.crop_applicable and crop in p.crop_applicable]

                # Sort by proximity (sub_county → county → other)
                def sort_key(p):
                    if sub_county and p.supplier_county == county:
                        # Check if supplier_location contains sub_county
                        loc = (p.supplier_location or "").lower()
                        if sub_county.lower() in loc:
                            return 0
                        return 1
                    return 2

                products = list(products)  # type: ignore[arg-type]
                products.sort(key=sort_key)

                return [
                    {
                        "id": p.id,
                        "name": p.name,
                        "name_sw": p.name_sw,
                        "description": p.description,
                        "category": p.category,
                        "price_kes": float(p.price_kes),
                        "unit": p.unit,
                        "in_stock": p.in_stock,
                        "stock_quantity": p.stock_quantity,
                        "supplier_name": p.supplier_name,
                        "supplier_location": p.supplier_location,
                        "supplier_county": p.supplier_county,
                        "crop_applicable": p.crop_applicable,
                    }
                    for p in products[:max_results]
                ]

        except Exception as e:
            logger.error(f"Product search error: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  4. FULL PIPELINE: condition → treatment → nearest shop → purchase
    # ------------------------------------------------------------------ #

    def recommend_for_condition(
        self,
        condition: str,
        farmer_data: Dict,
        sensor_data: Optional[Dict] = None,
        satellite_data: Optional[Dict] = None,
    ) -> Dict:
        """
        Complete recommendation pipeline:
          1. Get treatment plan with scaled doses
          2. Find nearest agrovets with matching products
          3. Calculate estimated cost
          4. Return structured recommendation + purchase links

        Args:
            condition: "leaf_blight", "nitrogen_low", etc.
            farmer_data: {name, phone, county, sub_county, farm_size, crops, language}
            sensor_data: optional IoT readings for context
            satellite_data: optional NDVI/NDWI for context

        Returns:
            {
                "condition": "leaf_blight",
                "treatment_plan": {...},
                "nearest_agrovets": [...],
                "recommended_products": [...],
                "estimated_cost_kes": {"min": 500, "max": 2500},
                "purchase_options": {...},
                "sms_summary": "...",
                "web_summary": "...",
            }
        """
        county = farmer_data.get("county", "")
        sub_county = farmer_data.get("sub_county", "")
        farm_size = farmer_data.get("farm_size", 1.0) or 1.0
        crops = farmer_data.get("crops", [])
        language = farmer_data.get("language", "en")
        name = farmer_data.get("name", "Farmer")

        # 1. Treatment plan — use AI-enhanced if Gemini available
        if self.gemini_client and (sensor_data or satellite_data):
            plan = self.get_ai_treatment_plan(
                condition=condition,
                farm_size_acres=farm_size,
                crops=crops,
                sensor_data=sensor_data,
                satellite_data=satellite_data,
                county=county,
            )
        else:
            plan = self.get_treatment_plan(condition, farm_size, crops)

        # 2. Collect all product names from treatments
        all_product_names = []
        all_categories = set()
        for t in plan.get("treatments", []):
            all_product_names.extend(t.get("names", []))
            all_categories.add(t.get("product_category", ""))

        # 3. Find nearest agrovets with these products
        agrovets = self.find_nearest_agrovets(
            county=county,
            sub_county=sub_county,
            product_names=all_product_names,
            limit=3,
        )

        # 4. Also search products directly
        recommended_products = []
        for product_name in all_product_names[:5]:
            matches = self.search_products(
                query=product_name,
                county=county,
                max_results=3,
            )
            recommended_products.extend(matches)

        # Deduplicate by product id
        seen_ids = set()
        unique_products = []
        for p in recommended_products:
            if p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                unique_products.append(p)
        recommended_products = unique_products[:10]

        # 5. Estimated cost range
        if recommended_products:
            prices = [p["price_kes"] for p in recommended_products]
            cost_range = {
                "min": round(min(prices), 2),
                "max": round(sum(sorted(prices)[:3]), 2),  # top 3 products
                "currency": "KES",
            }
        else:
            cost_range = {"min": 0, "max": 0, "currency": "KES", "note": "No products found in area"}

        # 6. Generate summaries
        sms_summary = self._build_sms_summary(plan, agrovets, language, name)
        web_summary = self._build_web_summary(plan, agrovets, recommended_products, cost_range, farmer_data)

        return {
            "condition": condition,
            "treatment_plan": plan,
            "nearest_agrovets": agrovets,
            "recommended_products": recommended_products,
            "estimated_cost_kes": cost_range,
            "purchase_options": {
                "web": f"/agrovet/products?condition={condition}&county={county}",
                "ussd": f"Dial *384*SHAMBA# → Menu 5 → {plan['display_name']}",
                "sms": f"SMS 'BUY {condition.upper()}' to 20880",
            },
            "sms_summary": sms_summary,
            "web_summary": web_summary,
        }

    # ------------------------------------------------------------------ #
    #  5. Process system_action from Flora AI
    # ------------------------------------------------------------------ #

    def process_system_action(self, system_action: Dict, farmer_data: Dict) -> Optional[Dict]:
        """
        Process a [SYSTEM_ACTION] JSON block from Flora AI and execute
        the agrovet query / recommendation.

        Common action_types:
          - "agrovet_query": search products by item/category
          - "disease_treatment": full treatment recommendation
          - "schedule_followup": schedule a follow-up check
          - "alert_escalation": escalate to extension officer
        """
        action_type = system_action.get("action_type", "")

        if action_type in ("agrovet_query", "disease_treatment"):
            condition = system_action.get("disease") or system_action.get("item", "")
            if condition:
                return self.recommend_for_condition(condition, farmer_data)

        elif action_type == "product_search":
            return {
                "products": self.search_products(
                    query=system_action.get("item"),
                    category=system_action.get("category"),
                    county=farmer_data.get("county"),
                    sub_county=farmer_data.get("sub_county"),
                ),
            }

        return None

    # ------------------------------------------------------------------ #
    #  6. Create order from recommendation
    # ------------------------------------------------------------------ #

    def create_order_from_recommendation(
        self,
        farmer_id: int,
        product_id: int,
        quantity: int,
        payment_method: str = "mpesa",
        order_source: str = "web",
    ) -> Dict:
        """
        Create an agrovet order triggered by a disease/deficiency recommendation.

        Returns:
            {"success": True, "order_id": 123, "total_kes": 5000, "order_number": "ORD-..."}
        """
        if not DB_AVAILABLE:
            return {"success": False, "error": "Database not available"}

        try:
            import uuid as _uuid
            with get_sync_session() as session:
                product = session.get(AgrovetProduct, product_id)  # type: ignore[arg-type]
                if not product:
                    return {"success": False, "error": "Product not found"}
                if not product.in_stock:
                    return {"success": False, "error": "Product out of stock"}

                total = Decimal(str(float(product.price_kes) * quantity))
                order_number = f"ORD-{_uuid.uuid4().hex[:8].upper()}"

                order = AgrovetOrder(
                    order_number=order_number,
                    farmer_id=farmer_id,
                    agrovet_id=product.agrovet_id,
                    product_id=product_id,
                    quantity=quantity,
                    total_price_kes=total,
                    payment_method=payment_method,
                    order_source=order_source,
                    notes=f"Auto-recommended based on farm condition analysis",
                )
                session.add(order)
                session.commit()
                session.refresh(order)

                return {
                    "success": True,
                    "order_id": order.id,
                    "order_number": order_number,
                    "total_kes": float(total),
                    "product_name": product.name,
                    "payment_method": payment_method,
                }

        except Exception as e:
            logger.error(f"Order creation error: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------ #
    #  Summary builders
    # ------------------------------------------------------------------ #

    def _build_sms_summary(
        self, plan: Dict, agrovets: List[Dict], language: str, name: str,
    ) -> str:
        """Build concise SMS summary (≤160 chars)."""
        display = plan.get("display_name", "issue")
        urgency = plan.get("urgency", "")
        treatments = plan.get("treatments", [])

        if language == "sw":
            msg = f"⚠️ {name}, {plan.get('display_name_sw', display)} imegunduliwa!"
            if treatments:
                msg += f" Tumia {treatments[0]['names'][0]}"
                msg += f" ({treatments[0].get('dose_for_farm', '')})"
            if agrovets:
                msg += f". {agrovets[0]['shop_name']} ina hiyo."
            return msg[:160]
        else:
            msg = f"⚠️ {name}, {display} detected!"
            if treatments:
                msg += f" Apply {treatments[0]['names'][0]}"
                msg += f" ({treatments[0].get('dose_for_farm', '')})"
            if agrovets:
                msg += f". Available at {agrovets[0]['shop_name']}."
            return msg[:160]

    def _build_web_summary(
        self, plan: Dict, agrovets: List[Dict],
        products: List[Dict], cost_range: Dict, farmer_data: Dict,
    ) -> str:
        """Build detailed web dashboard summary (markdown)."""
        display = plan.get("display_name", "Issue Detected")
        urgency = plan.get("urgency", "medium")
        urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(urgency, "ℹ️")
        farm_size = farmer_data.get("farm_size", 1.0) or 1.0

        lines = [
            f"## {urgency_emoji} {display}",
            f"**Urgency:** {urgency.upper()}",
            f"**Farm Size:** {farm_size} acres",
            "",
            plan.get("description", ""),
            "",
        ]

        # AI analysis section (if available)
        if plan.get("ai_enhanced"):
            lines.append("### 🤖 AI Expert Analysis")
            lines.append(plan.get("ai_analysis", ""))
            lines.append("")
            if plan.get("ai_warnings"):
                lines.append("**⚠️ Warnings:**")
                for w in plan["ai_warnings"]:
                    lines.append(f"- {w}")
                lines.append("")

        lines.append("### Recommended Treatments")

        for i, t in enumerate(plan.get("treatments", []), 1):
            lines.append(f"\n**Option {i}: {t['names'][0]}**")
            lines.append(f"- Category: {t['product_category'].replace('_', ' ').title()}")
            lines.append(f"- Dose for your farm: **{t.get('dose_for_farm', t['dose_per_acre'])}**")
            if t.get("ai_adjusted_dose"):
                lines.append(f"- 🤖 AI-adjusted dose: **{t['ai_adjusted_dose']}**")
            if t.get("ai_dose_note"):
                lines.append(f"- 🤖 Note: {t['ai_dose_note']}")
            lines.append(f"- Application: {t['application']}")
            lines.append(f"- ⚠️ {t['notes']}")
            if len(t['names']) > 1:
                lines.append(f"- Alternatives: {', '.join(t['names'][1:])}")

        # AI alternative treatments
        if plan.get("ai_alternative_treatments"):
            lines.append("\n### 🤖 AI-Suggested Alternatives")
            for alt in plan["ai_alternative_treatments"]:
                lines.append(f"- **{alt.get('name', '')}**: {alt.get('reason', '')}")

        if plan.get("cultural_practices"):
            lines.append("\n### Cultural Practices (No Cost)")
            for cp in plan["cultural_practices"]:
                lines.append(f"- {cp}")

        # AI additional recommendations
        if plan.get("ai_additional_recommendations"):
            lines.append("\n### 🤖 Additional Recommendations")
            for rec in plan["ai_additional_recommendations"]:
                lines.append(f"- {rec}")

        if agrovets:
            lines.append("\n### Nearest Agrovets")
            for a in agrovets:
                lines.append(f"\n**{a['shop_name']}** {'✅ Verified' if a['is_verified'] else ''}")
                lines.append(f"- Location: {a.get('shop_sub_county', '')}, {a.get('shop_county', '')}")
                lines.append(f"- Phone: {a['phone']}")
                if a.get("mpesa_till"):
                    lines.append(f"- M-Pesa Till: {a['mpesa_till']}")
                if a["products"]:
                    for p in a["products"][:3]:
                        lines.append(f"  - {p['name']}: **KES {p['price_kes']:,.0f}** per {p['unit']}")

        if cost_range.get("max", 0) > 0:
            lines.append(f"\n### Estimated Cost")
            lines.append(f"**KES {cost_range['min']:,.0f} — {cost_range['max']:,.0f}**")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  Self-test
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🏪 Agrovet Recommendation Service — Self Test")
    print("=" * 60)

    svc = AgrovetRecommendationService()

    # Test treatment plan
    plan = svc.get_treatment_plan("leaf_blight", farm_size_acres=3.0)
    print(f"\nTreatment plan for leaf_blight (3 acres):")
    print(f"  Display: {plan['display_name']}")
    print(f"  Urgency: {plan['urgency']}")
    print(f"  Treatments: {len(plan['treatments'])}")
    for t in plan["treatments"]:
        print(f"    - {t['names'][0]}: {t['dose_for_farm']}")

    # Test deficiency detection
    sensor = {"soil_nitrogen": 12, "soil_ph": 4.8, "soil_moisture_pct": 30}
    deficiencies = detect_deficiencies_from_sensors(sensor)
    print(f"\nSensor deficiencies detected: {len(deficiencies)}")
    for d in deficiencies:
        print(f"  - {d['display_name']}: value={d['value']}, severity={d['severity']}")

    # Test full recommendation
    farmer = {
        "name": "John Kamau",
        "phone": "+254712345678",
        "county": "Kiambu",
        "sub_county": "Githunguri",
        "farm_size": 5.0,
        "crops": ["maize", "beans"],
        "language": "en",
    }
    rec = svc.recommend_for_condition("leaf_blight", farmer)
    print(f"\nFull recommendation:")
    print(f"  Agrovets found: {len(rec['nearest_agrovets'])}")
    print(f"  Products found: {len(rec['recommended_products'])}")
    print(f"  Cost range: {rec['estimated_cost_kes']}")
    print(f"\n  SMS: {rec['sms_summary']}")

    print("\n✓ Agrovet service test complete!")
