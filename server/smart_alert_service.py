"""
Smart Alert Service for Smart Shamba
Uses actual Earth observation data to generate meaningful, actionable SMS alerts.

Includes:
- Structured crop-optimal thresholds per metric
- Farm condition evaluator (compares sensor + satellite vs optimal)
- Good-news alerts when all conditions are optimal
- Per-metric deviation alerts with exact readings
- RAG-augmented advice via pgvector + Gemini
"""

import os
import json as _json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agrovet integration for disease → product recommendation pipeline
try:
    from agrovet_service import AgrovetRecommendationService, detect_deficiencies_from_sensors
    AGROVET_AVAILABLE = True
except ImportError:
    AGROVET_AVAILABLE = False
    logger.warning("AgrovetRecommendationService not available")


# ══════════════════════════════════════════════════════════════════════
#  CROP OPTIMAL RANGES — Structured thresholds for Kenya's main crops
#  Format: (min, max, unit, description)
#  Used by evaluate_farm_conditions() for programmatic comparison
# ══════════════════════════════════════════════════════════════════════

CROP_OPTIMAL_RANGES: Dict[str, Dict[str, Tuple]] = {
    'maize': {
        'soil_ph':            (5.5,  7.0,  '',    'Slightly acidic to neutral'),
        'soil_moisture_pct':  (40,   70,   '%',   'Moderate moisture'),
        'temperature_c':      (18,   32,   '°C',  'Warm climate'),
        'humidity_pct':       (50,   80,   '%',   'Moderate to high'),
        'ndvi':               (0.35, 0.85, '',    'Active vegetation'),
        'ndwi':               (-0.1, 0.3,  '',    'Adequate water content'),
        'rainfall_mm':        (50,   200,  'mm',  'Monthly rainfall (500-1000mm/yr)'),
    },
    'coffee': {
        'soil_ph':            (6.0,  6.5,  '',    'Slightly acidic'),
        'soil_moisture_pct':  (50,   70,   '%',   'Consistently moist'),
        'temperature_c':      (15,   28,   '°C',  'Cool to warm highlands'),
        'humidity_pct':       (60,   85,   '%',   'High humidity'),
        'ndvi':               (0.45, 0.80, '',    'Dense canopy'),
        'ndwi':               (0.0,  0.35, '',    'Good moisture retention'),
        'rainfall_mm':        (80,   250,  'mm',  'Monthly rainfall (1200-2000mm/yr)'),
    },
    'tea': {
        'soil_ph':            (4.5,  5.8,  '',    'Acidic soil'),
        'soil_moisture_pct':  (60,   80,   '%',   'High moisture'),
        'temperature_c':      (13,   25,   '°C',  'Cool highlands'),
        'humidity_pct':       (70,   90,   '%',   'High humidity'),
        'ndvi':               (0.50, 0.85, '',    'Dense green canopy'),
        'ndwi':               (0.05, 0.35, '',    'High water content'),
        'rainfall_mm':        (100,  300,  'mm',  'Monthly rainfall (1500-2500mm/yr)'),
    },
    'rice': {
        'soil_ph':            (5.5,  7.0,  '',    'Slightly acidic to neutral'),
        'soil_moisture_pct':  (70,   100,  '%',   'Saturated/paddy'),
        'temperature_c':      (20,   35,   '°C',  'Warm tropical'),
        'humidity_pct':       (60,   90,   '%',   'High humidity'),
        'ndvi':               (0.30, 0.80, '',    'Active growth'),
        'ndwi':               (0.1,  0.5,  '',    'High water presence'),
        'rainfall_mm':        (100,  350,  'mm',  'Monthly rainfall (1500-3000mm/yr)'),
    },
    'beans': {
        'soil_ph':            (6.0,  7.0,  '',    'Near neutral'),
        'soil_moisture_pct':  (40,   65,   '%',   'Moderate, well-drained'),
        'temperature_c':      (16,   28,   '°C',  'Mild climate'),
        'humidity_pct':       (50,   75,   '%',   'Moderate'),
        'ndvi':               (0.30, 0.75, '',    'Active ground cover'),
        'ndwi':               (-0.1, 0.25, '',    'Moderate water needs'),
        'rainfall_mm':        (40,   150,  'mm',  'Monthly rainfall (400-900mm/yr)'),
    },
    'wheat': {
        'soil_ph':            (6.0,  7.5,  '',    'Neutral to slightly alkaline'),
        'soil_moisture_pct':  (35,   60,   '%',   'Moderate, drained'),
        'temperature_c':      (12,   25,   '°C',  'Cool climate'),
        'humidity_pct':       (40,   70,   '%',   'Low to moderate'),
        'ndvi':               (0.35, 0.80, '',    'Active tillering/heading'),
        'ndwi':               (-0.1, 0.25, '',    'Moderate water content'),
        'rainfall_mm':        (30,   120,  'mm',  'Monthly rainfall (300-600mm/yr)'),
    },
    'sugarcane': {
        'soil_ph':            (5.5,  7.5,  '',    'Wide pH tolerance'),
        'soil_moisture_pct':  (50,   80,   '%',   'High moisture'),
        'temperature_c':      (20,   35,   '°C',  'Tropical warm'),
        'humidity_pct':       (55,   85,   '%',   'High humidity'),
        'ndvi':               (0.40, 0.85, '',    'Tall dense canopy'),
        'ndwi':               (0.0,  0.35, '',    'Adequate moisture'),
        'rainfall_mm':        (80,   250,  'mm',  'Monthly rainfall (1000-2000mm/yr)'),
    },
    'potatoes': {
        'soil_ph':            (5.0,  6.5,  '',    'Acidic to slightly acidic'),
        'soil_moisture_pct':  (45,   70,   '%',   'Moist, well-drained'),
        'temperature_c':      (10,   22,   '°C',  'Cool highlands'),
        'humidity_pct':       (55,   80,   '%',   'Moderate to high'),
        'ndvi':               (0.35, 0.80, '',    'Active foliage'),
        'ndwi':               (-0.05,0.25, '',    'Moderate water needs'),
        'rainfall_mm':        (50,   150,  'mm',  'Monthly rainfall (500-800mm/yr)'),
    },
    'sorghum': {
        'soil_ph':            (5.5,  8.0,  '',    'Wide pH tolerance'),
        'soil_moisture_pct':  (25,   55,   '%',   'Drought-tolerant'),
        'temperature_c':      (20,   38,   '°C',  'Hot, semi-arid'),
        'humidity_pct':       (30,   65,   '%',   'Low to moderate'),
        'ndvi':               (0.25, 0.70, '',    'Moderate vegetation'),
        'ndwi':               (-0.2, 0.15, '',    'Low water demand'),
        'rainfall_mm':        (25,   100,  'mm',  'Monthly rainfall (300-600mm/yr)'),
    },
}

# Friendly display names for metrics
METRIC_DISPLAY = {
    'soil_ph':           ('Soil pH',           ''),
    'soil_moisture_pct': ('Soil Moisture',     '%'),
    'temperature_c':     ('Temperature',       '°C'),
    'humidity_pct':      ('Humidity',           '%'),
    'ndvi':              ('Crop Health (NDVI)', ''),
    'ndwi':              ('Water Index (NDWI)', ''),
    'rainfall_mm':       ('Rainfall',          'mm'),
    'wind_speed_ms':     ('Wind Speed',        'm/s'),
    'pressure_hpa':      ('Pressure',          'hPa'),
    'light_lux':         ('Light',             'lux'),
    'co2_ppm':           ('CO₂',               'ppm'),
    'soil_nitrogen':     ('Nitrogen (N)',       'mg/kg'),
    'soil_phosphorus':   ('Phosphorus (P)',     'mg/kg'),
    'soil_potassium':    ('Potassium (K)',      'mg/kg'),
}

# ══════════════════════════════════════════════════════════════════════
#  EXTREME WEATHER THRESHOLDS — Universal (not crop-specific)
#  Triggers: auto-alert when forecast or current conditions match
# ══════════════════════════════════════════════════════════════════════

EXTREME_WEATHER_THRESHOLDS = {
    'heavy_rainfall': {
        'metric': 'rainfall_mm',
        'threshold': 80,        # mm in 24 hours
        'direction': 'above',
        'severity': 'critical',
        'message_en': 'Heavy rainfall alert: {value:.0f}mm expected. '
                      'Secure crops, clear drainage channels, and avoid low-lying areas.',
        'message_sw': 'Onyo la mvua kubwa: {value:.0f}mm inatarajiwa. '
                      'Linda mazao, safisha mifereji, epuka maeneo ya chini.',
    },
    'drought_risk': {
        'metric': 'total_rain_10d_mm',
        'threshold': 5,         # <5mm total over 10 days
        'direction': 'below',
        'severity': 'warning',
        'message_en': 'Drought risk: Only {value:.0f}mm rain expected over 10 days. '
                      'Irrigate, mulch, and conserve soil moisture.',
        'message_sw': 'Hatari ya ukame: Mvua {value:.0f}mm pekee kwa siku 10. '
                      'Mwagilia, funika udongo, hifadhi unyevu.',
    },
    'heatwave': {
        'metric': 'max_temp_c',
        'threshold': 38,        # °C
        'direction': 'above',
        'severity': 'critical',
        'message_en': 'Heatwave alert: {value:.0f}°C expected. '
                      'Irrigate early morning, provide shade for seedlings.',
        'message_sw': 'Onyo la joto kali: {value:.0f}°C inatarajiwa. '
                      'Mwagilia asubuhi na mapema, weka kivuli kwa miche.',
    },
    'frost_risk': {
        'metric': 'min_temp_c',
        'threshold': 5,         # °C for Kenya highlands
        'direction': 'below',
        'severity': 'warning',
        'message_en': 'Frost/cold risk: {value:.0f}°C expected. '
                      'Cover sensitive crops and delay planting.',
        'message_sw': 'Hatari ya baridi kali: {value:.0f}°C inatarajiwa. '
                      'Funika mazao dhaifu, ahirisha kupanda.',
    },
    'high_wind': {
        'metric': 'wind_speed_kmh',
        'threshold': 50,        # km/h
        'direction': 'above',
        'severity': 'warning',
        'message_en': 'High wind alert: {value:.0f}km/h expected. '
                      'Stake tall crops, secure structures, avoid spraying.',
        'message_sw': 'Onyo la upepo mkali: {value:.0f}km/h. '
                      'Simamisha mazao marefu, imarisha miundo, epuka kunyunyizia.',
    },
    'storm_pressure': {
        'metric': 'pressure_hpa',
        'threshold': 1000,      # hPa — low pressure = storm
        'direction': 'below',
        'severity': 'warning',
        'message_en': 'Low pressure ({value:.0f}hPa) indicates incoming storm. '
                      'Harvest ripe crops and secure equipment.',
        'message_sw': 'Shinikizo la chini ({value:.0f}hPa) linaonyesha dhoruba inakuja. '
                      'Vuna mazao yaliyoiva na linda vifaa.',
    },
}

# ══════════════════════════════════════════════════════════════════════
#  IoT SENSOR ANOMALY THRESHOLDS — Rate-of-change and extremes
#  Triggers: auto-alert when sensor readings show sudden changes
# ══════════════════════════════════════════════════════════════════════

SENSOR_ANOMALY_THRESHOLDS = {
    'soil_moisture_crash': {
        'metric': 'soil_moisture_pct',
        'type': 'rate_drop',
        'delta_pct': 20,        # >20% drop in 6 hours
        'hours': 6,
        'severity': 'critical',
        'message_en': 'Soil moisture dropped {delta:.0f}% in {hours}h '
                      '(from {old:.0f}% to {new:.0f}%). Possible pipe break or wilting.',
        'message_sw': 'Unyevu wa udongo umeshuka {delta:.0f}% kwa saa {hours} '
                      '(kutoka {old:.0f}% hadi {new:.0f}%). Angalia bomba au mimea.',
    },
    'temperature_spike': {
        'metric': 'temperature_c',
        'type': 'abs_high',
        'threshold': 42,        # °C — extreme for Kenya farmland
        'severity': 'critical',
        'message_en': 'Extreme temperature: {value:.1f}°C at sensor. '
                      'Irrigate immediately and shade seedlings.',
        'message_sw': 'Joto kali sana: {value:.1f}°C kwenye sensori. '
                      'Mwagilia sasa na weka kivuli kwa miche.',
    },
    'ph_crash': {
        'metric': 'soil_ph',
        'type': 'rate_drop',
        'delta_pct': 15,        # >15% drop (e.g. 6.5 → 5.5)
        'hours': 12,
        'severity': 'warning',
        'message_en': 'Soil pH dropped from {old:.1f} to {new:.1f}. '
                      'Possible acid runoff — consider liming.',
        'message_sw': 'pH ya udongo imeshuka kutoka {old:.1f} hadi {new:.1f}. '
                      'Inawezekana ni asidi — fikiria chite.',
    },
    'co2_spike': {
        'metric': 'co2_ppm',
        'type': 'abs_high',
        'threshold': 1000,      # ppm — high for open-air farm
        'severity': 'warning',
        'message_en': 'High CO₂ ({value:.0f}ppm) detected. '
                      'Check ventilation in greenhouse or nearby combustion source.',
        'message_sw': 'CO₂ ya juu ({value:.0f}ppm). '
                      'Angalia hewa katika chafu au chanzo cha moto.',
    },
    'npk_depletion': {
        'metric': 'soil_nitrogen',
        'type': 'abs_low',
        'threshold': 10,        # mg/kg — critically low
        'severity': 'warning',
        'message_en': 'Nitrogen critically low ({value:.0f}mg/kg). '
                      'Apply urea or organic compost within 48 hours.',
        'message_sw': 'Nitrogen iko chini sana ({value:.0f}mg/kg). '
                      'Weka urea au mboji ndani ya saa 48.',
    },
    'battery_critical': {
        'metric': 'battery_pct',
        'type': 'abs_low',
        'threshold': 15,        # % — device will stop
        'severity': 'info',
        'message_en': 'Sensor battery low ({value:.0f}%). Device may go offline soon.',
        'message_sw': 'Betri ya sensori iko chini ({value:.0f}%). Kifaa kinaweza kuzima.',
    },
}


