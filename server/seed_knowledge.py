#!/usr/bin/env python3
"""
Seed the ag_knowledge table with agricultural threshold knowledge.

Each entry gets a 384-dim embedding via sentence-transformers/all-MiniLM-L6-v2
so the RAG system can retrieve relevant advice when smart alerts fire.

Usage:
    python seed_knowledge.py          # seed all entries
    python seed_knowledge.py --check  # just count existing entries
"""
import sys, os, logging

# ── project root on sys.path ------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── knowledge corpus --------------------------------------------------------
# Category keys: threshold, optimal, pest_disease, seasonal, practice
# Each dict: doc_text, doc_category, crop (optional), region (optional), season (optional)

KNOWLEDGE_ENTRIES = [
    # ====================================================================
    # MAIZE
    # ====================================================================
    {
        "doc_text": (
            "Maize optimal soil pH is 5.5–7.0. When soil pH drops below 5.5, "
            "aluminium toxicity reduces root growth and nutrient uptake. "
            "Apply agricultural lime at 2–3 tonnes/ha and retest after 3 months. "
            "If pH exceeds 7.5, add elemental sulphur or organic matter to lower it."
        ),
        "doc_category": "threshold",
        "crop": "maize",
    },
    {
        "doc_text": (
            "Maize requires soil moisture between 50–80 % field capacity during "
            "the vegetative and tasseling stages. Below 40 %, wilting and leaf "
            "rolling begin; irrigation or mulching is needed. Above 90 %, "
            "waterlogging reduces oxygen to roots—improve drainage."
        ),
        "doc_category": "threshold",
        "crop": "maize",
    },
    {
        "doc_text": (
            "Maize grows best at 18–32 °C. Temperatures above 35 °C during "
            "pollination cause kernel abortion and poor cob fill. Below 10 °C, "
            "germination slows dramatically. In hot conditions, consider "
            "heat-tolerant varieties like DUMA 43 or WH505."
        ),
        "doc_category": "threshold",
        "crop": "maize",
    },
    {
        "doc_text": (
            "Ideal NDVI for healthy maize ranges from 0.3 to 0.9 during the "
            "growing season. NDVI below 0.2 indicates severe stress or bare soil. "
            "Between 0.2–0.3 suggests early stress—scout for pests, nutrient "
            "deficiency, or drought stress and take corrective action."
        ),
        "doc_category": "threshold",
        "crop": "maize",
    },
    {
        "doc_text": (
            "When all maize growing conditions are within optimal ranges "
            "(soil pH 5.5–7.0, moisture 50–80 %, temperature 18–32 °C, "
            "humidity 50–80 %, NDVI 0.3–0.9), the crop is on track for good "
            "yields. Continue current management practices and monitor weekly."
        ),
        "doc_category": "optimal",
        "crop": "maize",
    },
    {
        "doc_text": (
            "Fall armyworm (Spodoptera frugiperda) is the most damaging maize "
            "pest in Kenya. Early signs include windowing on young leaves and "
            "frass in the whorl. Apply Bt-based biopesticides or recommended "
            "insecticides within the first 2 weeks of infestation. Maize lethal "
            "necrosis disease (MLND) causes complete crop loss—use certified seed."
        ),
        "doc_category": "pest_disease",
        "crop": "maize",
    },
    {
        "doc_text": (
            "Maize in Kenya is best planted at the onset of the long rains "
            "(March–April) or short rains (October–November). Apply DAP at "
            "planting (50 kg/ha) and top-dress with CAN at knee height "
            "(50 kg/ha). Optimal rainfall for maize is 50–200 mm per month."
        ),
        "doc_category": "seasonal",
        "crop": "maize",
        "season": "long_rains",
    },

    # ====================================================================
    # COFFEE
    # ====================================================================
    {
        "doc_text": (
            "Coffee (Arabica) thrives in slightly acidic soil with pH 6.0–6.5. "
            "Below pH 5.5, iron and manganese toxicity occurs; apply dolomitic "
            "lime. Above pH 7.0, micronutrient lockout reduces berry quality. "
            "Test soil every 6 months in coffee plots."
        ),
        "doc_category": "threshold",
        "crop": "coffee",
    },
    {
        "doc_text": (
            "Coffee needs consistent soil moisture of 60–80 % field capacity. "
            "Water stress during flowering causes star flowers (aborted blossoms) "
            "and reduces yield by up to 50 %. Excess moisture promotes coffee "
            "berry disease (CBD). Mulch with 10 cm of organic material."
        ),
        "doc_category": "threshold",
        "crop": "coffee",
    },
    {
        "doc_text": (
            "Arabica coffee grows best at 15–24 °C. Above 30 °C, photosynthesis "
            "declines and sun-scorch damages leaves. Below 10 °C, growth stops. "
            "In warming climates, consider shade trees (Grevillea robusta) to "
            "moderate canopy temperature by 3–5 °C."
        ),
        "doc_category": "threshold",
        "crop": "coffee",
    },
    {
        "doc_text": (
            "When all coffee conditions are optimal (pH 6.0–6.5, moisture 60–80 %, "
            "temperature 15–24 °C, humidity 60–80 %, NDVI 0.4–0.8), the plantation "
            "is performing well. Maintain current fertilisation and shade management."
        ),
        "doc_category": "optimal",
        "crop": "coffee",
    },
    {
        "doc_text": (
            "Coffee berry disease (CBD) caused by Colletotrichum kahawae is the "
            "most serious coffee disease in Kenya. It thrives in cool, wet "
            "conditions. Apply copper-based fungicides preventively during "
            "flowering. Coffee leaf rust (Hemileia vastatrix) appears as orange "
            "pustules—use resistant varieties like Ruiru 11 or Batian."
        ),
        "doc_category": "pest_disease",
        "crop": "coffee",
    },

    # ====================================================================
    # TEA
    # ====================================================================
    {
        "doc_text": (
            "Tea requires strongly acidic soil with pH 4.5–5.5. Above pH 6.0, "
            "iron chlorosis causes yellowing leaves. Below pH 4.0, aluminium "
            "toxicity stunts root development. Apply sulphate of ammonia (SA) "
            "as the nitrogen source to help maintain acidity."
        ),
        "doc_category": "threshold",
        "crop": "tea",
    },
    {
        "doc_text": (
            "Tea needs consistent moisture of 70–90 % field capacity and cannot "
            "tolerate drought. Below 60 %, leaf production drops sharply and "
            "shoots become dormant. Irrigation via drip or sprinkler is needed "
            "in dry months. Excess waterlogging causes root rot (Armillaria)."
        ),
        "doc_category": "threshold",
        "crop": "tea",
    },
    {
        "doc_text": (
            "Tea grows best at 18–25 °C with high humidity (70–90 %). Below "
            "13 °C, growth ceases. Above 30 °C, leaf quality deteriorates and "
            "the plant enters stress. Kenya's highland areas (1500–2200 m ASL) "
            "provide ideal tea-growing microclimates."
        ),
        "doc_category": "threshold",
        "crop": "tea",
    },
    {
        "doc_text": (
            "When tea conditions are optimal (pH 4.5–5.5, moisture 70–90 %, "
            "temperature 18–25 °C, humidity 70–90 %, NDVI 0.5–0.85), expect "
            "healthy flush growth. Maintain plucking rounds every 7–10 days."
        ),
        "doc_category": "optimal",
        "crop": "tea",
    },
    {
        "doc_text": (
            "Tea mosquito bug (Helopeltis schoutedeni) causes shoot damage and "
            "yield loss of 20–50 %. Blister blight (Exobasidium vexans) appears "
            "as translucent blisters on young leaves during wet weather. "
            "Apply systemic insecticides and copper fungicides as recommended by TRFK."
        ),
        "doc_category": "pest_disease",
        "crop": "tea",
    },

    # ====================================================================
    # RICE
    # ====================================================================
    {
        "doc_text": (
            "Rice optimal soil pH is 5.5–7.0. In flooded paddy conditions, pH "
            "tends to converge toward 6.5–7.0 regardless of initial soil pH. "
            "For upland rice, lime if pH < 5.0. Iron toxicity (bronzing) occurs "
            "in acidic, poorly drained soils—improve drainage and add lime."
        ),
        "doc_category": "threshold",
        "crop": "rice",
    },
    {
        "doc_text": (
            "Rice needs 60–85 % soil moisture (upland) or standing water "
            "(paddy). Moisture stress during booting and heading reduces grain "
            "fill by 30–60 %. In Mwea Irrigation Scheme, maintain 5–10 cm "
            "standing water from transplanting to 2 weeks before harvest."
        ),
        "doc_category": "threshold",
        "crop": "rice",
    },
    {
        "doc_text": (
            "Rice grows best at 20–35 °C. Temperatures below 15 °C cause cold "
            "sterility and poor germination in the nursery. Above 40 °C, "
            "spikelet sterility increases. Kenya's Mwea and Ahero schemes "
            "provide suitable thermal regimes."
        ),
        "doc_category": "threshold",
        "crop": "rice",
    },
    {
        "doc_text": (
            "When rice conditions are optimal (pH 5.5–7.0, moisture 60–85 %, "
            "temperature 20–35 °C, humidity 60–85 %, NDVI 0.3–0.85), the crop "
            "is developing normally. Maintain water management schedules."
        ),
        "doc_category": "optimal",
        "crop": "rice",
    },

    # ====================================================================
    # BEANS
    # ====================================================================
    {
        "doc_text": (
            "Common beans grow best at soil pH 6.0–7.0. Below pH 5.5, "
            "Rhizobium nodulation is impaired and nitrogen fixation drops. "
            "Apply lime to raise pH. Above pH 7.5, zinc and iron deficiency "
            "symptoms appear—apply foliar micronutrient sprays."
        ),
        "doc_category": "threshold",
        "crop": "beans",
    },
    {
        "doc_text": (
            "Beans need soil moisture of 50–70 % field capacity. They are "
            "drought-sensitive during flowering and pod filling. Excess moisture "
            "promotes root rot (Pythium, Fusarium). Avoid waterlogged fields. "
            "Rainfall of 40–160 mm/month is ideal for rainfed beans."
        ),
        "doc_category": "threshold",
        "crop": "beans",
    },
    {
        "doc_text": (
            "Beans grow optimally at 16–28 °C. Below 12 °C, germination is "
            "very slow and flower abortion occurs. Above 32 °C, pollen "
            "viability drops. In Kenya, beans are grown from 900–2200 m ASL."
        ),
        "doc_category": "threshold",
        "crop": "beans",
    },
    {
        "doc_text": (
            "When bean conditions are optimal (pH 6.0–7.0, moisture 50–70 %, "
            "temperature 16–28 °C, humidity 50–70 %, NDVI 0.3–0.8), expect "
            "good pod set and fill. Scout for angular leaf spot and anthracnose."
        ),
        "doc_category": "optimal",
        "crop": "beans",
    },
    {
        "doc_text": (
            "Bean stem maggot (Ophiomyia spp.) is a major pest in Kenya beans, "
            "causing seedling death. Treat seed with imidacloprid before planting. "
            "Angular leaf spot and anthracnose are controlled with copper-based "
            "fungicides and certified disease-free seed (e.g., KAT B1, GLP 2)."
        ),
        "doc_category": "pest_disease",
        "crop": "beans",
    },

    # ====================================================================
    # WHEAT
    # ====================================================================
    {
        "doc_text": (
            "Wheat grows best at soil pH 6.0–7.5. Acidic soils below pH 5.5 "
            "cause aluminium toxicity; lime before planting. Wheat is more "
            "tolerant of alkaline conditions than most cereals, but pH above "
            "8.0 causes zinc and phosphorus deficiency."
        ),
        "doc_category": "threshold",
        "crop": "wheat",
    },
    {
        "doc_text": (
            "Wheat requires soil moisture of 45–65 % field capacity. It is "
            "sensitive to waterlogging, especially at tillering. Drought stress "
            "during heading and grain filling reduces yield. In Kenya, wheat "
            "is largely rainfed in Narok and Uasin Gishu; rainfall of 40–120 "
            "mm/month is suitable."
        ),
        "doc_category": "threshold",
        "crop": "wheat",
    },
    {
        "doc_text": (
            "Wheat thrives at 12–25 °C. Below 5 °C, frost damage kills tillers. "
            "Above 30 °C during grain fill, heat stress causes shrivelled kernels. "
            "Choose varieties adapted to Kenya highlands: Kenya Fahari, Eagle 10."
        ),
        "doc_category": "threshold",
        "crop": "wheat",
    },
    {
        "doc_text": (
            "When wheat conditions are optimal (pH 6.0–7.5, moisture 45–65 %, "
            "temperature 12–25 °C, humidity 40–65 %, NDVI 0.25–0.85), the crop "
            "is developing well. Monitor for stem rust (Ug99) weekly."
        ),
        "doc_category": "optimal",
        "crop": "wheat",
    },
    {
        "doc_text": (
            "Stem rust (Puccinia graminis race Ug99) is the most devastating "
            "wheat disease in Kenya. Spray Propiconazole or Tebuconazole at "
            "first sign of pustules. Septoria leaf blotch thrives in cool, wet "
            "weather—use resistant varieties and rotate fungicide modes of action."
        ),
        "doc_category": "pest_disease",
        "crop": "wheat",
    },

    # ====================================================================
    # SUGARCANE
    # ====================================================================
    {
        "doc_text": (
            "Sugarcane optimal soil pH is 5.5–7.5. Below 5.0, calcium and "
            "molybdenum deficiency occur; apply calcitic lime. Sugarcane tolerates "
            "mildly alkaline soils but above pH 8.0, iron chlorosis appears. "
            "Apply ferrous sulphate foliar spray."
        ),
        "doc_category": "threshold",
        "crop": "sugarcane",
    },
    {
        "doc_text": (
            "Sugarcane is a heavy water user requiring 60–85 % soil moisture and "
            "100–250 mm rainfall per month in the active growth phase. Water "
            "stress during the grand growth period (4–8 months) severely reduces "
            "cane tonnage. In western Kenya, supplemental irrigation is recommended "
            "during dry spells."
        ),
        "doc_category": "threshold",
        "crop": "sugarcane",
    },
    {
        "doc_text": (
            "Sugarcane grows best at 20–35 °C. Below 15 °C, growth stops and "
            "maturation is accelerated (sometimes desired). Above 38 °C, heat "
            "stress causes leaf tip burning. Night temperatures should ideally "
            "drop to 15–20 °C to promote sucrose accumulation."
        ),
        "doc_category": "threshold",
        "crop": "sugarcane",
    },
    {
        "doc_text": (
            "When sugarcane conditions are optimal (pH 5.5–7.5, moisture 60–85 %, "
            "temperature 20–35 °C, humidity 55–85 %, NDVI 0.3–0.85), the cane "
            "is growing vigorously. Maintain trash mulch and inter-row cultivation."
        ),
        "doc_category": "optimal",
        "crop": "sugarcane",
    },

    # ====================================================================
    # POTATOES
    # ====================================================================
    {
        "doc_text": (
            "Potatoes prefer slightly acidic soil with pH 5.0–6.5. Below pH 4.5, "
            "aluminium toxicity stunts growth. Above pH 7.0, common scab "
            "(Streptomyces scabies) incidence increases sharply—do NOT lime "
            "potato fields above pH 6.5. Apply sulphur to lower pH if needed."
        ),
        "doc_category": "threshold",
        "crop": "potatoes",
    },
    {
        "doc_text": (
            "Potatoes need consistent moisture of 60–80 % field capacity. Water "
            "stress during tuber initiation and bulking causes misshapen tubers "
            "and hollow heart. Excess moisture promotes late blight. In Nyandarua "
            "and Meru counties, supplement rainfall with drip irrigation."
        ),
        "doc_category": "threshold",
        "crop": "potatoes",
    },
    {
        "doc_text": (
            "Potatoes grow best at 15–22 °C. Above 25 °C, tuber initiation fails "
            "and the plant produces only foliage (heat sprouting). Below 7 °C, "
            "frost kills foliage. Kenya's potato zones (1800–3000 m ASL) provide "
            "suitable cool temperatures."
        ),
        "doc_category": "threshold",
        "crop": "potatoes",
    },
    {
        "doc_text": (
            "When potato conditions are optimal (pH 5.0–6.5, moisture 60–80 %, "
            "temperature 15–22 °C, humidity 60–80 %, NDVI 0.3–0.85), expect good "
            "tuber development. Hill up soil around stems at 4 and 8 weeks."
        ),
        "doc_category": "optimal",
        "crop": "potatoes",
    },
    {
        "doc_text": (
            "Late blight (Phytophthora infestans) is the most destructive potato "
            "disease in Kenya, especially at high humidity (>80 %) and 15–22 °C. "
            "Apply Mancozeb + Metalaxyl preventively every 7–10 days. Use "
            "certified seed from KALRO or ADC. Bacterial wilt (Ralstonia "
            "solanacearum) is soil-borne—rotate with non-solanaceous crops."
        ),
        "doc_category": "pest_disease",
        "crop": "potatoes",
    },

    # ====================================================================
    # SORGHUM
    # ====================================================================
    {
        "doc_text": (
            "Sorghum is tolerant of a wide pH range (5.5–8.5) and is more "
            "acid-tolerant than maize. However, below pH 5.0, aluminium toxicity "
            "reduces root growth. Sorghum is an excellent choice for alkaline "
            "soils where other cereals struggle."
        ),
        "doc_category": "threshold",
        "crop": "sorghum",
    },
    {
        "doc_text": (
            "Sorghum is drought-tolerant and needs only 35–60 % soil moisture. "
            "It can survive dry spells through leaf rolling and waxy bloom on "
            "stems. However, moisture stress during booting and flowering still "
            "reduces yield. Rainfall of 30–150 mm/month is adequate."
        ),
        "doc_category": "threshold",
        "crop": "sorghum",
    },
    {
        "doc_text": (
            "Sorghum grows best at 25–35 °C and is more heat-tolerant than maize. "
            "Below 15 °C, germination is poor and seedlings are susceptible to "
            "damping off. Above 40 °C, pollen viability drops. Suited to lower "
            "elevation, drier parts of Kenya (Eastern, Coast, Nyanza)."
        ),
        "doc_category": "threshold",
        "crop": "sorghum",
    },
    {
        "doc_text": (
            "When sorghum conditions are optimal (pH 5.5–8.5, moisture 35–60 %, "
            "temperature 25–35 °C, humidity 40–65 %, NDVI 0.25–0.8), the crop "
            "is performing well. Continue scouting for shoot fly and stem borer."
        ),
        "doc_category": "optimal",
        "crop": "sorghum",
    },
    {
        "doc_text": (
            "Sorghum shoot fly (Atherigona soccata) attacks within 2 weeks of "
            "emergence—deadheart symptoms. Plant early and use resistant varieties "
            "like Gadam. Striga (Striga hermonthica) is a parasitic weed that "
            "devastates sorghum in western Kenya. Intercrop with Desmodium "
            "(push-pull technology) and apply Imazapyr-coated seed."
        ),
        "doc_category": "pest_disease",
        "crop": "sorghum",
    },

    # ====================================================================
    # GENERAL / CROSS-CROP
    # ====================================================================
    {
        "doc_text": (
            "NDVI (Normalized Difference Vegetation Index) ranges from -1 to +1. "
            "Values 0.2–0.4 indicate sparse or stressed vegetation. Values "
            "0.4–0.6 indicate moderate vegetation. Values above 0.6 indicate "
            "dense, healthy canopy. NDVI below 0.2 in cropland suggests bare "
            "soil, harvest, or severe stress requiring immediate investigation."
        ),
        "doc_category": "threshold",
    },
    {
        "doc_text": (
            "NDWI (Normalized Difference Water Index) above 0.3 indicates "
            "abundant water or saturated conditions. Between 0.0–0.3 is normal "
            "crop moisture. Below -0.1 indicates dry conditions. NDWI is useful "
            "for detecting irrigation status and drought onset."
        ),
        "doc_category": "threshold",
    },
    {
        "doc_text": (
            "Soil pH is the single most important soil chemical property. It "
            "controls nutrient availability: below pH 5.5, phosphorus and "
            "molybdenum are locked up; above pH 7.5, iron, zinc, and manganese "
            "become unavailable. Regular soil testing every 6–12 months is "
            "essential for all crops in Kenya."
        ),
        "doc_category": "practice",
    },
    {
        "doc_text": (
            "Integrated Pest Management (IPM) combines biological control, "
            "cultural practices, and targeted chemical use. In Kenya, push-pull "
            "technology (Napier grass + Desmodium) controls stem borers and "
            "Striga in cereal crops while improving soil fertility."
        ),
        "doc_category": "practice",
    },
    {
        "doc_text": (
            "AfricasTalking SMS alerts for Kenyan farmers should be concise "
            "(max 160 chars if possible), bilingual (English + Swahili), and "
            "include specific actionable recommendations. Alert categories: "
            "optimal (good news), warning (single metric off), critical "
            "(multiple metrics off or severe deviation)."
        ),
        "doc_category": "practice",
    },
    {
        "doc_text": (
            "Kenya's long rains season (March–May) and short rains season "
            "(October–December) are the primary planting windows. Climate change "
            "is shifting these patterns—advise farmers to plant within 2 weeks of "
            "reliable rainfall onset. Monitor CHIRPS rainfall data via GEE."
        ),
        "doc_category": "seasonal",
        "season": "long_rains",
    },
    {
        "doc_text": (
            "Kenya's main agricultural regions and their specialities: "
            "Central (coffee, tea, potatoes), Western (sugarcane, maize), "
            "Rift Valley (wheat, maize, tea), Nyanza (rice, sorghum), "
            "Eastern (beans, sorghum, maize), Coast (coconut, cashew, rice). "
            "Alert thresholds should be tuned to regional microclimates."
        ),
        "doc_category": "practice",
        "region": "kenya",
    },

    # ====================================================================
    # DISEASE / PEST TREATMENT KNOWLEDGE (for RAG disease alerts)
    # ====================================================================
    {
        "doc_text": (
            "Leaf blight (bacterial or fungal) causes brown/yellow lesions on leaves. "
            "TREATMENT: Apply Mancozeb 80% WP at 200g/acre or Ridomil Gold MZ as foliar "
            "spray every 7-10 days. Apply early morning or late evening. Do NOT spray if "
            "rain is expected within 6 hours. ORGANIC: Copper Oxychloride at 150g/acre. "
            "CULTURAL: Remove and burn infected leaves, improve air circulation by pruning, "
            "avoid overhead irrigation, rotate crops next season."
        ),
        "doc_category": "pest_disease",
        "crop": "maize",
    },
    {
        "doc_text": (
            "Rust disease (fungal) causes orange-brown pustules on leaf surfaces. "
            "TREATMENT: Apply Propiconazole 250 EC (Score/Tilt) at 100ml/acre as foliar spray "
            "at first sign of rust. Systemic action — absorbed into leaves. For prevention, "
            "use Mancozeb 80% WP at 200g/acre. CULTURAL: Plant rust-resistant varieties "
            "(WH505 wheat, H614D maize), remove volunteer plants between seasons."
        ),
        "doc_category": "pest_disease",
        "crop": "maize",
    },
    {
        "doc_text": (
            "Aphid and pest damage (sucking insects — aphids, whiteflies, thrips, mites). "
            "TREATMENT: Apply Imidacloprid 200 SL (Confidor) at 50ml/acre as systemic drench "
            "or foliar spray. Observe pre-harvest interval. ORGANIC: Neem Oil Extract at "
            "200ml/acre every 5-7 days. CULTURAL: Introduce beneficial insects (ladybugs), "
            "use yellow sticky traps, intercrop with marigold or basil as repellent plants."
        ),
        "doc_category": "pest_disease",
    },
    {
        "doc_text": (
            "Plant wilting can result from water stress, fusarium wilt, or nutrient deficiency. "
            "DIAGNOSIS: Check soil moisture first — if below 40%, irrigate immediately. If soil "
            "moisture is adequate, inspect roots for brown discoloration (fusarium). "
            "TREATMENT: For nutrient stress, apply Foliar Feed NPK 20-20-20 at 500g/acre. "
            "For fusarium, apply Carbendazim 50% WP at 100g/acre as soil drench. "
            "CULTURAL: Mulch to conserve moisture, improve drainage if waterlogged."
        ),
        "doc_category": "pest_disease",
    },
    {
        "doc_text": (
            "Fall armyworm (Spodoptera frugiperda) is the most devastating maize pest in Kenya. "
            "Signs: windowing on young leaves, frass in the whorl. "
            "TREATMENT: Apply Emamectin Benzoate or Ampligo 150 ZC at 40ml/acre — spray directly "
            "into maize whorls, target larvae within first 2 weeks. ORGANIC: Bt (Bacillus "
            "thuringiensis) at 100g/acre on leaves. CULTURAL: Push-pull technology with "
            "Brachiaria and Desmodium. Hand-pick egg masses. Use pheromone traps."
        ),
        "doc_category": "pest_disease",
        "crop": "maize",
    },
    {
        "doc_text": (
            "Coffee berry disease (CBD) and leaf rust are major coffee diseases in Kenya. "
            "CBD TREATMENT: Apply Copper-based fungicide at flowering, repeat every 3 weeks. "
            "Leaf rust TREATMENT: Propiconazole or Triadimefon at 100ml/acre. "
            "CULTURAL: Prune to improve air flow, remove diseased berries. Use Ruiru 11 "
            "or Batian varieties which are resistant to both CBD and leaf rust."
        ),
        "doc_category": "pest_disease",
        "crop": "coffee",
    },
    {
        "doc_text": (
            "Potato late blight (Phytophthora infestans) thrives in cool wet conditions. "
            "Signs: water-soaked lesions on leaves, white mould underneath. Spreads rapidly. "
            "TREATMENT: Preventive Mancozeb at 200g/acre, curative Metalaxyl at 100g/acre. "
            "Apply every 5-7 days in wet season. CULTURAL: Plant certified disease-free seed, "
            "remove and destroy infected plants, practice 3-year crop rotation."
        ),
        "doc_category": "pest_disease",
        "crop": "potatoes",
    },
    {
        "doc_text": (
            "When disease detection from ESP32-CAM or uploaded images identifies a crop issue, "
            "the system should: 1) Classify the disease/deficiency, 2) Look up treatment in the "
            "knowledge base, 3) Calculate doses based on farm size in acres, 4) Search nearest "
            "agrovets in the farmer's sub-county for matching products with prices, 5) Present "
            "purchase options (web dashboard, USSD, or SMS order). The alert should include "
            "both immediate cultural practices (free, no-cost actions) and product-based treatments "
            "with exact quantities and estimated costs."
        ),
        "doc_category": "practice",
    },
    {
        "doc_text": (
            "Soil nutrient deficiency treatment guide for Kenya: "
            "LOW NITROGEN (N < 20 ppm): Apply CAN at 50kg/acre or Urea 46% at 50kg/acre. "
            "Side-dress along crop rows. CAN for acidic soils, Urea for neutral soils. "
            "LOW PHOSPHORUS (P < 15 ppm): Apply DAP at 50kg/acre at planting depth. "
            "P is immobile — must be placed near roots. "
            "LOW POTASSIUM (K < 100 ppm): Apply MOP at 40kg/acre. SOP for sensitive crops. "
            "ACIDIC SOIL (pH < 5.5): Agricultural Lime at 1 tonne/acre, apply 2-3 months before planting. "
            "ALKALINE SOIL (pH > 7.5): Elemental Sulphur at 200kg/acre."
        ),
        "doc_category": "threshold",
    },
    {
        "doc_text": (
            "Multimodal correlation for disease diagnosis: When leaf blight is detected from "
            "camera images AND soil pH is low AND moisture is high, the condition is likely "
            "fungal blight exacerbated by acidic waterlogged conditions. Treatment should address "
            "both the disease (fungicide) and the root cause (lime application + drainage). "
            "When wilting is detected AND soil moisture is adequate, suspect fusarium wilt — "
            "check roots for discoloration. Correlating image, soil, and satellite data gives "
            "90%+ accurate diagnosis vs 70% from images alone."
        ),
        "doc_category": "practice",
    },
    {
        "doc_text": (
            "Agrovet product pricing guide for common treatments in Kenya (2025): "
            "Mancozeb 80% WP (250g): KES 350-500. Ridomil Gold MZ (250g): KES 800-1200. "
            "Propiconazole 250 EC (100ml): KES 600-900. Imidacloprid 200 SL (100ml): KES 500-800. "
            "CAN fertilizer (50kg bag): KES 3000-3500. DAP fertilizer (50kg bag): KES 3500-4500. "
            "Urea 46% (50kg bag): KES 3000-3800. Agricultural Lime (50kg bag): KES 600-1000. "
            "Neem Oil Extract (100ml): KES 300-500. Drip Irrigation Kit (1/4 acre): KES 15000-25000."
        ),
        "doc_category": "practice",
    },
]


