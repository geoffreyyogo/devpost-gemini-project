"""
Smart Alert Service for BloomWatch Kenya
Uses actual Earth observation data to generate meaningful, actionable SMS alerts
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    into actionable farmer insights
    """
    
    def __init__(self, mongo_service=None, africastalking_service=None):
        """Initialize with optional services"""
        self.mongo = mongo_service
        self.at_service = africastalking_service
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
            header = f"🌾 BloomWatch Kenya – {region_name}"
            greeting = f"Habari {alert.farmer_name},"
            
            data_line = f"Data za satelaiti ({alert.data_source}) zinaonyesha afya ya mazao: {alert.health_score:.0f}/100"
            
            bloom_line = f"{risk_emoji} Hatari ya kuchanua: {alert.bloom_risk} ({alert.bloom_confidence*100:.0f}%)"
            
            advice_line = f"💡 Ushauri: {alert.advice}"
            
            footer = "— BloomWatch Kenya"
            
            sms = f"{header}\n{greeting} {data_line}.\n{bloom_line}\n{advice_line}\n{footer}"
            
        else:
            # English template
            header = f"🌾 BloomWatch Kenya – {region_name}"
            greeting = f"Hello {alert.farmer_name},"
            
            data_line = f"Satellite data ({alert.data_source}) shows crop health: {alert.health_score:.0f}/100"
            
            bloom_line = f"{risk_emoji} Bloom activity: {alert.bloom_risk} ({alert.bloom_confidence*100:.0f}% confidence)"
            
            advice_line = f"👉 Advice: {alert.advice}"
            
            footer = "— Powered by BloomWatch Kenya"
            
            sms = f"{header}\n{greeting} {data_line}.\n{bloom_line}\n{advice_line}\n{footer}"
        
        return sms
    
    def send_welcome_alert(self, farmer_data: Dict, bloom_data: Dict) -> Dict:
        """
        Send welcome alert with current bloom status when farmer signs up
        Uses actual EO data
        """
        # Extract farmer info
        name = farmer_data.get('name', 'Farmer')
        phone = farmer_data.get('phone')
        region = farmer_data.get('region', 'central')
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
            if self.at_service:
                try:
                    result = self.at_service.send_sms(phone, sms_text)
                    sms_sent = True
                    logger.info(f"SMS sent to {phone} for {crop}")
                except Exception as e:
                    logger.error(f"Failed to send SMS: {e}")
            
            # Store in MongoDB if available
            if self.mongo:
                try:
                    self.mongo.get_alerts_collection().insert_one({
                        'farmer_phone': phone,
                        'crop': crop,
                        'message': sms_text,
                        'bloom_risk': bloom_risk,
                        'health_score': health_score,
                        'ndvi': ndvi_mean,
                        'data_source': data_source,
                        'timestamp': datetime.now(),
                        'sent_sms': sms_sent,
                        'alert_type': 'welcome'
                    })
                except Exception as e:
                    logger.error(f"Failed to store alert in MongoDB: {e}")
            
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
            'details': results
        }


# Testing
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