@dataclass
class MetricDeviation:
    """A single metric that deviates from the optimal range."""
    metric: str
    display_name: str
    value: float
    optimal_min: float
    optimal_max: float
    unit: str
    severity: str          # 'info', 'warning', 'critical'
    direction: str         # 'low', 'high'
    description: str       # e.g. "Soil pH is too acidic"
    pct_deviation: float   # how far from the nearest bound (0-100+)


@dataclass
class FarmConditionReport:
    """Full evaluation of all farm metrics against optimal ranges."""
    crop: str
    status: str                              # 'optimal', 'good', 'warning', 'critical'
    overall_score: float                     # 0-100
    optimal_metrics: List[str] = field(default_factory=list)
    deviations: List[MetricDeviation] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

# Kenya Regions with their characteristics
KENYA_REGIONS = {
    'central': {
        'name_en': 'Central Highlands',
        'name_sw': 'Milima ya Kati',
        'counties': ['Kiambu', "Murang'a", 'Nyeri', 'Kirinyaga', 'Nyandarua'],
        'main_crops': ['coffee', 'tea', 'maize', 'beans', 'potatoes'],
        'rainfall_pattern': 'bimodal'  # Two rainy seasons
    },
    'rift_valley': {
        'name_en': 'Rift Valley',
        'name_sw': 'Bonde la Ufa',
        'counties': ['Nakuru', 'Uasin Gishu', 'Trans Nzoia', 'Kericho', 'Bomet'],
        'main_crops': ['maize', 'wheat', 'tea', 'pyrethrum', 'barley'],
        'rainfall_pattern': 'bimodal'
    },
    'western': {
        'name_en': 'Western Region',
        'name_sw': 'Mkoa wa Magharibi',
        'counties': ['Kakamega', 'Bungoma', 'Busia', 'Vihiga'],
        'main_crops': ['maize', 'beans', 'sugarcane', 'tea', 'bananas'],
        'rainfall_pattern': 'bimodal'
    },
    'eastern': {
        'name_en': 'Eastern Region',
        'name_sw': 'Mkoa wa Mashariki',
        'counties': ['Machakos', 'Kitui', 'Makueni', 'Embu', 'Tharaka-Nithi'],
        'main_crops': ['maize', 'beans', 'sorghum', 'millet', 'cotton'],
        'rainfall_pattern': 'bimodal'
    },
    'nyanza': {
        'name_en': 'Lake Victoria Basin',
        'name_sw': 'Eneo la Ziwa Victoria',
        'counties': ['Kisumu', 'Siaya', 'Migori', 'Homa Bay', 'Kisii'],
        'main_crops': ['rice', 'sugarcane', 'maize', 'cotton', 'sorghum'],
        'rainfall_pattern': 'bimodal'
    },
    'coast': {
        'name_en': 'Coastal Region',
        'name_sw': 'Pwani',
        'counties': ['Mombasa', 'Kilifi', 'Kwale', 'Lamu', 'Taita-Taveta'],
        'main_crops': ['coconut', 'cashew', 'maize', 'cassava', 'mango'],
        'rainfall_pattern': 'bimodal'
    }
}

# Crop-specific advice based on growth stages
CROP_ADVICE = {
    'maize': {
        'en': {
            'flowering': {
                'low_ndvi': "Your maize shows water stress. Irrigate immediately if possible. Check for fall armyworm.",
                'medium_ndvi': "Maize flowering detected. Ensure adequate moisture. Monitor for pests.",
                'high_ndvi': "Excellent maize health! Maintain current irrigation. Watch for tasseling stage."
            },
            'vegetative': {
                'low_ndvi': "Maize growth is slow. Consider top-dressing with nitrogen fertilizer.",
                'medium_ndvi': "Good maize establishment. Continue weeding and pest monitoring.",
                'high_ndvi': "Strong vegetative growth. Prepare for flowering stage in 2-3 weeks."
            }
        },
        'sw': {
            'flowering': {
                'low_ndvi': "Mahindi yako yanaonyesha ukosefu wa maji. Nyunyizia maji haraka. Kagua funza wa jeshi.",
                'medium_ndvi': "Kuchanua kwa mahindi kumegunduliwa. Hakikisha unyevu wa kutosha. Fuatilia wadudu.",
                'high_ndvi': "Afya bora ya mahindi! Endelea na umwagiliaji. Angalia hatua ya kutoa masuke."
            },
            'vegetative': {
                'low_ndvi': "Ukuaji wa mahindi ni polepole. Fikiria kutumia mbolea ya nitrojeni.",
                'medium_ndvi': "Mahindi yameanza vizuri. Endelea kupalilia na kufuatilia wadudu.",
                'high_ndvi': "Ukuaji mkubwa. Jiandae kwa hatua ya kuchanua katika wiki 2-3."
            }
        }
    },
    'coffee': {
        'en': {
            'flowering': {
                'low_ndvi': "Coffee bloom weak. Protect from heavy rain. Supplement with potassium.",
                'medium_ndvi': "Coffee flowering underway. Monitor for Coffee Berry Disease (CBD).",
                'high_ndvi': "Strong coffee bloom! Perfect conditions. Prepare for berry development."
            },
            'dormancy': {
                'low_ndvi': "Coffee stress detected during dormancy. Check soil moisture and pH.",
                'medium_ndvi': "Coffee entering dormancy. Good time for pruning and fertilization.",
                'high_ndvi': "Healthy coffee plants. Prepare for next flowering season."
            }
        },
        'sw': {
            'flowering': {
                'low_ndvi': "Kuchanua kwa kahawa ni dhaifu. Linda kutoka mvua kubwa. Ongeza potasiamu.",
                'medium_ndvi': "Kahawa inapochanua. Fuatilia ugonjwa wa tunda la kahawa (CBD).",
                'high_ndvi': "Kuchanua kwa kahawa kuzuri sana! Hali nzuri. Jiandae kwa ukuaji wa tunda."
            },
            'dormancy': {
                'low_ndvi': "Kahawa ina dhiki wakati wa kupumzika. Kagua unyevu wa udongo na pH.",
                'medium_ndvi': "Kahawa inaingia mapumziko. Wakati mzuri wa kukata na kuboreshwa.",
                'high_ndvi': "Mimea ya kahawa yenye afya. Jiandae kwa msimu ujao wa kuchanua."
            }
        }
    },
    'rice': {
        'en': {
            'flowering': {
                'low_ndvi': "Rice panicle initiation weak. Check water levels. Monitor for Rice Blast.",
                'medium_ndvi': "Rice heading stage detected. Maintain field water at 5-10cm depth.",
                'high_ndvi': "Excellent rice vigor! Optimal for grain filling. Protect from birds."
            },
            'vegetative': {
                'low_ndvi': "Rice growth stunted. Check for nutrient deficiency or waterlogging.",
                'medium_ndvi': "Rice tillering well. Apply nitrogen topdressing at this stage.",
                'high_ndvi': "Strong rice tillering. Prepare for panicle emergence in 2-3 weeks."
            }
        },
        'sw': {
            'flowering': {
                'low_ndvi': "Kuanza kwa masuke ya mpunga ni dhaifu. Kagua kiwango cha maji. Angalia ugonjwa.",
                'medium_ndvi': "Hatua ya kutoa masuke ya mpunga imegunduliwa. Weka maji kwa kina cha cm 5-10.",
                'high_ndvi': "Nguvu bora ya mpunga! Mazuri kwa kujaza nafaka. Linda kutoka ndege."
            },
            'vegetative': {
                'low_ndvi': "Ukuaji wa mpunga umepungua. Kagua ukosefu wa virutubisho au maji mengi.",
                'medium_ndvi': "Mpunga unaenea vizuri. Tumia mbolea ya nitrojeni wakati huu.",
                'high_ndvi': "Kuenea kwa mpunga kuzuri. Jiandae kwa kutoa masuke katika wiki 2-3."
            }
        }
    },
    'beans': {
        'en': {
            'flowering': {
                'low_ndvi': "Bean flowering weak. Ensure good drainage. Watch for bean fly.",
                'medium_ndvi': "Beans flowering detected. Good time to scout for pests.",
                'high_ndvi': "Strong bean bloom! Maintain moisture for pod development."
            },
            'vegetative': {
                'low_ndvi': "Bean growth slow. Check for root rot. Improve drainage.",
                'medium_ndvi': "Beans establishing well. Continue weeding between rows.",
                'high_ndvi': "Excellent bean growth. Prepare for flowering in 1-2 weeks."
            }
        },
        'sw': {
            'flowering': {
                'low_ndvi': "Kuchanua kwa maharagwe ni dhaifu. Hakikisha mtiririko wa maji ni mzuri. Angalia nzi.",
                'medium_ndvi': "Maharagwe yanapochanua. Wakati mzuri wa kutafuta wadudu.",
                'high_ndvi': "Kuchanua kwa maharagwe kuzuri! Dumisha unyevu kwa ukuaji wa masapi."
            },
            'vegetative': {
                'low_ndvi': "Ukuaji wa maharagwe ni polepole. Kagua kuoza kwa mizizi. Boresha mtiririko wa maji.",
                'medium_ndvi': "Maharagwe yanaanza vizuri. Endelea kupalilia kati ya mistari.",
                'high_ndvi': "Ukuaji wa maharagwe uzuri sana. Jiandae kwa kuchanua katika wiki 1-2."
            }
        }
    },
    'tea': {
        'en': {
            'plucking': {
                'low_ndvi': "Tea vigor declining. Consider fertilization and mulching.",
                'medium_ndvi': "Tea ready for plucking. Maintain 7-10 day plucking round.",
                'high_ndvi': "Excellent tea flush! Optimal plucking window. Don't delay."
            }
        },
        'sw': {
            'plucking': {
                'low_ndvi': "Nguvu ya chai inapungua. Fikiria mbolea na kuongeza malisho.",
                'medium_ndvi': "Chai iko tayari kwa kuchuma. Dumisha mzunguko wa siku 7-10.",
                'high_ndvi': "Majani ya chai mazuri sana! Wakati bora wa kuchuma. Usikawike."
            }
        }
    },
    'sugarcane': {
        'en': {
            'vegetative': {
                'low_ndvi': "Sugarcane stress detected. Check for stalk borers and water stress.",
                'medium_ndvi': "Sugarcane growing steadily. Continue weeding and fertilization.",
                'high_ndvi': "Excellent sugarcane vigor. Monitor for pests and diseases."
            }
        },
        'sw': {
            'vegetative': {
                'low_ndvi': "Dhiki ya miwa imegunduliwa. Kagua wadudu wa shina na ukosefu wa maji.",
                'medium_ndvi': "Miwa inakua vizuri. Endelea kupalilia na kutumia mbolea.",
                'high_ndvi': "Nguvu bora ya miwa. Fuatilia wadudu na magonjwa."
            }
        }
    },
    'wheat': {
        'en': {
            'flowering': {
                'low_ndvi': "Wheat heading weak. Apply nitrogen if not too late. Monitor for rust.",
                'medium_ndvi': "Wheat heading detected. Watch for rust diseases in humid weather.",
                'high_ndvi': "Strong wheat crop! Prepare for grain filling stage."
            },
            'vegetative': {
                'low_ndvi': "Wheat tillering poor. Top-dress with nitrogen fertilizer.",
                'medium_ndvi': "Wheat tillering adequately. Continue monitoring.",
                'high_ndvi': "Excellent wheat stand. Heading expected in 2-3 weeks."
            }
        },
        'sw': {
            'flowering': {
                'low_ndvi': "Kutoa masuke kwa ngano ni dhaifu. Tumia mbolea ya nitrojeni haraka. Angalia kutu.",
                'medium_ndvi': "Ngano inatoa masuke. Angalia magonjwa ya kutu katika hali ya unyevu.",
                'high_ndvi': "Mazao ya ngano mazuri! Jiandae kwa hatua ya kujaza nafaka."
            },
            'vegetative': {
                'low_ndvi': "Kuenea kwa ngano ni duni. Ongeza mbolea ya nitrojeni.",
                'medium_ndvi': "Ngano inaenea vya kutosha. Endelea kufuatilia.",
                'high_ndvi': "Ngano nzuri sana. Masuke yanatarajiwa katika wiki 2-3."
            }
        }
    }
}