def seed_knowledge():
    """Insert all knowledge entries with embeddings."""
    from database.connection import get_sync_session
    from database.models import AgKnowledge

    try:
        from sentence_transformers import SentenceTransformer
        embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception as e:
        logger.error(f"Cannot load embedding model: {e}")
        sys.exit(1)

    with get_sync_session() as session:
        # Check existing count
        from sqlmodel import text
        existing = session.exec(text("SELECT COUNT(*) FROM ag_knowledge")).one()  # type: ignore[call-overload]
        logger.info(f"Existing entries: {existing}")

        inserted = 0
        for entry in KNOWLEDGE_ENTRIES:
            doc_text = entry["doc_text"]

            # Check for duplicate (exact text match)
            dup = session.exec(  # type: ignore[call-overload]
                text("SELECT id FROM ag_knowledge WHERE doc_text = :t LIMIT 1"),
                params={"t": doc_text},
            ).first()
            if dup:
                logger.debug(f"Skipping duplicate: {doc_text[:60]}...")
                continue

            # Compute embedding
            vec = embed_model.encode(doc_text).tolist()

            obj = AgKnowledge(
                doc_text=doc_text,
                doc_category=entry.get("doc_category", "general"),
                doc_source="seed_knowledge",
                crop=entry.get("crop"),
                region=entry.get("region"),
                season=entry.get("season"),
                embedding=vec,
            )
            session.add(obj)
            inserted += 1

        session.commit()
        logger.info(f"Inserted {inserted} new knowledge entries")

        # Final count
        total = session.exec(text("SELECT COUNT(*) FROM ag_knowledge")).one()  # type: ignore[call-overload]
        logger.info(f"Total ag_knowledge entries: {total}")


def check_knowledge():
    """Just print the current count and categories."""
    from database.connection import get_sync_session
    from sqlmodel import text

    with get_sync_session() as session:
        total = session.exec(text("SELECT COUNT(*) FROM ag_knowledge")).one()  # type: ignore[call-overload]
        logger.info(f"Total ag_knowledge entries: {total}")

        cats = session.exec(  # type: ignore[call-overload]
            text("SELECT doc_category, COUNT(*) FROM ag_knowledge GROUP BY doc_category ORDER BY count DESC")
        ).all()
        for cat, cnt in cats:
            logger.info(f"  {cat}: {cnt}")

        crops = session.exec(  # type: ignore[call-overload]
            text("SELECT crop, COUNT(*) FROM ag_knowledge WHERE crop IS NOT NULL GROUP BY crop ORDER BY crop")
        ).all()
        for crop, cnt in crops:
            logger.info(f"  {crop}: {cnt}")

        crops = session.exec(  # type: ignore[call-overload]
            text("SELECT crop, COUNT(*) FROM ag_knowledge WHERE crop IS NOT NULL GROUP BY crop ORDER BY crop")
        ).all()
        for crop, cnt in crops:
            logger.info(f"  crop={crop}: {cnt}")


# ════════════════════════════════════════════════════════════════════════
#  Agrovet product seed data (sample products across Kenya)
# ════════════════════════════════════════════════════════════════════════