@dataclass
class SmartAlert:
    """Enhanced alert with Earth observation insights"""
    farmer_name: str
    phone: str
    region: str
    crop: str
    language: str
    
    # EO Data
    ndvi_value: float
    health_score: float
    bloom_risk: str  # 'Low', 'Moderate', 'High'
    bloom_confidence: float
    
    # Contextual
    growth_stage: str
    advice: str
    data_source: str  # 'Sentinel-2', 'Landsat', 'MODIS'
    timestamp: datetime


class SmartAlertService:
    """
    Intelligent alert service that converts Earth observation data
    into actionable farmer insights using RAG (Retrieval-Augmented Generation).

    Pipeline:
      1. Gather satellite + IoT sensor data from PostgreSQL.
      2. Retrieve relevant knowledge via pgvector (Flora AI RAG).
      3. Build an augmented prompt and generate advice with Gemini.
      4. Deliver via Africa's Talking SMS + SendGrid email.
      5. Log every alert to PostgreSQL (alerts table).

    Sends both SMS and Email alerts based on farmer registration type:
    - Web users (with email): Receive both email and SMS
    - USSD users (no email): Receive only SMS
    """

    def __init__(self, db_service=None, sms_service=None, email_service=None,
                 flora_service=None, agrovet_service=None, weather_service=None):
        """Initialize with PostgreSQL, Africa's Talking, Email, Flora AI, Agrovet, and Weather."""
        self.db = db_service
        self.sms_service = sms_service
        self.flora = flora_service
        self.email_service = email_service
        self.agrovet = agrovet_service
        self.weather = weather_service

        # Initialize email service if not provided
        if not self.email_service:
            try:
                from email_service import EmailService
                self.email_service = EmailService()
            except Exception as e:
                logger.warning(f"Email service not available: {e}")
                self.email_service = None

        # Initialize Flora AI (RAG) if not provided
        if not self.flora:
            try:
                from flora_ai_gemini import FloraAIService
                self.flora = FloraAIService(db_service=self.db)
            except Exception as e:
                logger.warning(f"Flora AI not available for RAG alerts: {e}")
                self.flora = None

        # Initialize Agrovet service if not provided
        if not self.agrovet and AGROVET_AVAILABLE:
            try:
                self.agrovet = AgrovetRecommendationService()
                logger.info("✓ AgrovetRecommendationService auto-initialized")
            except Exception as e:
                logger.warning(f"Agrovet service not available: {e}")
                self.agrovet = None

        # Initialize Weather Forecast service if not provided
        if not self.weather:
            try:
                from weather_forecast_service import WeatherForecastService
                self.weather = WeatherForecastService(db_service=self.db)
                logger.info("✓ WeatherForecastService auto-initialized for smart alerts")
            except Exception as e:
                logger.warning(f"Weather service not available for alerts: {e}")
                self.weather = None

        logger.info("Smart Alert Service initialized")
    
    def classify_bloom_risk(self, bloom_confidence: float, ndvi: float) -> str:
        """
        Classify bloom risk based on confidence and NDVI
        
        Returns: 'Low', 'Moderate', or 'High'
        """
        if bloom_confidence >= 0.7 and ndvi > 0.6:
            return 'High'
        elif bloom_confidence >= 0.5 or ndvi > 0.5:
            return 'Moderate'
        else:
            return 'Low'
    
    def classify_ndvi_status(self, ndvi: float, crop: str = None) -> Tuple[str, str]:
        """
        Classify NDVI into crop health status
        
        Returns: (status_key, status_description)
        """
        if ndvi < 0.3:
            return 'low_ndvi', 'Crop stress detected'
        elif ndvi < 0.6:
            return 'medium_ndvi', 'Moderate crop health'
        else:
            return 'high_ndvi', 'Healthy vegetation'
    
    def determine_growth_stage(self, crop: str, month: int) -> str:
        """Determine likely growth stage based on crop and month (Kenya calendar)"""
        # Kenya's main seasons: Long rains (Mar-May), Short rains (Oct-Dec)
        
        growth_stages = {
            'maize': {
                'long_rains': {3: 'vegetative', 4: 'vegetative', 5: 'flowering'},
                'short_rains': {10: 'vegetative', 11: 'vegetative', 12: 'flowering'}
            },
            'coffee': {
                'long_rains': {1: 'flowering', 2: 'flowering', 5: 'flowering', 6: 'flowering'},
                'all': 'dormancy'
            },
            'rice': {
                'long_rains': {3: 'vegetative', 4: 'vegetative', 5: 'flowering'},
                'short_rains': {10: 'vegetative', 11: 'vegetative', 12: 'flowering'}
            },
            'beans': {
                'long_rains': {3: 'vegetative', 4: 'flowering', 5: 'flowering'},
                'short_rains': {10: 'vegetative', 11: 'flowering', 12: 'flowering'}
            },
            'tea': {'all': 'plucking'},
            'sugarcane': {'all': 'vegetative'},
            'wheat': {
                'long_rains': {3: 'vegetative', 4: 'flowering', 5: 'flowering'}
            }
        }
        
        crop_stages = growth_stages.get(crop, {})
        
        # Check season-specific stages
        if 3 <= month <= 5:  # Long rains
            stages = crop_stages.get('long_rains', {})
            return stages.get(month, crop_stages.get('all', 'vegetative'))
        elif 10 <= month <= 12:  # Short rains
            stages = crop_stages.get('short_rains', {})
            return stages.get(month, crop_stages.get('all', 'vegetative'))
        else:
            return crop_stages.get('all', 'vegetative')
    
    def get_crop_advice(self, crop: str, growth_stage: str, ndvi_status: str, language: str = 'en') -> str:
        """Get specific advice for crop, stage, and NDVI status"""
        crop_data = CROP_ADVICE.get(crop, {})
        lang_data = crop_data.get(language, crop_data.get('en', {}))
        stage_data = lang_data.get(growth_stage, {})
        
        advice = stage_data.get(ndvi_status, '')
        
        if not advice:
            # Fallback generic advice
            if language == 'sw':
                advice = f"Fuatilia mazao yako kwa makini. Hakikisha maji na mbolea ni ya kutosha."
            else:
                advice = f"Monitor your {crop} carefully. Ensure adequate water and nutrients."
        
        return advice
    
    def generate_sms_alert(self, alert: SmartAlert) -> str:
        """
        Generate complete SMS message from alert data
        Uses actual Earth observation data
        """
        region_data = KENYA_REGIONS.get(alert.region, {})
        region_name = region_data.get(f'name_{alert.language}', alert.region.replace('_', ' ').title())
        
        # Risk emoji
        risk_emoji = {'High': '🔴', 'Moderate': '🟡', 'Low': '🟢'}.get(alert.bloom_risk, '🟢')
        
        if alert.language == 'sw':
            # Swahili template
            header = f"🌾 Smart Shamba – {region_name}"
            greeting = f"Habari {alert.farmer_name},"
            
            data_line = f"Data za satelaiti ({alert.data_source}) zinaonyesha afya ya mazao: {alert.health_score:.0f}/100"
            
            bloom_line = f"{risk_emoji} Hatari ya kuchanua: {alert.bloom_risk} ({alert.bloom_confidence*100:.0f}%)"
            
            advice_line = f"💡 Ushauri: {alert.advice}"
            
            footer = "— Smart Shamba"
            
            sms = f"{header}\n{greeting} {data_line}.\n{bloom_line}\n{advice_line}\n{footer}"
            
        else:
            # English template
            header = f"🌾 Smart Shamba – {region_name}"
            greeting = f"Hello {alert.farmer_name},"
            
            data_line = f"Satellite data ({alert.data_source}) shows crop health: {alert.health_score:.0f}/100"
            
            bloom_line = f"{risk_emoji} Bloom activity: {alert.bloom_risk} ({alert.bloom_confidence*100:.0f}% confidence)"
            
            advice_line = f"👉 Advice: {alert.advice}"
            
            footer = "— Powered by Smart Shamba"
            
            sms = f"{header}\n{greeting} {data_line}.\n{bloom_line}\n{advice_line}\n{footer}"
        
        return sms
    
    def send_welcome_alert(self, farmer_data: Dict, bloom_data: Dict) -> Dict:
        """
        Send welcome alert with current bloom status when farmer signs up
        Uses actual EO data
        
        For web users (with email): Sends both email and SMS
        For USSD users (no email): Sends only SMS
        """
        # Extract farmer info
        name = farmer_data.get('name', 'Farmer')
        phone = farmer_data.get('phone')
        email = farmer_data.get('email')  # May be None for USSD users
        region = farmer_data.get('region', 'central')
        county = farmer_data.get('county', 'Kenya')
        crops = farmer_data.get('crops', ['maize'])
        language = farmer_data.get('language', 'en')
        
        # Extract bloom data
        ndvi_mean = bloom_data.get('ndvi_mean', 0.5)
        health_score = bloom_data.get('health_score', 50.0)
        data_source = bloom_data.get('data_source', 'Satellite')
        
        # Get bloom confidence for primary crop
        bloom_months = bloom_data.get('bloom_months', [])
        bloom_scores = bloom_data.get('bloom_scores', [])
        
        current_month = datetime.now().month - 1  # 0-indexed
        bloom_confidence = bloom_scores[current_month] if current_month < len(bloom_scores) else 0.5
        
        # Classify bloom risk for overall status
        bloom_risk = self.classify_bloom_risk(bloom_confidence, ndvi_mean)
        
        # ====================================
        # SEND EMAIL (if web user has email)
        # ====================================
        email_sent = False
        if email and self.email_service:
            try:
                email_bloom_data = {
                    'ndvi_mean': ndvi_mean,
                    'health_score': health_score,
                    'bloom_risk': bloom_risk,
                    'bloom_confidence': bloom_confidence
                }
                email_result = self.email_service.send_welcome_email(farmer_data, email_bloom_data)
                email_sent = email_result.get('success', False)
                if email_sent:
                    logger.info(f"✓ Welcome email sent to {email}")
            except Exception as e:
                logger.error(f"✗ Failed to send welcome email: {e}")
        
        # ====================================
        # SEND SMS (for all users)
        # ====================================
        results = []
        
        for crop in crops[:2]:  # Send for first 2 crops to avoid too many SMS
            # Determine growth stage
            growth_stage = self.determine_growth_stage(crop, datetime.now().month)
            
            # Classify NDVI status
            ndvi_status, _ = self.classify_ndvi_status(ndvi_mean, crop)
            
            # Get crop-specific advice
            advice = self.get_crop_advice(crop, growth_stage, ndvi_status, language)
            
            # Classify bloom risk
            bloom_risk = self.classify_bloom_risk(bloom_confidence, ndvi_mean)
            
            # Create alert object
            alert = SmartAlert(
                farmer_name=name,
                phone=phone,
                region=region,
                crop=crop,
                language=language,
                ndvi_value=ndvi_mean,
                health_score=health_score,
                bloom_risk=bloom_risk,
                bloom_confidence=bloom_confidence,
                growth_stage=growth_stage,
                advice=advice,
                data_source=data_source,
                timestamp=datetime.now()
            )
            
            # Generate SMS
            sms_text = self.generate_sms_alert(alert)
            
            # Send via Africa's Talking if available
            sms_sent = False
            if self.sms_service:
                try:
                    result = self.sms_service.send_sms(phone, sms_text)
                    sms_sent = result.get('success', False)
                    logger.info(f"SMS sent to {phone} for {crop}")
                except Exception as e:
                    logger.error(f"Failed to send SMS: {e}")
            
            # Store alert in PostgreSQL
            if self.db:
                try:
                    self.db.log_alert(
                        str(farmer_data.get('id', farmer_data.get('_id', ''))),
                        {
                            'alert_type': 'welcome',
                            'farmer_phone': phone,
                            'crop': crop,
                            'message': sms_text,
                            'bloom_risk': bloom_risk,
                            'health_score': health_score,
                            'ndvi': ndvi_mean,
                            'data_source': data_source,
                            'sent_sms': sms_sent,
                            'sent_email': email_sent,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to store alert in PostgreSQL: {e}")
            
            results.append({
                'crop': crop,
                'phone': phone,
                'sms_text': sms_text,
                'sms_sent': sms_sent,
                'bloom_risk': bloom_risk
            })
        
        return {
            'success': True,
            'alerts_sent': len(results),
            'email_sent': email_sent,
            'has_email': email is not None,
            'details': results
        }
    
    def send_crop_alert(self, farmer_data: Dict, crop: str, alert_data: Dict) -> Dict:
        """
        Send crop-specific alert (bloom/climate update) to farmer
        
        For web users (with email): Sends both email and SMS
        For USSD users (no email): Sends only SMS
        """
        # Extract farmer info
        name = farmer_data.get('name', 'Farmer')
        phone = farmer_data.get('phone')
        email = farmer_data.get('email')
        region = farmer_data.get('region', 'central')
        language = farmer_data.get('language', 'en')
        
        # Extract alert data
        ndvi_mean = alert_data.get('ndvi', 0.5)
        health_score = alert_data.get('health_score', 50.0)
        bloom_confidence = alert_data.get('bloom_confidence', 0.5)
        data_source = alert_data.get('data_source', 'Satellite')
        advice = alert_data.get('advice', '')
        
        # Classify bloom risk
        bloom_risk = self.classify_bloom_risk(bloom_confidence, ndvi_mean)
        
        # ====================================
        # SEND EMAIL (if web user has email)
        # ====================================
        email_sent = False
        if email and self.email_service:
            try:
                email_alert_data = {
                    'crop': crop,
                    'health_score': health_score,
                    'bloom_risk': bloom_risk,
                    'ndvi': ndvi_mean,
                    'advice': advice,
                    'data_source': data_source
                }
                email_result = self.email_service.send_alert_email(farmer_data, email_alert_data)
                email_sent = email_result.get('success', False)
                if email_sent:
                    logger.info(f"✓ Alert email sent to {email} for {crop}")
            except Exception as e:
                logger.error(f"✗ Failed to send alert email: {e}")
        
        # ====================================
        # SEND SMS (for all users)
        # ====================================
        # Determine growth stage
        growth_stage = self.determine_growth_stage(crop, datetime.now().month)
        
        # Classify NDVI status
        ndvi_status, _ = self.classify_ndvi_status(ndvi_mean, crop)
        
        # Get crop-specific advice if not provided
        if not advice:
            advice = self.get_crop_advice(crop, growth_stage, ndvi_status, language)
        
        # Create alert object
        alert = SmartAlert(
            farmer_name=name,
            phone=phone,
            region=region,
            crop=crop,
            language=language,
            ndvi_value=ndvi_mean,
            health_score=health_score,
            bloom_risk=bloom_risk,
            bloom_confidence=bloom_confidence,
            growth_stage=growth_stage,
            advice=advice,
            data_source=data_source,
            timestamp=datetime.now()
        )
        
        # Generate SMS
        sms_text = self.generate_sms_alert(alert)
        
        # Send via Africa's Talking if available
        sms_sent = False
        if self.sms_service:
            try:
                result = self.sms_service.send_sms(phone, sms_text)
                sms_sent = result.get('success', False)
                logger.info(f"✓ SMS sent to {phone} for {crop}")
            except Exception as e:
                logger.error(f"✗ Failed to send SMS: {e}")
        
        # Store alert in PostgreSQL
        if self.db:
            try:
                self.db.log_alert(
                    str(farmer_data.get('id', farmer_data.get('_id', ''))),
                    {
                        'alert_type': 'crop_update',
                        'farmer_phone': phone,
                        'farmer_email': email,
                        'crop': crop,
                        'message': sms_text,
                        'bloom_risk': bloom_risk,
                        'health_score': health_score,
                        'ndvi': ndvi_mean,
                        'data_source': data_source,
                        'sent_sms': sms_sent,
                        'sent_email': email_sent,
                    }
                )
            except Exception as e:
                logger.error(f"✗ Failed to store alert in PostgreSQL: {e}")
        
        return {
            'success': True,
            'sms_sent': sms_sent,
            'email_sent': email_sent,
            'has_email': email is not None,
            'crop': crop,
            'bloom_risk': bloom_risk
        }

    # ------------------------------------------------------------------ #
    #  RAG-powered Smart Alert (Gemini + pgvector + sensor data)
    # ------------------------------------------------------------------ #

    def generate_rag_alert(self, farmer_data: Dict, sensor_data: Optional[Dict] = None,
                           satellite_data: Optional[Dict] = None) -> Dict:
        """
        Generate a RAG-augmented alert using the full Smart Shamba pipeline.

        Flow:
        1. Maps farmer phone → farm profile from PostgreSQL.
        2. Dynamic retrieval: latest sensor readings + satellite data from PG.
        3. Static retrieval: pgvector knowledge base search.
        4. Augmented prompt → Gemini (dual output: SMS brief + web detailed).
        5. Send SMS via Africa's Talking; parse for product recommendations.
        6. Log to PostgreSQL alerts table.

        Returns dict with sms_text, web_text, system_action, etc.
        """
        phone = farmer_data.get('phone', '')
        name = farmer_data.get('name', 'Farmer')
        county = farmer_data.get('county', '')
        crops = farmer_data.get('crops', [])
        farm_size = farmer_data.get('farm_size', 0)
        language = farmer_data.get('language', 'en')

        # ------- 1. Dynamic retrieval: sensor + satellite + weather from PG ------- #
        sensor_context = ""
        if sensor_data:
            sensor_context = (
                f"\n**IoT SENSOR TELEMETRY:**\n"
                f"- Soil pH: {sensor_data.get('soil_ph', sensor_data.get('ph', 'N/A'))}\n"
                f"- Soil Moisture: {sensor_data.get('soil_moisture_pct', sensor_data.get('moisture', 'N/A'))}%\n"
                f"- NPK: N={sensor_data.get('soil_nitrogen', sensor_data.get('nitrogen', 'N/A'))}mg/kg, "
                f"P={sensor_data.get('soil_phosphorus', sensor_data.get('phosphorus', 'N/A'))}mg/kg, "
                f"K={sensor_data.get('soil_potassium', sensor_data.get('potassium', 'N/A'))}mg/kg\n"
                f"- Temperature: {sensor_data.get('temperature_c', sensor_data.get('temperature', 'N/A'))}°C\n"
                f"- Humidity: {sensor_data.get('humidity_pct', sensor_data.get('humidity', 'N/A'))}%\n"
                f"- Wind: {sensor_data.get('wind_speed_ms', 'N/A')} m/s\n"
                f"- Light: {sensor_data.get('light_lux', 'N/A')} lux\n"
                f"- Pressure: {sensor_data.get('pressure_hpa', 'N/A')} hPa\n"
                f"- CO₂: {sensor_data.get('co2_ppm', 'N/A')} ppm\n"
                f"- Rainfall: {sensor_data.get('rainfall_mm', 'N/A')} mm\n"
            )
        elif self.db:
            # Try to pull sensor readings from farmer's farms
            farmer_id = farmer_data.get('id')
            if farmer_id:
                try:
                    from database.models import Farm
                    from sqlmodel import Session, select
                    from database.postgres_service import engine
                    with Session(engine) as session:
                        farms = session.exec(
                            select(Farm).where(Farm.farmer_id == int(farmer_id))
                        ).all()
                        for farm in farms:
                            readings = self.db.get_sensor_readings(farm.id, hours=24)
                            if readings:
                                latest = readings[0]
                                sensor_context = (
                                    f"\n**IoT SENSOR TELEMETRY (latest from farm):**\n"
                                    f"- Soil pH: {latest.get('soil_ph', 'N/A')}\n"
                                    f"- Soil Moisture: {latest.get('soil_moisture_pct', 'N/A')}%\n"
                                    f"- NPK: N={latest.get('soil_nitrogen', 'N/A')}mg/kg, "
                                    f"P={latest.get('soil_phosphorus', 'N/A')}mg/kg, "
                                    f"K={latest.get('soil_potassium', 'N/A')}mg/kg\n"
                                    f"- Temperature: {latest.get('temperature_c', 'N/A')}°C\n"
                                    f"- Humidity: {latest.get('humidity_pct', 'N/A')}%\n"
                                    f"- Wind: {latest.get('wind_speed_ms', 'N/A')} m/s\n"
                                    f"- Light: {latest.get('light_lux', 'N/A')} lux\n"
                                    f"- Pressure: {latest.get('pressure_hpa', 'N/A')} hPa\n"
                                    f"- CO₂: {latest.get('co2_ppm', 'N/A')} ppm\n"
                                    f"- Rainfall: {latest.get('rainfall_mm', 'N/A')} mm\n"
                                )
                                break
                except Exception as e:
                    logger.debug(f"No sensor readings available: {e}")

        sat_context = ""
        if satellite_data:
            sat_context = (
                f"\n**SATELLITE DATA ({satellite_data.get('data_source', 'NASA')}):**\n"
                f"- NDVI (Crop Health): {satellite_data.get('ndvi', 'N/A')}\n"
                f"- NDWI (Water Index): {satellite_data.get('ndwi', 'N/A')}\n"
                f"- Temperature: {satellite_data.get('temperature_c', 'N/A')}°C\n"
                f"- Rainfall: {satellite_data.get('rainfall_mm', 'N/A')}mm\n"
                f"- Soil Moisture (satellite): {satellite_data.get('soil_moisture_pct', 'N/A')}%\n"
                f"- Soil pH (satellite): {satellite_data.get('soil_ph', 'N/A')}\n"
                f"- Bloom Probability: {satellite_data.get('bloom_probability', 'N/A')}\n"
            )
        elif self.db and hasattr(self.db, 'get_county_details'):
            try:
                cd = self.db.get_county_details(county)
                if cd and 'error' not in cd:
                    sat = cd.get('satellite_data', {})
                    sat_context = (
                        f"\n**SATELLITE DATA (from database):**\n"
                        f"- NDVI: {sat.get('ndvi', 'N/A')}\n"
                        f"- NDWI: {sat.get('ndwi', 'N/A')}\n"
                        f"- Temperature: {sat.get('temperature_c', 'N/A')}°C\n"
                        f"- Rainfall: {sat.get('rainfall_mm', 'N/A')}mm\n"
                        f"- Soil Moisture: {sat.get('soil_moisture_pct', 'N/A')}%\n"
                        f"- Soil pH: {sat.get('soil_ph', 'N/A')}\n"
                        f"- Bloom Prob: {sat.get('bloom_probability', 'N/A')}\n"
                    )
            except Exception:
                pass

        # ------- Weather forecast context ------- #
        weather_context = ""
        if self.weather:
            try:
                import asyncio
                weather_data = asyncio.get_event_loop().run_until_complete(
                    self._fetch_weather_for_farmer(farmer_data)
                )
                if weather_data and 'error' not in weather_data:
                    days = weather_data.get('daily_forecasts', [])[:5]
                    ag = weather_data.get('agriculture_summary', {})
                    insights = weather_data.get('insights', [])

                    weather_context = "\n**WEATHER FORECAST (Google Weather API):**\n"
                    if ag:
                        weather_context += (
                            f"- 10-day total rainfall: {ag.get('total_rain_10d_mm', 'N/A')}mm\n"
                            f"- Rainy days: {ag.get('rainy_days', 'N/A')}\n"
                            f"- Max temperature: {ag.get('max_temperature_c', 'N/A')}°C\n"
                            f"- Min temperature: {ag.get('min_temperature_c', 'N/A')}°C\n"
                        )
                    for d in days[:3]:
                        weather_context += (
                            f"  {d.get('date', '?')}: "
                            f"{d.get('min_temp_c', '?')}–{d.get('max_temp_c', '?')}°C, "
                            f"rain {d.get('precipitation_mm', 0):.0f}mm "
                            f"({d.get('precipitation_probability', 0)}%), "
                            f"wind {d.get('wind_speed_kmh', 0):.0f}km/h\n"
                        )
                    if insights:
                        weather_context += "\n**WEATHER INSIGHTS:**\n"
                        for ins in insights[:3]:
                            weather_context += f"- [{ins.get('severity', 'info').upper()}] {ins.get('message', '')}\n"
            except Exception as e:
                logger.debug(f"Weather context for RAG failed: {e}")

        # ------- 2. Static retrieval via pgvector RAG ------- #
        rag_context = ""
        if self.flora:
            crop_query = f"{', '.join(crops)} farming advice {county} Kenya"
            snippets = self.flora._retrieve_knowledge(crop_query, top_k=3)
            if snippets:
                rag_context = "\n**KNOWLEDGE BASE (pgvector RAG):**\n" + "\n---\n".join(snippets)

        # ------- 3. Augmented prompt → Gemini ------- #
        system_prompt = (
            "**ROLE:**\n"
            'You are the "Smart Shamba" Chief Agronomist Agent. Your goal is to '
            "orchestrate farm operations by synthesizing data from satellite analysis "
            "(NASA/Sentinel-2), ground IoT sensors (ESP32), weather forecasts "
            "(Google Weather API), and local supply chains.\n\n"
            "**INPUT DATA YOU WILL RECEIVE:**\n"
            "1. **Farmer Profile:** Name, Location, Farm Size, Crop Type.\n"
            "2. **Soil Telemetry:** Current pH, Moisture, N-P-K, Temperature, Humidity, "
            "Wind, Light, Pressure, CO₂ (from IoT sensors).\n"
            "3. **Satellite Data:** NDVI, NDWI, rainfall, soil moisture, bloom probability.\n"
            "4. **Weather Forecast:** 10-day forecast with rainfall, temperature, wind, "
            "humidity. Includes agricultural insights (heavy rain, dry spell, heat stress, "
            "planting windows, spray windows, bloom risk).\n"
            "5. **Knowledge Base:** Relevant agricultural knowledge from our database.\n\n"
            "**YOUR INSTRUCTIONS:**\n"
            "Process ALL data sources to provide a \"Smart Action\" plan.\n\n"
            "**STEP 1: REASONING TRACE (Internal Monologue)**\n"
            "Before generating a response, analyze step-by-step in an "
            "`[INTERNAL_REASONING]` block. You must:\n"
            "* **Diagnose:** Identify the core issue based on ALL telemetry.\n"
            "* **Contextualize:** Cross-reference weather forecast with satellite + IoT data. "
            "If lime is needed but heavy rain is forecast, REJECT immediate application. "
            "If drought is forecast but soil moisture is currently adequate, advise preemptive irrigation.\n"
            "* **Extreme Events:** Flag any extreme weather (heatwave, frost, heavy rain, "
            "drought, high wind) or sensor anomalies (sudden moisture drop, pH crash, NPK depletion).\n"
            "* **Optimize:** Select the best action plan considering the 10-day forecast.\n"
            "* **Calculate:** Compute exact quantity based on Farm Size.\n\n"
            "**STEP 2: FARMER COMMUNICATION**\n"
            "Generate a concise, actionable message in the `[FARMER_SMS]` block.\n"
            "* Keep it under 160 characters if possible.\n"
            "* Be authoritative but helpful.\n"
            "* Include specific quantities and actions.\n\n"
            "**STEP 3: WEB DETAILED**\n"
            "Generate a detailed explanation in the `[WEB_DETAILED]` block.\n"
            "* For the web dashboard — can be longer.\n"
            "* Include diagnosis, reasoning, and full action plan.\n\n"
            "**STEP 4: SYSTEM ACTION**\n"
            "Generate a JSON object in the `[SYSTEM_ACTION]` block for backend triggers.\n\n"
            "---\n"
            "**OUTPUT FORMAT:**\n"
            "Strictly follow this format:\n\n"
            "[INTERNAL_REASONING]\n"
            "... your step-by-step strategic analysis ...\n\n"
            "[FARMER_SMS]\n"
            "... the SMS message ...\n\n"
            "[WEB_DETAILED]\n"
            "... detailed web dashboard text ...\n\n"
            "[SYSTEM_ACTION]\n"
            '{"action_type": "...", "item": "...", "quantity": "...", "vendor_id": "..."}\n'
        )

        lang_instruction = (
            "\nIMPORTANT: Write the FARMER_SMS and WEB_DETAILED sections in Kiswahili."
            if language == "sw"
            else "\nIMPORTANT: Write the FARMER_SMS and WEB_DETAILED sections in English."
        )

        farmer_profile = (
            f"\n**FARMER PROFILE:**\n"
            f"- Name: {name}\n"
            f"- County: {county}\n"
            f"- Farm Size: {farm_size} acres\n"
            f"- Crops: {', '.join(crops)}\n"
            f"- Language: {language}\n"
        )

        full_prompt = (
            system_prompt + lang_instruction + farmer_profile
            + sensor_context + sat_context + weather_context + rag_context
        )

        # Call Gemini via Flora AI or directly
        sms_text = ""
        web_text = ""
        system_action = {}

        if self.flora and self.flora.gemini_available:
            try:
                raw_text = self.flora._call_gemini(full_prompt, max_tokens=1200)

                # Parse structured output
                sms_text = self._extract_section(raw_text, "FARMER_SMS")
                web_text = self._extract_section(raw_text, "WEB_DETAILED")

                import json as _json
                action_str = self._extract_section(raw_text, "SYSTEM_ACTION")
                if action_str:
                    try:
                        system_action = _json.loads(action_str)
                    except Exception:
                        system_action = {"raw": action_str}

            except Exception as e:
                logger.error(f"RAG alert generation failed: {e}")

        # Fallback: use template-based alert if Gemini unavailable
        if not sms_text:
            ndvi = (satellite_data or {}).get('ndvi', 0.5)
            bloom_conf = (satellite_data or {}).get('bloom_confidence', 0.5)
            crop = crops[0] if crops else 'maize'
            growth_stage = self.determine_growth_stage(crop, datetime.now().month)
            ndvi_status, _ = self.classify_ndvi_status(ndvi, crop)
            advice = self.get_crop_advice(crop, growth_stage, ndvi_status, language)
            bloom_risk = self.classify_bloom_risk(bloom_conf, ndvi)

            alert = SmartAlert(
                farmer_name=name, phone=phone, region=farmer_data.get('region', ''),
                crop=crop, language=language, ndvi_value=ndvi,
                health_score=(satellite_data or {}).get('health_score', 50.0),
                bloom_risk=bloom_risk, bloom_confidence=bloom_conf,
                growth_stage=growth_stage, advice=advice,
                data_source=(satellite_data or {}).get('data_source', 'Satellite'),
                timestamp=datetime.now(),
            )
            sms_text = self.generate_sms_alert(alert)
            web_text = sms_text

        # ------- 4. Send SMS ------- #
        sms_sent = False
        if self.sms_service and phone:
            try:
                result = self.sms_service.send_sms(phone, sms_text)
                sms_sent = result.get('success', False)
            except Exception as e:
                logger.error(f"Failed to send RAG SMS: {e}")

        # ------- 5. Log to PostgreSQL ------- #
        if self.db:
            try:
                self.db.log_alert(
                    str(farmer_data.get('id', farmer_data.get('_id', ''))),
                    {
                        'alert_type': 'rag_smart_alert',
                        'farmer_phone': phone,
                        'crop': ', '.join(crops),
                        'message': sms_text,
                        'channel': 'sms',
                        'delivered': sms_sent,
                        'metadata': {
                            'web_message': web_text,
                            'system_action': str(system_action),
                        },
                    }
                )
            except Exception as e:
                logger.error(f"Failed to log RAG alert: {e}")

        return {
            'success': True,
            'sms_text': sms_text,
            'web_text': web_text,
            'system_action': system_action,
            'sms_sent': sms_sent,
        }

    # ------------------------------------------------------------------ #
    #  Farm Condition Evaluator — compares readings vs optimal thresholds
    # ------------------------------------------------------------------ #

    def evaluate_farm_conditions(
        self,
        crop: str,
        sensor_data: Optional[Dict] = None,
        satellite_data: Optional[Dict] = None,
    ) -> FarmConditionReport:
        """
        Compare every available metric against the crop's optimal range.

        Args:
            crop:           Crop name (e.g. 'maize', 'coffee')
            sensor_data:    Dict from IoT sensors (temperature_c, humidity_pct,
                            soil_moisture_pct, soil_ph, etc.)
            satellite_data: Dict from GEE (ndvi, ndwi, rainfall_mm, temperature_mean_c)

        Returns:
            FarmConditionReport with optimal_metrics, deviations, overall score.
        """
        ranges = CROP_OPTIMAL_RANGES.get(crop, CROP_OPTIMAL_RANGES.get('maize', {}))

        # Merge available readings into a single dict
        readings: Dict[str, float] = {}
        if sensor_data:
            for key in ('soil_ph', 'soil_moisture_pct', 'temperature_c',
                        'humidity_pct'):
                val = sensor_data.get(key) or sensor_data.get(key.replace('_c', ''))
                if val is not None:
                    try:
                        readings[key] = float(val)
                    except (ValueError, TypeError):
                        pass
            # Aliases
            if 'ph' in sensor_data and 'soil_ph' not in readings:
                try: readings['soil_ph'] = float(sensor_data['ph'])
                except (ValueError, TypeError): pass
            if 'moisture' in sensor_data and 'soil_moisture_pct' not in readings:
                try: readings['soil_moisture_pct'] = float(sensor_data['moisture'])
                except (ValueError, TypeError): pass
            if 'temperature' in sensor_data and 'temperature_c' not in readings:
                try: readings['temperature_c'] = float(sensor_data['temperature'])
                except (ValueError, TypeError): pass
            if 'humidity' in sensor_data and 'humidity_pct' not in readings:
                try: readings['humidity_pct'] = float(sensor_data['humidity'])
                except (ValueError, TypeError): pass

        if satellite_data:
            for key in ('ndvi', 'ndwi', 'rainfall_mm'):
                val = satellite_data.get(key)
                if val is not None:
                    try:
                        readings[key] = float(val)
                    except (ValueError, TypeError):
                        pass
            # Temperature from satellite if not from sensors
            if 'temperature_c' not in readings:
                for alias in ('temperature_mean_c', 'temperature_c', 'temp'):
                    val = satellite_data.get(alias)
                    if val is not None:
                        try:
                            readings['temperature_c'] = float(val)
                        except (ValueError, TypeError):
                            pass
                        break

        optimal_metrics: List[str] = []
        deviations: List[MetricDeviation] = []

        for metric, (opt_min, opt_max, unit, desc) in ranges.items():
            if metric not in readings:
                continue

            value = readings[metric]
            display_name, display_unit = METRIC_DISPLAY.get(metric, (metric, unit))

            if opt_min <= value <= opt_max:
                optimal_metrics.append(metric)
            else:
                # Determine direction and severity
                if value < opt_min:
                    direction = 'low'
                    distance = opt_min - value
                    range_span = opt_max - opt_min if opt_max != opt_min else 1
                    pct = (distance / range_span) * 100
                else:
                    direction = 'high'
                    distance = value - opt_max
                    range_span = opt_max - opt_min if opt_max != opt_min else 1
                    pct = (distance / range_span) * 100

                # Severity: >50% outside range = critical, >20% = warning, else info
                if pct > 50:
                    severity = 'critical'
                elif pct > 20:
                    severity = 'warning'
                else:
                    severity = 'info'

                # Human-readable description
                if direction == 'low':
                    desc_text = (
                        f"{display_name} is too low at {value:.2f}{display_unit} "
                        f"(optimal: {opt_min}–{opt_max}{display_unit})"
                    )
                else:
                    desc_text = (
                        f"{display_name} is too high at {value:.2f}{display_unit} "
                        f"(optimal: {opt_min}–{opt_max}{display_unit})"
                    )

                deviations.append(MetricDeviation(
                    metric=metric,
                    display_name=display_name,
                    value=value,
                    optimal_min=opt_min,
                    optimal_max=opt_max,
                    unit=display_unit,
                    severity=severity,
                    direction=direction,
                    description=desc_text,
                    pct_deviation=round(pct, 1),
                ))

        # Sort deviations by severity (critical first) then by % deviation
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        deviations.sort(key=lambda d: (severity_order.get(d.severity, 3), -d.pct_deviation))

        # Overall score: 100 if all optimal, reduced proportionally
        total_checked = len(optimal_metrics) + len(deviations)
        if total_checked == 0:
            score = 50.0  # No data
            status = 'warning'
        else:
            base = (len(optimal_metrics) / total_checked) * 100
            # Penalise for severity
            penalty = sum(
                15 if d.severity == 'critical' else 8 if d.severity == 'warning' else 3
                for d in deviations
            )
            score = max(0, min(100, base - penalty))

            if not deviations:
                status = 'optimal'
            elif any(d.severity == 'critical' for d in deviations):
                status = 'critical'
            elif any(d.severity == 'warning' for d in deviations):
                status = 'warning'
            else:
                status = 'good'

        return FarmConditionReport(
            crop=crop,
            status=status,
            overall_score=round(score, 1),
            optimal_metrics=optimal_metrics,
            deviations=deviations,
        )

    # ------------------------------------------------------------------ #
    #  Disease Detection Alert (from ESP32-CAM + BloomVisionCNN)
    # ------------------------------------------------------------------ #

    def generate_disease_alert(
        self,
        farmer_data: Dict,
        disease_context: Dict,
        sensor_data: Optional[Dict] = None,
        satellite_data: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate an actionable alert when crop disease is detected from
        an ESP32-CAM image processed by BloomVisionCNN.

        Pipeline:
        1. pgvector RAG retrieval for disease-specific knowledge
        2. Gemini prompt with disease + farm context → SMS + web advice
        3. Agrovet product recommendations (AI-enhanced if sensor/satellite data available)
        4. SMS delivery via Africa's Talking
        5. Alert logged to PostgreSQL

        Args:
            farmer_data: {name, phone, county, crops, farm_size, language}
            disease_context: {disease_detected, confidence, image_uid}
            sensor_data: optional IoT sensor readings for AI treatment plan
            satellite_data: optional NDVI/NDWI/rainfall for AI treatment plan

        Returns:
            {sms_text, web_text, system_action, alert_sent, alert_type, agrovet_recommendation}
        """
        name = farmer_data.get('name', 'Farmer')
        phone = farmer_data.get('phone', '')
        county = farmer_data.get('county', '')
        crops = farmer_data.get('crops', [])
        language = farmer_data.get('language', 'en')
        farm_size = farmer_data.get('farm_size', 0)

        disease_name = disease_context.get('disease_detected', 'unknown')
        confidence = disease_context.get('confidence', 0)
        image_uid = disease_context.get('image_uid', '')

        # Human-readable disease names
        disease_display = {
            'leaf_blight': 'Leaf Blight',
            'rust': 'Rust Disease',
            'aphid_damage': 'Aphid Damage',
            'wilting': 'Wilting',
            'bloom_detected': 'Bloom Detected',
            'healthy': 'Healthy',
        }
        display_name = disease_display.get(disease_name, disease_name.replace('_', ' ').title())

        # ------- 1. RAG: retrieve pest/disease knowledge ------- #
        rag_context = ""
        if self.flora:
            crop_str = ', '.join(crops) if crops else 'crops'
            query = f"{display_name} treatment prevention {crop_str} Kenya"
            snippets = self.flora._retrieve_knowledge(query, top_k=3)
            if snippets:
                rag_context = "\n**KNOWLEDGE BASE (pgvector RAG):**\n" + "\n---\n".join(snippets)

        # ------- 2. Gemini prompt ------- #
        lang_note = "Kiswahili" if language == "sw" else "English"

        prompt = (
            f"**ROLE:** You are Smart Shamba's crop disease advisor.\n\n"
            f"**DISEASE DETECTED:** {display_name}\n"
            f"**Confidence:** {confidence:.0%}\n"
            f"**Image ID:** {image_uid}\n\n"
            f"**FARMER PROFILE:**\n"
            f"- Name: {name}\n"
            f"- County: {county}\n"
            f"- Farm Size: {farm_size} acres\n"
            f"- Crops: {', '.join(crops)}\n\n"
            f"{rag_context}\n\n"
            f"**INSTRUCTIONS:**\n"
            f"1. Explain what {display_name} is and how it affects the crops.\n"
            f"2. Provide IMMEDIATE actions the farmer should take.\n"
            f"3. Recommend specific treatments or organic remedies available in Kenya.\n"
            f"4. Suggest preventive measures for the future.\n"
            f"5. If confidence is low (<60%), advise the farmer to also inspect manually.\n\n"
            f"**OUTPUT FORMAT:**\n"
            f"[FARMER_SMS]\n"
            f"... concise SMS (max 160 chars) in {lang_note} ...\n\n"
            f"[WEB_DETAILED]\n"
            f"... detailed web dashboard advisory in {lang_note} ...\n\n"
            f"[SYSTEM_ACTION]\n"
            f'{{\"action_type\": \"disease_treatment\", \"disease\": \"{disease_name}\", '
            f'\"urgency\": \"high|medium|low\", \"recommended_product\": \"...\"}}\n'
        )

        sms_text = ""
        web_text = ""
        system_action = {}

        if self.flora and self.flora.gemini_available:
            try:
                raw_text = self.flora._call_gemini(prompt, max_tokens=1000)

                sms_text = self._extract_section(raw_text, "FARMER_SMS")
                web_text = self._extract_section(raw_text, "WEB_DETAILED")

                import json as _json
                action_str = self._extract_section(raw_text, "SYSTEM_ACTION")
                if action_str:
                    try:
                        system_action = _json.loads(action_str)
                    except Exception:
                        system_action = {"raw": action_str}

            except Exception as e:
                logger.error(f"Disease alert Gemini generation failed: {e}")

        # ------- Fallback if Gemini unavailable ------- #
        if not sms_text:
            if language == "sw":
                sms_text = (
                    f"⚠️ {display_name} imegunduliwa kwenye shamba lako ({confidence:.0%}). "
                    f"Tafadhali kagua mimea yako na utumie dawa zinazofaa."
                )
            else:
                sms_text = (
                    f"⚠️ {display_name} detected on your farm ({confidence:.0%}). "
                    f"Please inspect your crops and apply appropriate treatment."
                )

        if not web_text:
            web_text = (
                f"## Disease Detected: {display_name}\n\n"
                f"**Confidence:** {confidence:.0%}\n"
                f"**Image:** {image_uid}\n\n"
                f"### Recommended Actions\n"
                f"1. Inspect affected plants immediately\n"
                f"2. Remove and destroy severely affected leaves\n"
                f"3. Apply appropriate fungicide/pesticide\n"
                f"4. Consult your local agricultural extension officer\n"
            )

        # ------- 3. Agrovet product recommendations ------- #
        agrovet_recommendation = {}
        if self.agrovet and disease_name not in ('healthy', 'bloom_detected'):
            try:
                agrovet_recommendation = self.agrovet.recommend_for_condition(
                    condition=disease_name,
                    farmer_data=farmer_data,
                    sensor_data=sensor_data,
                    satellite_data=satellite_data,
                )
                if agrovet_recommendation.get('treatment_plan'):
                    # Append agrovet info to web_text
                    plan = agrovet_recommendation['treatment_plan']
                    shops = agrovet_recommendation.get('nearest_agrovets', [])
                    products = agrovet_recommendation.get('matching_products', [])
                    cost = agrovet_recommendation.get('estimated_cost', {})

                    web_text += "\n\n---\n## 🏪 Recommended Products & Nearest Agrovets\n\n"

                    # AI expert analysis (if AI-enhanced plan)
                    if plan.get('ai_enhanced'):
                        web_text += "### 🤖 AI Expert Analysis\n"
                        web_text += f"{plan.get('ai_analysis', '')}\n\n"
                        for w in plan.get('ai_warnings', []):
                            web_text += f"⚠️ {w}\n"
                        if plan.get('ai_warnings'):
                            web_text += "\n"

                    # Treatment plan
                    for t in plan.get('treatments', []):
                        web_text += (
                            f"**{t.get('product_category', 'Treatment').title()}:** "
                            f"{', '.join(t.get('names', []))}\n"
                            f"- Dose: {t.get('dose_for_farm', t.get('dose_per_acre', 'N/A'))} "
                            f"for {farm_size} acres\n"
                        )
                        if t.get('ai_adjusted_dose'):
                            web_text += f"- 🤖 AI-adjusted: {t['ai_adjusted_dose']}\n"
                        if t.get('ai_dose_note'):
                            web_text += f"- 🤖 {t['ai_dose_note']}\n"
                        web_text += f"- Application: {t.get('application', '')}\n\n"

                    # AI alternative treatments
                    if plan.get('ai_alternative_treatments'):
                        web_text += "**🤖 AI-Suggested Alternatives:**\n"
                        for alt in plan['ai_alternative_treatments']:
                            web_text += f"- {alt.get('name', '')}: {alt.get('reason', '')}\n"
                        web_text += "\n"

                    # Cultural practices
                    practices = plan.get('cultural_practices', [])
                    if practices:
                        web_text += "**Cultural Practices:**\n"
                        for p in practices[:4]:
                            web_text += f"- {p}\n"
                        web_text += "\n"

                    # AI additional recommendations
                    if plan.get('ai_additional_recommendations'):
                        web_text += "**🤖 Additional Recommendations:**\n"
                        for rec_item in plan['ai_additional_recommendations']:
                            web_text += f"- {rec_item}\n"
                        web_text += "\n"

                    # Nearest agrovets
                    if shops:
                        web_text += "### 📍 Nearest Agrovets\n"
                        for s in shops[:3]:
                            web_text += (
                                f"- **{s.get('shop_name', 'Agrovet')}** — "
                                f"{s.get('location', s.get('sub_county', ''))}, "
                                f"{s.get('county', '')}\n"
                            )
                            if s.get('phone'):
                                web_text += f"  📞 {s['phone']}\n"
                            if s.get('products'):
                                for prod in s['products'][:2]:
                                    web_text += (
                                        f"  🛒 {prod.get('name', '')} — "
                                        f"KES {prod.get('price_kes', 'N/A')}/{prod.get('unit', 'unit')}\n"
                                    )
                        web_text += "\n"

                    # Cost estimate
                    if cost:
                        web_text += (
                            f"💰 **Estimated Cost:** KES {cost.get('total_estimated', 'N/A')}\n"
                        )

                    # Append short agrovet note to SMS
                    if shops:
                        nearest = shops[0]
                        sms_agrovet = (
                            f"\n🏪 Nearest: {nearest.get('shop_name', 'Agrovet')}"
                        )
                        if nearest.get('phone'):
                            sms_agrovet += f" ({nearest['phone']})"
                        if len(sms_text) + len(sms_agrovet) <= 300:
                            sms_text += sms_agrovet

                logger.info(f"Agrovet recommendation attached for {disease_name}")
            except Exception as e:
                logger.error(f"Agrovet recommendation failed: {e}")

        # ------- 4. Send SMS ------- #
        alert_sent = False
        if phone and self.sms_service:
            try:
                sms_result = self.sms_service.send_sms(phone, sms_text)
                alert_sent = sms_result.get('success', False)
            except Exception as e:
                logger.error(f"Disease alert SMS failed: {e}")

        # ------- 4. Log to alerts table ------- #
        if self.db and hasattr(self.db, 'save_alert'):
            try:
                self.db.save_alert({
                    'phone': phone,
                    'alert_type': 'disease_detection',
                    'message': sms_text,
                    'channel': 'sms',
                    'disease': disease_name,
                    'confidence': confidence,
                    'image_uid': image_uid,
                    'severity': 'critical' if confidence > 0.8 else 'warning',
                })
            except Exception as e:
                logger.debug(f"Alert logging: {e}")

        return {
            "alert_type": "disease_detection",
            "disease": disease_name,
            "disease_display": display_name,
            "confidence": confidence,
            "sms_text": sms_text,
            "web_text": web_text,
            "system_action": system_action,
            "alert_sent": alert_sent,
            "image_uid": image_uid,
            "agrovet_recommendation": agrovet_recommendation,
        }

    # ------------------------------------------------------------------ #
    #  Condition-based Alert Generator (good-news + per-metric warnings)
    # ------------------------------------------------------------------ #

    def generate_condition_alert(
        self,
        farmer_data: Dict,
        sensor_data: Optional[Dict] = None,
        satellite_data: Optional[Dict] = None,
    ) -> Dict:
        """
        Evaluate farm conditions for each of the farmer's crops and send
        the appropriate alert:

        • ALL optimal  → 🟢 "Good news!" congratulatory alert
        • ONE deviation → 🟡 Targeted advisory about the exact metric
        • MULTIPLE      → 🔴 Prioritised alert listing worst deviations first

        Uses RAG (pgvector) to enrich advice with knowledge-base context.

        Returns dict with sms_text, web_text, report, sms_sent, etc.
        """
        name = farmer_data.get('name', 'Farmer')
        phone = farmer_data.get('phone', '')
        county = farmer_data.get('county', '')
        crops = farmer_data.get('crops', ['maize'])
        language = farmer_data.get('language', 'en')

        # ----- Pull live data from PG if not supplied ----- #
        if not sensor_data and self.db:
            farmer_id = farmer_data.get('id')
            if farmer_id:
                try:
                    from database.models import Farm
                    from sqlmodel import Session, select
                    from database.postgres_service import engine
                    with Session(engine) as session:
                        farms = session.exec(
                            select(Farm).where(Farm.farmer_id == int(farmer_id))
                        ).all()
                        for farm in farms:
                            readings = self.db.get_sensor_readings(farm.id, hours=24)
                            if readings:
                                sensor_data = readings[0]
                                break
                except Exception:
                    pass

        if not satellite_data and self.db and hasattr(self.db, 'get_county_details'):
            try:
                cd = self.db.get_county_details(county)
                if cd and 'error' not in cd:
                    satellite_data = cd.get('satellite_data', {})
            except Exception:
                pass

        # ----- Evaluate each crop ----- #
        reports: List[FarmConditionReport] = []
        for crop in crops[:3]:
            report = self.evaluate_farm_conditions(crop, sensor_data, satellite_data)
            reports.append(report)

        # Use the worst-status report as the primary
        status_order = {'critical': 0, 'warning': 1, 'good': 2, 'optimal': 3}
        reports.sort(key=lambda r: status_order.get(r.status, 4))
        primary = reports[0]

        # ----- Fetch weather forecast for context ----- #
        weather_warnings = []
        try:
            if self.weather:
                import asyncio
                weather_data = asyncio.get_event_loop().run_until_complete(
                    self._fetch_weather_for_farmer(farmer_data)
                )
                if weather_data and 'error' not in weather_data:
                    weather_events = self._check_weather_extremes(weather_data)
                    weather_warnings = [
                        e for e in weather_events
                        if e.get('severity') in ('critical', 'warning')
                    ]
        except Exception as e:
            logger.debug(f"Weather check for condition alert failed: {e}")

        # ----- Build alert messages ----- #
        status_emoji = {
            'optimal': '🟢', 'good': '🟢', 'warning': '🟡', 'critical': '🔴'
        }
        emoji = status_emoji.get(primary.status, '⚪')

        if primary.status == 'optimal':
            # ===== GOOD NEWS ALERT =====
            if language == 'sw':
                sms_text = (
                    f"🌾 Smart Shamba\n"
                    f"Habari {name}! {emoji} Hali njema!\n"
                    f"Mazao yako ({primary.crop}) yanaendelea vizuri. "
                    f"Vigezo vyote viko katika kiwango bora:\n"
                )
                for m in primary.optimal_metrics[:4]:
                    dn, _ = METRIC_DISPLAY.get(m, (m, ''))
                    sms_text += f"  ✅ {dn}\n"
                sms_text += "Endelea na kazi nzuri! — Smart Shamba"
            else:
                sms_text = (
                    f"🌾 Smart Shamba\n"
                    f"Hello {name}! {emoji} Great news!\n"
                    f"Your {primary.crop} is thriving. "
                    f"All monitored conditions are within optimal range:\n"
                )
                for m in primary.optimal_metrics[:4]:
                    dn, _ = METRIC_DISPLAY.get(m, (m, ''))
                    sms_text += f"  ✅ {dn}\n"
                sms_text += "Keep up the good work! — Smart Shamba"

            web_text = sms_text  # Can be expanded for dashboard

        elif len(primary.deviations) == 1:
            # ===== SINGLE METRIC DEVIATION =====
            d = primary.deviations[0]
            if language == 'sw':
                sms_text = (
                    f"🌾 Smart Shamba\n"
                    f"Habari {name}, {emoji} Tahadhari:\n"
                    f"{d.description}\n"
                    f"Mazao ({primary.crop}): vigezo {len(primary.optimal_metrics)} "
                    f"ni sawa lakini {d.display_name} inahitaji umakini.\n"
                )
            else:
                sms_text = (
                    f"🌾 Smart Shamba\n"
                    f"Hello {name}, {emoji} Advisory:\n"
                    f"{d.description}\n"
                    f"Your {primary.crop}: {len(primary.optimal_metrics)} metrics "
                    f"are optimal but {d.display_name} needs attention.\n"
                )

            # RAG enrichment for the specific metric
            rag_advice = ""
            if self.flora:
                try:
                    query = (
                        f"{d.display_name} {d.direction} for {primary.crop} "
                        f"in {county} Kenya — {d.description}"
                    )
                    snippets = self.flora._retrieve_knowledge(query, top_k=2)
                    if snippets:
                        rag_advice = snippets[0][:120]
                except Exception:
                    pass

            if rag_advice:
                sms_text += f"💡 {rag_advice}\n"

            sms_text += "— Smart Shamba"
            web_text = sms_text

        else:
            # ===== MULTIPLE DEVIATIONS =====
            if language == 'sw':
                sms_text = (
                    f"🌾 Smart Shamba\n"
                    f"Habari {name}, {emoji} Onyo:\n"
                    f"Mazao ({primary.crop}) — masuala {len(primary.deviations)} yamegunduliwa:\n"
                )
                for d in primary.deviations[:3]:
                    severity_sw = {'critical': '⛔', 'warning': '⚠️', 'info': 'ℹ️'}
                    sms_text += f"{severity_sw.get(d.severity, '•')} {d.description}\n"
                if primary.optimal_metrics:
                    sms_text += (
                        f"✅ Vigezo {len(primary.optimal_metrics)} viko sawa "
                        f"({', '.join(METRIC_DISPLAY.get(m, (m,''))[0] for m in primary.optimal_metrics[:3])})\n"
                    )
            else:
                sms_text = (
                    f"🌾 Smart Shamba\n"
                    f"Hello {name}, {emoji} Alert:\n"
                    f"Your {primary.crop} — {len(primary.deviations)} issue(s) detected:\n"
                )
                for d in primary.deviations[:3]:
                    severity_en = {'critical': '⛔', 'warning': '⚠️', 'info': 'ℹ️'}
                    sms_text += f"{severity_en.get(d.severity, '•')} {d.description}\n"
                if primary.optimal_metrics:
                    sms_text += (
                        f"✅ {len(primary.optimal_metrics)} metric(s) are optimal "
                        f"({', '.join(METRIC_DISPLAY.get(m, (m,''))[0] for m in primary.optimal_metrics[:3])})\n"
                    )

            sms_text += "— Smart Shamba"
            web_text = sms_text

        # ----- Append weather warnings to alerts ----- #
        if weather_warnings:
            weather_note = ""
            for ww in weather_warnings[:2]:
                msg_key = 'message_sw' if language == 'sw' else 'message_en'
                msg = ww.get(msg_key) or ww.get('message_en', '')
                if msg:
                    emoji_w = '⛔' if ww.get('severity') == 'critical' else '⚠️'
                    weather_note += f"\n{emoji_w} {msg}"
            if weather_note and len(sms_text) + len(weather_note) <= 450:
                sms_text = sms_text.replace("— Smart Shamba", "")
                sms_text += weather_note + "\n— Smart Shamba"
                web_text = sms_text

        # ----- Agrovet: detect soil deficiencies → product recommendations ----- #
        deficiency_recommendations = []
        if self.agrovet and AGROVET_AVAILABLE and sensor_data and primary.status in ('warning', 'critical'):
            try:
                deficiencies = detect_deficiencies_from_sensors(sensor_data)
                for deficiency in deficiencies[:3]:
                    rec = self.agrovet.recommend_for_condition(
                        condition=deficiency['condition'],
                        farmer_data=farmer_data,
                        sensor_data=sensor_data,
                        satellite_data=satellite_data,
                    )
                    if rec.get('treatment_plan'):
                        deficiency_recommendations.append(rec)

                if deficiency_recommendations:
                    web_text += "\n\n---\n## 🧪 Soil Deficiency Corrections\n\n"
                    for rec in deficiency_recommendations:
                        plan = rec['treatment_plan']
                        web_text += f"**{plan.get('display_name', '')}** ({plan.get('urgency', 'medium')} urgency)\n"
                        for t in plan.get('treatments', [])[:2]:
                            web_text += (
                                f"- {', '.join(t.get('names', []))}: "
                                f"{t.get('dose_for_farm', t.get('dose_per_acre', 'N/A'))} "
                                f"— {t.get('application', '')}\n"
                            )
                        shops = rec.get('nearest_agrovets', [])
                        if shops:
                            s = shops[0]
                            web_text += (
                                f"  📍 {s.get('shop_name', 'Agrovet')} in "
                                f"{s.get('sub_county', s.get('county', ''))}\n"
                            )
                        web_text += "\n"

                    # Append deficiency note to SMS if space allows
                    if deficiencies:
                        deficiency_names = [d['display_name'] for d in deficiencies[:2]]
                        note = f"\n⚠️ Soil: {', '.join(deficiency_names)} detected"
                        if len(sms_text) + len(note) <= 350:
                            sms_text += note

                    logger.info(f"Deficiency recommendations: {len(deficiency_recommendations)} conditions")
            except Exception as e:
                logger.error(f"Deficiency detection failed: {e}")

        # ----- Send SMS ----- #
        sms_sent = False
        if self.sms_service and phone:
            try:
                result = self.sms_service.send_sms(phone, sms_text)
                sms_sent = result.get('success', False)
            except Exception as e:
                logger.error(f"Condition alert SMS failed: {e}")

        # ----- Log to PostgreSQL ----- #
        if self.db:
            try:
                severity = primary.status if primary.status != 'optimal' else 'info'
                self.db.log_alert(
                    str(farmer_data.get('id', farmer_data.get('_id', ''))),
                    {
                        'alert_type': f"condition_{primary.status}",
                        'severity': severity,
                        'farmer_phone': phone,
                        'crop': primary.crop,
                        'message': sms_text,
                        'health_score': primary.overall_score,
                        'ndvi': (satellite_data or {}).get('ndvi'),
                        'data_source': (satellite_data or {}).get('data_source', 'sensor+satellite'),
                        'sent_sms': sms_sent,
                        'metadata': _json.dumps({
                            'optimal_metrics': primary.optimal_metrics,
                            'deviations': [
                                {'metric': d.metric, 'value': d.value,
                                 'severity': d.severity, 'direction': d.direction}
                                for d in primary.deviations
                            ],
                        }),
                    }
                )
            except Exception as e:
                logger.error(f"Failed to log condition alert: {e}")

        return {
            'success': True,
            'status': primary.status,
            'overall_score': primary.overall_score,
            'crop': primary.crop,
            'optimal_count': len(primary.optimal_metrics),
            'deviation_count': len(primary.deviations),
            'sms_text': sms_text,
            'web_text': web_text,
            'sms_sent': sms_sent,
            'deficiency_recommendations': deficiency_recommendations,
            'reports': [
                {
                    'crop': r.crop,
                    'status': r.status,
                    'score': r.overall_score,
                    'optimal': r.optimal_metrics,
                    'deviations': [
                        {'metric': d.metric, 'value': d.value,
                         'range': f"{d.optimal_min}–{d.optimal_max}",
                         'severity': d.severity, 'description': d.description}
                        for d in r.deviations
                    ],
                }
                for r in reports
            ],
        }

    # ------------------------------------------------------------------ #
    #  Extreme Event Detection — weather forecast + IoT sensor anomalies
    # ------------------------------------------------------------------ #

    async def _fetch_weather_for_farmer(self, farmer_data: Dict) -> Dict:
        """
        Fetch weather forecast + agricultural insights for a farmer's location.
        Uses farm lat/lon, falls back to county coordinates.
        Returns dict with daily forecasts, insights, and agriculture_summary.
        """
        if not self.weather:
            return {}

        lat = farmer_data.get('location_lat')
        lon = farmer_data.get('location_lon')

        # Fallback: use county config coordinates
        if not lat or not lon:
            county = farmer_data.get('county', '')
            if county:
                try:
                    from kenya_counties_config import KENYA_COUNTIES
                    county_info = KENYA_COUNTIES.get(county, {})
                    coords = county_info.get('coordinates', {})
                    lat = coords.get('lat')
                    lon = coords.get('lon')
                except ImportError:
                    pass

        if not lat or not lon:
            return {}

        try:
            crop = (farmer_data.get('crops') or ['maize'])[0]
            result = await self.weather.get_agricultural_insights(lat, lon, crop)
            if 'error' not in result:
                return result
        except Exception as e:
            logger.debug(f"Weather fetch for farmer failed: {e}")

        return {}

    def _check_weather_extremes(self, weather_data: Dict) -> List[Dict]:
        """
        Check weather forecast data against EXTREME_WEATHER_THRESHOLDS.
        Returns list of triggered extreme events.
        """
        events = []
        if not weather_data:
            return events

        days = weather_data.get('daily_forecasts', [])
        ag_summary = weather_data.get('agriculture_summary', {})

        for event_key, rule in EXTREME_WEATHER_THRESHOLDS.items():
            metric = rule['metric']
            threshold = rule['threshold']
            direction = rule['direction']

            # Check aggregate metrics (total_rain_10d_mm from ag_summary)
            if metric in ag_summary:
                value = ag_summary.get(metric, 0) or 0
                triggered = (
                    (direction == 'above' and value > threshold) or
                    (direction == 'below' and value < threshold)
                )
                if triggered:
                    events.append({
                        'event_type': event_key,
                        'severity': rule['severity'],
                        'value': value,
                        'threshold': threshold,
                        'metric': metric,
                        'message_en': rule['message_en'].format(value=value),
                        'message_sw': rule['message_sw'].format(value=value),
                        'source': 'weather_forecast',
                    })
                continue

            # Check daily forecasts (max/min across all days)
            if not days:
                continue

            if metric == 'max_temp_c':
                value = max((d.get('max_temp_c', 0) or 0) for d in days)
            elif metric == 'min_temp_c':
                value = min((d.get('min_temp_c', 99) or 99) for d in days)
            elif metric == 'rainfall_mm':
                # Check single-day max rainfall
                value = max((d.get('precipitation_mm', 0) or 0) for d in days)
            elif metric == 'wind_speed_kmh':
                value = max((d.get('wind_speed_kmh', 0) or 0) for d in days)
            elif metric == 'pressure_hpa':
                # Not in Google Weather daily — skip
                continue
            else:
                continue

            triggered = (
                (direction == 'above' and value > threshold) or
                (direction == 'below' and value < threshold)
            )
            if triggered:
                events.append({
                    'event_type': event_key,
                    'severity': rule['severity'],
                    'value': value,
                    'threshold': threshold,
                    'metric': metric,
                    'message_en': rule['message_en'].format(value=value),
                    'message_sw': rule['message_sw'].format(value=value),
                    'source': 'weather_forecast',
                })

        # Also include any insights from get_agricultural_insights
        for insight in weather_data.get('insights', []):
            if insight.get('severity') in ('warning', 'alert', 'critical'):
                events.append({
                    'event_type': insight.get('type', 'weather_insight'),
                    'severity': 'warning' if insight.get('severity') == 'alert' else insight['severity'],
                    'message_en': insight.get('message', ''),
                    'message_sw': '',
                    'source': 'weather_insight',
                })

        return events

    def _check_sensor_anomalies(self, readings: List[Dict]) -> List[Dict]:
        """
        Check IoT sensor readings for anomalies defined in SENSOR_ANOMALY_THRESHOLDS.
        Handles both absolute thresholds and rate-of-change detection.

        Args:
            readings: List of sensor readings dicts, ordered newest-first.
        Returns:
            List of triggered anomaly events.
        """
        events = []
        if not readings:
            return events

        latest = readings[0]

        for anomaly_key, rule in SENSOR_ANOMALY_THRESHOLDS.items():
            metric = rule['metric']
            anomaly_type = rule['type']

            if anomaly_type == 'abs_high':
                value = latest.get(metric)
                if value is not None and value > rule['threshold']:
                    events.append({
                        'event_type': anomaly_key,
                        'severity': rule['severity'],
                        'value': value,
                        'threshold': rule['threshold'],
                        'metric': metric,
                        'message_en': rule['message_en'].format(value=value),
                        'message_sw': rule['message_sw'].format(value=value),
                        'source': 'iot_sensor',
                    })

            elif anomaly_type == 'abs_low':
                value = latest.get(metric)
                if value is not None and value < rule['threshold']:
                    events.append({
                        'event_type': anomaly_key,
                        'severity': rule['severity'],
                        'value': value,
                        'threshold': rule['threshold'],
                        'metric': metric,
                        'message_en': rule['message_en'].format(value=value),
                        'message_sw': rule['message_sw'].format(value=value),
                        'source': 'iot_sensor',
                    })

            elif anomaly_type == 'rate_drop':
                # Need at least 2 readings to detect rate change
                if len(readings) < 2:
                    continue
                new_val = latest.get(metric)
                # Find the oldest reading within the window
                hours_window = rule.get('hours', 6)
                old_val = None
                for r in readings[1:]:
                    ts_str = r.get('ts', '')
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str)
                            age_hours = (datetime.utcnow() - ts).total_seconds() / 3600
                            if age_hours <= hours_window:
                                old_val = r.get(metric)
                        except (ValueError, TypeError):
                            pass

                if new_val is not None and old_val is not None and old_val > 0:
                    delta = old_val - new_val
                    delta_pct = (delta / old_val) * 100
                    if delta_pct >= rule['delta_pct']:
                        events.append({
                            'event_type': anomaly_key,
                            'severity': rule['severity'],
                            'value': new_val,
                            'metric': metric,
                            'message_en': rule['message_en'].format(
                                delta=delta_pct, hours=hours_window,
                                old=old_val, new=new_val, value=new_val,
                            ),
                            'message_sw': rule['message_sw'].format(
                                delta=delta_pct, hours=hours_window,
                                old=old_val, new=new_val, value=new_val,
                            ),
                            'source': 'iot_sensor',
                        })

        return events

    async def detect_extreme_events(
        self,
        farmer_data: Dict,
        sensor_readings: Optional[List[Dict]] = None,
        weather_data: Optional[Dict] = None,
        satellite_data: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Full extreme-event scan for one farmer:
          1. Check weather forecast for extreme weather events.
          2. Check IoT sensor readings for anomalies.
          3. Check satellite data for severe conditions (very low NDVI, high bloom).

        Returns list of extreme events, sorted by severity (critical first).
        """
        events = []

        # 1. Weather extremes
        if weather_data is None:
            weather_data = await self._fetch_weather_for_farmer(farmer_data)
        events.extend(self._check_weather_extremes(weather_data))

        # 2. IoT sensor anomalies
        if sensor_readings is None and self.db:
            # Try to get farm_id from farmer's farms
            farmer_id = farmer_data.get('id')
            if farmer_id:
                try:
                    from database.models import Farm
                    from sqlmodel import Session, select
                    from database.postgres_service import engine
                    with Session(engine) as session:
                        farms = session.exec(
                            select(Farm).where(Farm.farmer_id == int(farmer_id))
                        ).all()
                        all_readings = []
                        for farm in farms:
                            farm_readings = self.db.get_sensor_readings(
                                farm.id, hours=24
                            )
                            all_readings.extend(farm_readings)
                        sensor_readings = all_readings
                except Exception as e:
                    logger.debug(f"Could not fetch sensor readings: {e}")
                    sensor_readings = []

        if sensor_readings:
            events.extend(self._check_sensor_anomalies(sensor_readings))

        # 3. Satellite-data extremes
        if satellite_data is None and self.db:
            county = farmer_data.get('county', '')
            if county:
                try:
                    cd = self.db.get_county_details(county)
                    if cd and 'error' not in cd:
                        satellite_data = cd.get('satellite_data', {})
                except Exception:
                    pass

        if satellite_data:
            ndvi = satellite_data.get('ndvi')
            bloom_prob = satellite_data.get('bloom_probability')

            if ndvi is not None and ndvi < 0.15:
                events.append({
                    'event_type': 'severe_crop_stress',
                    'severity': 'critical',
                    'value': ndvi,
                    'metric': 'ndvi',
                    'message_en': f'Severe crop stress detected: NDVI={ndvi:.2f}. '
                                  'Investigate immediately — possible drought, pest, or disease damage.',
                    'message_sw': f'Msongo mkubwa wa mazao: NDVI={ndvi:.2f}. '
                                  'Chunguza haraka — inawezekana ni ukame, wadudu, au ugonjwa.',
                    'source': 'satellite',
                })
            if bloom_prob is not None and bloom_prob > 0.75:
                events.append({
                    'event_type': 'high_bloom_risk',
                    'severity': 'warning',
                    'value': bloom_prob,
                    'metric': 'bloom_probability',
                    'message_en': f'High algal bloom risk ({bloom_prob:.0%}). '
                                  'Avoid water from nearby lakes/ponds for irrigation.',
                    'message_sw': f'Hatari ya mwani ({bloom_prob:.0%}). '
                                  'Epuka maji ya ziwa/bwawa kwa umwagiliaji.',
                    'source': 'satellite',
                })

        # Sort: critical first
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        events.sort(key=lambda e: severity_order.get(e.get('severity', 'info'), 3))

        return events

    async def generate_extreme_event_alert(
        self, farmer_data: Dict, events: List[Dict]
    ) -> Dict:
        """
        Generate and send a consolidated alert for extreme events
        detected by detect_extreme_events().
        """
        if not events:
            return {'success': True, 'sent': False, 'reason': 'no_events'}

        name = farmer_data.get('name', 'Farmer')
        phone = farmer_data.get('phone', '')
        language = farmer_data.get('language', 'en')

        critical_events = [e for e in events if e['severity'] == 'critical']
        warning_events = [e for e in events if e['severity'] == 'warning']

        # Build SMS
        if language == 'sw':
            sms = f"🚨 Smart Shamba\nHabari {name}!\n"
            for e in (critical_events + warning_events)[:3]:
                emoji = '⛔' if e['severity'] == 'critical' else '⚠️'
                sms += f"{emoji} {e.get('message_sw') or e.get('message_en', '')}\n"
            sms += "— Smart Shamba"
        else:
            sms = f"🚨 Smart Shamba\nHello {name}!\n"
            for e in (critical_events + warning_events)[:3]:
                emoji = '⛔' if e['severity'] == 'critical' else '⚠️'
                sms += f"{emoji} {e.get('message_en', '')}\n"
            sms += "— Smart Shamba"

        # Build web detail
        web = f"# 🚨 Extreme Event Alert for {name}\n\n"
        web += f"**{len(critical_events)} critical** and **{len(warning_events)} warning** events detected.\n\n"
        for e in events:
            emoji = '⛔' if e['severity'] == 'critical' else '⚠️' if e['severity'] == 'warning' else 'ℹ️'
            web += f"### {emoji} {e['event_type'].replace('_', ' ').title()}\n"
            web += f"{e.get('message_en', '')}\n"
            web += f"*Source: {e.get('source', 'unknown')}*\n\n"

        # Send SMS
        sms_sent = False
        if self.sms_service and phone:
            try:
                result = self.sms_service.send_sms(phone, sms)
                sms_sent = result.get('success', False)
            except Exception as e:
                logger.error(f"Extreme event SMS failed: {e}")

        # Log to PG
        if self.db:
            try:
                self.db.log_alert(
                    str(farmer_data.get('id', '')),
                    {
                        'alert_type': 'extreme_event',
                        'severity': 'critical' if critical_events else 'warning',
                        'message': sms,
                        'farmer_phone': phone,
                        'sent_sms': sms_sent,
                        'metadata': _json.dumps({
                            'events': [
                                {'type': e['event_type'], 'severity': e['severity'],
                                 'source': e.get('source')}
                                for e in events
                            ]
                        }),
                    }
                )
            except Exception as e:
                logger.error(f"Failed to log extreme event alert: {e}")

        return {
            'success': True,
            'sms_text': sms,
            'web_text': web,
            'sms_sent': sms_sent,
            'events_count': len(events),
            'critical_count': len(critical_events),
            'warning_count': len(warning_events),
        }

    # ------------------------------------------------------------------ #
    #  Scheduled Smart Alert Scan — auto-triggers for all farmers
    # ------------------------------------------------------------------ #

    async def run_scheduled_smart_alerts(self) -> Dict:
        """
        Periodic scan for ALL registered farmers:
          1. Fetch weather forecast for each farmer's location.
          2. Pull latest IoT sensor readings from their farms.
          3. Pull satellite data for their county.
          4. Run detect_extreme_events() to find critical conditions.
          5. Auto-send alerts for any extreme events found.
          6. Also run generate_condition_alert() for general farm health.

        Returns summary of alerts sent.
        """
        if not self.db:
            return {'error': 'No database service'}

        logger.info("🔔 Starting scheduled smart alert scan for all farmers...")

        farmers = self.db.get_all_farmers(skip=0, limit=500)
        if not farmers:
            logger.info("No farmers registered — skipping alert scan")
            return {'farmers_scanned': 0, 'alerts_sent': 0}

        total_extreme = 0
        total_condition = 0
        errors = 0

        for farmer in farmers:
            try:
                # 1. Detect extreme events (weather + IoT + satellite)
                events = await self.detect_extreme_events(farmer)

                if events:
                    result = await self.generate_extreme_event_alert(farmer, events)
                    if result.get('sms_sent'):
                        total_extreme += 1
                    logger.info(
                        f"  🚨 {farmer.get('name', 'Unknown')}: "
                        f"{result.get('events_count', 0)} extreme events "
                        f"(SMS {'sent' if result.get('sms_sent') else 'queued'})"
                    )

                # 2. Run general condition alert (non-extreme farm health check)
                # Only if no critical extreme events (avoid alert fatigue)
                critical_events = [e for e in events if e.get('severity') == 'critical']
                if not critical_events:
                    try:
                        cond_result = self.generate_condition_alert(farmer)
                        if cond_result.get('sms_sent'):
                            total_condition += 1
                    except Exception as e:
                        logger.debug(f"Condition alert failed for {farmer.get('name')}: {e}")

            except Exception as e:
                errors += 1
                logger.error(
                    f"Alert scan failed for farmer {farmer.get('name', 'unknown')}: {e}"
                )

        summary = {
            'farmers_scanned': len(farmers),
            'extreme_alerts_sent': total_extreme,
            'condition_alerts_sent': total_condition,
            'errors': errors,
            'timestamp': datetime.now().isoformat(),
        }
        logger.info(
            f"✅ Alert scan complete: {len(farmers)} farmers, "
            f"{total_extreme} extreme alerts, {total_condition} condition alerts, "
            f"{errors} errors"
        )
        return summary

    @staticmethod
    def _extract_section(text: str, section_name: str) -> str:
        """Extract content between [SECTION_NAME] and the next [SECTION] or end."""
        import re
        pattern = rf"\[{section_name}\]\s*(.*?)(?=\n\[|$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
if __name__ == "__main__":
    print("🌾 Smart Alert Service Test")
    print("=" * 70)
    
    service = SmartAlertService()
    
    # Simulate bloom data from processor
    bloom_data = {
        'ndvi_mean': 0.65,
        'health_score': 75.0,
        'data_source': 'Sentinel-2',
        'bloom_months': [3, 4, 10, 11],
        'bloom_scores': [0.0, 0.0, 0.0, 0.8, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.7, 0.6]
    }
    
    # Test farmer
    farmer_data = {
        'name': 'John Kamau',
        'phone': '+254712345678',
        'region': 'central',
        'crops': ['maize', 'beans'],
        'language': 'en'
    }
    
    print("\n📱 Generating English Alert...")
    print("-" * 70)
    result = service.send_welcome_alert(farmer_data, bloom_data)
    for detail in result['details']:
        print(f"\n🌾 Crop: {detail['crop'].upper()}")
        print(f"Risk: {detail['bloom_risk']}")
        print("\nSMS Preview:")
        print(detail['sms_text'])
    
    # Test Swahili
    farmer_data_sw = farmer_data.copy()
    farmer_data_sw['language'] = 'sw'
    farmer_data_sw['name'] = 'Mary Wanjiku'
    farmer_data_sw['crops'] = ['coffee']
    
    print("\n\n📱 Generating Swahili Alert...")
    print("-" * 70)
    result_sw = service.send_welcome_alert(farmer_data_sw, bloom_data)
    for detail in result_sw['details']:
        print(f"\n🌾 Crop: {detail['crop'].upper()}")
        print(f"Risk: {detail['bloom_risk']}")
        print("\nSMS Preview:")
        print(detail['sms_text'])
    
    print("\n" + "=" * 70)
    print("✅ Smart Alert Service test complete!")