SAMPLE_AGROVET_PRODUCTS = [
    # Fungicides
    {"name": "Mancozeb 80% WP 250g", "name_sw": "Dawa ya Kuvu Mancozeb 250g", "description": "Contact fungicide for leaf blight, downy mildew, late blight. Apply 200g/acre as foliar spray.", "category": "pesticide", "price_kes": 450, "unit": "pack", "crop_applicable": ["maize", "potatoes", "tomatoes", "beans"]},
    {"name": "Ridomil Gold MZ 250g", "name_sw": "Ridomil Gold 250g", "description": "Systemic + contact fungicide for late blight and downy mildew. Premium protection.", "category": "pesticide", "price_kes": 1050, "unit": "pack", "crop_applicable": ["potatoes", "tomatoes", "maize"]},
    {"name": "Score 250 EC 100ml", "name_sw": "Score 250 EC 100ml", "description": "Systemic fungicide (Propiconazole) for rust, leaf spot, powdery mildew.", "category": "pesticide", "price_kes": 750, "unit": "bottle", "crop_applicable": ["wheat", "maize", "coffee", "beans"]},
    {"name": "Copper Oxychloride 500g", "name_sw": "Shaba Oxychloride 500g", "description": "Organic-approved copper fungicide. Preventive and curative for blight and leaf spot.", "category": "pesticide", "price_kes": 550, "unit": "pack", "crop_applicable": ["coffee", "potatoes", "tomatoes", "maize"]},
    {"name": "Carbendazim 50% WP 100g", "name_sw": "Carbendazim 100g", "description": "Systemic fungicide for fusarium wilt and root rot. Soil drench application.", "category": "pesticide", "price_kes": 350, "unit": "pack", "crop_applicable": ["beans", "maize", "wheat"]},

    # Insecticides
    {"name": "Confidor (Imidacloprid 200 SL) 100ml", "name_sw": "Confidor 100ml", "description": "Systemic insecticide for aphids, whiteflies, thrips. 50ml/acre as drench or spray.", "category": "pesticide", "price_kes": 650, "unit": "bottle", "crop_applicable": ["maize", "beans", "coffee", "potatoes"]},
    {"name": "Thunder OD 145 100ml", "name_sw": "Thunder 100ml", "description": "Dual-action insecticide (Imidacloprid + Beta-cyfluthrin). For severe pest infestations.", "category": "pesticide", "price_kes": 850, "unit": "bottle", "crop_applicable": ["maize", "beans", "coffee"]},
    {"name": "Ampligo 150 ZC 100ml", "name_sw": "Ampligo 100ml", "description": "Premium insecticide for fall armyworm in maize. Spray into whorls.", "category": "pesticide", "price_kes": 900, "unit": "bottle", "crop_applicable": ["maize", "sorghum"]},
    {"name": "Neem Oil Extract 200ml", "name_sw": "Mafuta ya Mwarobaini 200ml", "description": "Organic bio-insecticide from Neem. Safe for beneficial insects. Spray every 5-7 days.", "category": "pesticide", "price_kes": 400, "unit": "bottle", "crop_applicable": ["maize", "beans", "coffee", "potatoes", "tomatoes"]},
    {"name": "Bt (Bacillus thuringiensis) 100g", "name_sw": "Dawa ya Kibayolojia Bt 100g", "description": "Organic bio-pesticide for caterpillars and armyworm. Larvae must ingest.", "category": "pesticide", "price_kes": 500, "unit": "pack", "crop_applicable": ["maize", "sorghum", "beans"]},

    # Fertilizers
    {"name": "CAN (Calcium Ammonium Nitrate) 50kg", "name_sw": "CAN Mbolea 50kg", "description": "Nitrogen fertilizer for top-dressing. 50kg/acre at knee height. Best for acidic soils.", "category": "fertilizer", "price_kes": 3200, "unit": "bag", "crop_applicable": ["maize", "wheat", "sorghum", "rice"]},
    {"name": "DAP (Di-Ammonium Phosphate) 50kg", "name_sw": "DAP Mbolea 50kg", "description": "Phosphorus fertilizer for planting. Band placement at seed depth. 50kg/acre.", "category": "fertilizer", "price_kes": 4000, "unit": "bag", "crop_applicable": ["maize", "beans", "wheat", "potatoes"]},
    {"name": "Urea 46% 50kg", "name_sw": "Urea Mbolea 50kg", "description": "High-nitrogen fertilizer for top-dressing. 50kg/acre. Apply before rain or irrigate after.", "category": "fertilizer", "price_kes": 3400, "unit": "bag", "crop_applicable": ["maize", "wheat", "rice", "sugarcane"]},
    {"name": "NPK 17-17-17 50kg", "name_sw": "NPK Mbolea 50kg", "description": "Balanced NPK fertilizer for general use. Suitable for all crops at planting.", "category": "fertilizer", "price_kes": 3800, "unit": "bag", "crop_applicable": ["maize", "beans", "potatoes", "coffee", "tea"]},
    {"name": "MOP (Muriate of Potash) 50kg", "name_sw": "Potashi Mbolea 50kg", "description": "Potassium fertilizer. 40kg/acre. Essential for fruit and tuber crops.", "category": "fertilizer", "price_kes": 3000, "unit": "bag", "crop_applicable": ["potatoes", "beans", "coffee", "sugarcane"]},
    {"name": "Agricultural Lime 50kg", "name_sw": "Chokaa ya Kilimo 50kg", "description": "For acidic soils (pH < 5.5). Apply 1 tonne/acre, 2-3 months before planting.", "category": "fertilizer", "price_kes": 800, "unit": "bag", "crop_applicable": ["maize", "beans", "wheat", "potatoes", "coffee"]},
    {"name": "Foliar Feed NPK 20-20-20 500g", "name_sw": "Mbolea ya Majani 500g", "description": "Foliar spray fertilizer for quick nutrient recovery. 500g/acre in 200L water.", "category": "fertilizer", "price_kes": 450, "unit": "pack", "crop_applicable": ["maize", "beans", "potatoes", "coffee", "tomatoes"]},

    # Seeds
    {"name": "DK 8031 Maize Seed 2kg", "name_sw": "Mbegu za Mahindi DK 8031 2kg", "description": "High-yielding hybrid maize. Matures in 120-150 days. Good for medium-altitude zones.", "category": "seeds", "price_kes": 850, "unit": "pack", "crop_applicable": ["maize"]},
    {"name": "WH505 Wheat Seed 10kg", "name_sw": "Mbegu za Ngano WH505 10kg", "description": "Rust-resistant bread wheat variety. Best for Rift Valley and Central Kenya.", "category": "seeds", "price_kes": 1200, "unit": "pack", "crop_applicable": ["wheat"]},
    {"name": "KK8 Beans Seed 2kg", "name_sw": "Mbegu za Maharagwe KK8 2kg", "description": "Climbing bean variety. High yield, disease resistant. Good for Central Kenya.", "category": "seeds", "price_kes": 600, "unit": "pack", "crop_applicable": ["beans"]},

    # Tools
    {"name": "Drip Irrigation Kit (1/4 acre)", "name_sw": "Kifaa cha Umwagiliaji Matone", "description": "Complete drip irrigation system for 1/4 acre. Saves 30-50% water vs flood irrigation.", "category": "tools", "price_kes": 18000, "unit": "kit", "crop_applicable": ["maize", "beans", "potatoes", "tomatoes"]},
    {"name": "Knapsack Sprayer 16L", "name_sw": "Kipulizia Dawa 16L", "description": "Manual backpack sprayer for pesticide and foliar feed application.", "category": "tools", "price_kes": 3500, "unit": "piece", "crop_applicable": ["maize", "beans", "potatoes", "coffee", "tomatoes"]},
    {"name": "Soil pH Test Kit", "name_sw": "Kifaa cha Kupima pH ya Udongo", "description": "Quick soil pH test strips. 50 tests per pack. Essential for liming decisions.", "category": "tools", "price_kes": 800, "unit": "pack", "crop_applicable": ["maize", "beans", "potatoes", "coffee", "wheat"]},
]

# ────────────────────────────────────────────────────────────────────
#  Build county → sub-county map dynamically from kenya_sub_counties
#  This ensures ALL 47 Kenyan counties get agrovet products.
# ────────────────────────────────────────────────────────────────────

def _build_all_counties_map() -> dict:
    """
    Returns {display_county_name: [sub_county_display, ...]}.
    Uses kenya_sub_counties.py for the authoritative list.
    Falls back to the original 10-county hardcoded set if import fails.
    """
    try:
        from kenya_sub_counties import KENYA_SUB_COUNTIES
        counties = {}
        for county_key, data in KENYA_SUB_COUNTIES.items():
            display = data.get("county_name", county_key.replace("_", " ").title())
            subs = []
            for sub_key, sub_data in data.get("sub_counties", {}).items():
                sub_display = sub_data.get("name", sub_key.replace("_", " ").title())
                subs.append(sub_display)
            if not subs:
                subs = [display]  # fallback: use county name
            counties[display] = subs
        logger.info(f"Built county map: {len(counties)} counties")
        return counties
    except ImportError:
        logger.warning("kenya_sub_counties not available — using hardcoded 10-county fallback")
        return {
            "Kiambu": ["Githunguri", "Thika Town", "Limuru", "Ruiru"],
            "Nakuru": ["Nakuru Town East", "Naivasha", "Gilgil", "Molo"],
            "Uasin Gishu": ["Kapseret", "Ainabkoi", "Turbo"],
            "Trans Nzoia": ["Kitale Town", "Saboti"],
            "Bungoma": ["Kanduyi", "Bumula"],
            "Nyandarua": ["Ol Kalou", "Kinangop"],
            "Meru": ["Imenti North", "Imenti South"],
            "Kisii": ["Kisii Central", "South Mugirango"],
            "Nyeri": ["Nyeri Town", "Mathira"],
            "Kericho": ["Ainamoi", "Belgut"],
        }


# Non-agricultural counties get a reduced product set (basic essentials)
_NON_AGRICULTURAL_COUNTIES = {
    "Samburu", "Turkana", "Isiolo", "Marsabit",
    "Mombasa", "Garissa", "Mandera", "Wajir", "Nairobi",
}

# Indices into SAMPLE_AGROVET_PRODUCTS for the basic subset (fertilizers + tools + seeds)
_BASIC_PRODUCT_CATEGORIES = {"fertilizer", "tools", "seeds"}


def seed_agrovet_products(force: bool = False):
    """
    Seed agrovet_products table with sample products across ALL 47 Kenyan counties.

    Agricultural counties (38): Full product range (23 products each)
    Non-agricultural counties (9): Basic subset (fertilizers, seeds, tools — ~10 products)

    Total: ~38×23 + 9×10 ≈ 964 products
    """
    from database.connection import get_sync_session
    from database.models import AgrovetProduct
    from sqlmodel import text
    from decimal import Decimal

    with get_sync_session() as session:
        existing = session.exec(text("SELECT COUNT(*) FROM agrovet_products")).first()  # type: ignore[call-overload]
        count = existing[0] if existing else 0
        if count > 0 and not force:
            logger.info(f"Agrovet products already seeded ({count} products). Use --force to reseed.")
            return

        if force and count > 0:
            session.exec(text("DELETE FROM agrovet_products"))  # type: ignore[call-overload]
            session.commit()
            logger.info(f"Cleared {count} existing products for reseed")

        all_counties = _build_all_counties_map()
        inserted = 0
        county_count = 0

        for county_name, sub_counties in all_counties.items():
            county_count += 1
            is_non_agricultural = county_name in _NON_AGRICULTURAL_COUNTIES

            # Select product set: full for agricultural, basic for others
            if is_non_agricultural:
                products_to_seed = [
                    p for p in SAMPLE_AGROVET_PRODUCTS
                    if p["category"] in _BASIC_PRODUCT_CATEGORIES
                ]
            else:
                products_to_seed = SAMPLE_AGROVET_PRODUCTS

            for idx, product_data in enumerate(products_to_seed):
                # Distribute products across sub-counties
                sub = sub_counties[idx % len(sub_counties)]
                product = AgrovetProduct(
                    name=product_data["name"],
                    name_sw=product_data.get("name_sw"),
                    description=product_data.get("description"),
                    category=product_data["category"],
                    price_kes=Decimal(str(product_data["price_kes"])),
                    unit=product_data["unit"],
                    in_stock=True,
                    stock_quantity=50,
                    supplier_name=f"{county_name} Agrovet Centre",
                    supplier_location=f"{sub}, {county_name}",
                    supplier_county=county_name,
                    supplier_sub_county=sub,
                    crop_applicable=product_data.get("crop_applicable"),
                    active=True,
                )
                session.add(product)
                inserted += 1

        session.commit()
        logger.info(f"Seeded {inserted} agrovet products across {county_count} counties")


if __name__ == "__main__":
    force = "--force" in sys.argv
    if "--check" in sys.argv:
        check_knowledge()
    elif "--products" in sys.argv:
        seed_agrovet_products(force=force)
    elif "--all" in sys.argv:
        seed_knowledge()
        seed_agrovet_products(force=force)
    else:
        seed_knowledge()
