"""
MongoDB Database Seed Script for BloomWatch Kenya
Populates database with crops, regions, templates, and sample data
"""

import sys
import os
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(__file__))
from mongodb_service import MongoDBService
from kenya_crops import KENYA_REGIONS, KenyaCropCalendar

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# REFERENCE DATA
# ============================================================================

CROPS_DATA = {
    'maize': {
        'name': 'Maize',
        'name_sw': 'Mahindi',
        'scientific_name': 'Zea mays',
        'category': 'cereal',
        'seasons': {
            'long_rains': {'plant': [3, 4], 'bloom': [6, 7], 'harvest': [8, 9]},
            'short_rains': {'plant': [10, 11], 'bloom': [1, 2], 'harvest': [3, 4]}
        },
        'varieties': ['H614', 'H629', 'DK8031', 'Local varieties'],
        'bloom_duration_days': 14,
        'critical_stages': ['tasseling', 'silking', 'grain_filling'],
        'optimal_temp_c': [18, 30],
        'rainfall_mm': [500, 800],
        'regions': ['central', 'rift_valley', 'eastern', 'western'],
        'icon': '🌽'
    },
    'beans': {
        'name': 'Beans',
        'name_sw': 'Maharagwe',
        'scientific_name': 'Phaseolus vulgaris',
        'category': 'legume',
        'seasons': {
            'long_rains': {'plant': [3, 4], 'bloom': [5, 6], 'harvest': [7, 8]},
            'short_rains': {'plant': [10, 11], 'bloom': [12, 1], 'harvest': [2, 3]}
        },
        'varieties': ['Rose coco', 'Canadian wonder', 'Mwitemania', 'GLP-2'],
        'bloom_duration_days': 10,
        'critical_stages': ['flowering', 'pod_formation', 'pod_filling'],
        'optimal_temp_c': [15, 25],
        'rainfall_mm': [400, 600],
        'regions': ['central', 'eastern', 'western'],
        'icon': '🫘'
    },
    'coffee': {
        'name': 'Coffee',
        'name_sw': 'Kahawa',
        'scientific_name': 'Coffea arabica',
        'category': 'cash_crop',
        'seasons': {
            'main_bloom': {'plant': 'perennial', 'bloom': [3, 5], 'harvest': [10, 12]},
            'fly_bloom': {'plant': 'perennial', 'bloom': [9, 11], 'harvest': [5, 7]}
        },
        'varieties': ['SL28', 'SL34', 'K7', 'Ruiru 11', 'Batian'],
        'bloom_duration_days': 21,
        'critical_stages': ['flowering', 'pin_head', 'cherry_development'],
        'optimal_temp_c': [15, 24],
        'rainfall_mm': [1000, 1800],
        'regions': ['central', 'eastern', 'nyanza'],
        'icon': '☕'
    },
    'tea': {
        'name': 'Tea',
        'name_sw': 'Chai',
        'scientific_name': 'Camellia sinensis',
        'category': 'cash_crop',
        'seasons': {
            'continuous': {'plant': 'perennial', 'bloom': [1, 12], 'harvest': [1, 12]}
        },
        'varieties': ['TRFK 6/8', 'TRFK 31/8', 'Purple tea'],
        'bloom_duration_days': 365,
        'critical_stages': ['flush_growth', 'leaf_maturity'],
        'optimal_temp_c': [13, 25],
        'rainfall_mm': [1200, 2000],
        'regions': ['central', 'rift_valley', 'western'],
        'icon': '🍵'
    },
    'wheat': {
        'name': 'Wheat',
        'name_sw': 'Ngano',
        'scientific_name': 'Triticum aestivum',
        'category': 'cereal',
        'seasons': {
            'long_rains': {'plant': [6, 7], 'bloom': [9, 10], 'harvest': [11, 12]},
            'short_rains': {'plant': [1, 2], 'bloom': [4, 5], 'harvest': [6, 7]}
        },
        'varieties': ['Kenya Kudu', 'Kenya Tai', 'Njoro BW II'],
        'bloom_duration_days': 7,
        'critical_stages': ['heading', 'flowering', 'grain_filling'],
        'optimal_temp_c': [15, 25],
        'rainfall_mm': [450, 650],
        'regions': ['rift_valley', 'central'],
        'icon': '🌾'
    },
    'sorghum': {
        'name': 'Sorghum',
        'name_sw': 'Mtama',
        'scientific_name': 'Sorghum bicolor',
        'category': 'cereal',
        'seasons': {
            'long_rains': {'plant': [3, 4], 'bloom': [6, 7], 'harvest': [8, 9]},
            'short_rains': {'plant': [10, 11], 'bloom': [1, 2], 'harvest': [3, 4]}
        },
        'varieties': ['Gadam', 'Serena', 'Kari Mtama 1'],
        'bloom_duration_days': 10,
        'critical_stages': ['panicle_emergence', 'flowering', 'grain_filling'],
        'optimal_temp_c': [21, 35],
        'rainfall_mm': [400, 600],
        'regions': ['eastern', 'coast', 'northern'],
        'icon': '🌾'
    }
}

# ============================================================================
# MESSAGE TEMPLATES
# ============================================================================

MESSAGE_TEMPLATES = {
    'welcome_sms': {
        'type': 'sms',
        'category': 'registration',
        'en': 'Welcome to BloomWatch Kenya, {name}! We will send you bloom alerts for {crops} in {region}. Reply STOP to unsubscribe.',
        'sw': 'Karibu BloomWatch Kenya, {name}! Tutakutumia arifa za kuchanua kwa {crops} katika {region}. Jibu STOP kuacha.'
    },
    'welcome_email': {
        'type': 'email',
        'category': 'registration',
        'subject_en': 'Welcome to BloomWatch Kenya!',
        'subject_sw': 'Karibu BloomWatch Kenya!',
        'body_en': '''Dear {name},

Welcome to BloomWatch Kenya! 🌾

Your account has been successfully created. We will monitor bloom events for your crops ({crops}) in the {region} region using NASA satellite data.

What to expect:
• Real-time bloom alerts via SMS and email
• Crop calendar and seasonal advice
• Weather updates and farming tips
• Personalized recommendations

You can manage your preferences anytime through our web dashboard.

Best regards,
BloomWatch Kenya Team
Powered by NASA Earth Observation Data''',
        'body_sw': '''Mpendwa {name},

Karibu BloomWatch Kenya! 🌾

Akaunti yako imeundwa kikamilifu. Tutafuatilia matukio ya kuchanua kwa mazao yako ({crops}) katika mkoa wa {region} kwa kutumia data za satelaiti za NASA.

Tarajia:
• Arifa za wakati halisi za kuchanua kupitia SMS na barua pepe
• Kalenda ya mazao na ushauri wa misimu
• Sasisho za hali ya hewa na vidokezo vya kilimo
• Mapendekezo maalum

Unaweza kudhibiti mapendeleo yako wakati wowote kupitia dashibodi yetu ya wavuti.

Heshima,
Timu ya BloomWatch Kenya
Inayotumia Data za Uchunguzi wa Dunia za NASA'''
    },
    'bloom_start_sms': {
        'type': 'sms',
        'category': 'alert',
        'en': '🌸 BloomWatch Alert: {crop} blooming detected near your farm! Intensity: {intensity}. Check crops for optimal harvest timing.',
        'sw': '🌸 Onyo la BloomWatch: {crop} inaanza kuchanua karibu na shamba lako! Nguvu: {intensity}. Angalia mazao yako kwa wakati mzuri wa kuvuna.'
    },
    'bloom_peak_sms': {
        'type': 'sms',
        'category': 'alert',
        'en': '🌺 Peak Bloom: {crop} at peak bloom! Perfect time for pollination. Intensity: {intensity}',
        'sw': '🌺 Kilele cha Kuchanua: {crop} iko kwenye kilele! Wakati mzuri wa uchavushaji. Nguvu: {intensity}'
    },
    'bloom_end_sms': {
        'type': 'sms',
        'category': 'alert',
        'en': '🍃 Bloom Ending: {crop} bloom cycle ending. Consider post-bloom care and disease prevention.',
        'sw': '🍃 Kuchanua Kunaisha: Mzunguko wa kuchanua kwa {crop} unaisha. Fikiria utunzaji na kuzuia magonjwa.'
    },
    'bloom_alert_email': {
        'type': 'email',
        'category': 'alert',
        'subject_en': 'BloomWatch Alert - {crop} {alert_type}',
        'subject_sw': 'Onyo la BloomWatch - {crop} {alert_type}',
        'body_en': '''Dear {name},

{alert_message}

Bloom Details:
• Crop: {crop}
• Location: {location_lat}, {location_lon}
• Intensity: {intensity}
• Detected: {timestamp}
• Distance from your farm: ~{distance_km} km

Recommended Actions:
{recommendations}

For real-time monitoring, visit our dashboard: https://bloomwatch.ke

Best regards,
BloomWatch Kenya Team''',
        'body_sw': '''Mpendwa {name},

{alert_message}

Maelezo ya Kuchanua:
• Mazao: {crop}
• Mahali: {location_lat}, {location_lon}
• Nguvu: {intensity}
• Ilionekana: {timestamp}
• Umbali kutoka shamba lako: ~{distance_km} km

Hatua Zinazopendekeza:
{recommendations}

Kwa ufuatiliaji wa wakati halisi, tembelea dashibodi yetu: https://bloomwatch.ke

Heshima,
Timu ya BloomWatch Kenya'''
    },
    'seasonal_advice_email': {
        'type': 'email',
        'category': 'advice',
        'subject_en': 'Seasonal Farming Advice - {season}',
        'subject_sw': 'Ushauri wa Kilimo wa Msimu - {season}',
        'body_en': '''Dear {name},

Seasonal Update for {region} Region - {season}

{advice_content}

Your Crops: {crops}

Expected Activities This Month:
{activities}

Weather Forecast:
{weather_summary}

Stay tuned for more updates!

BloomWatch Kenya Team''',
        'body_sw': '''Mpendwa {name},

Sasisho la Msimu kwa Mkoa wa {region} - {season}

{advice_content}

Mazao Yako: {crops}

Shughuli Zinazotarajiwa Mwezi Huu:
{activities}

Utabiri wa Hali ya Hewa:
{weather_summary}

Endelea kusubiri sasisho zaidi!

Timu ya BloomWatch Kenya'''
    }
}

# ============================================================================
# AGRICULTURAL ADVICE
# ============================================================================

AGRICULTURAL_ADVICE = {
    'maize': {
        'tasseling': {
            'en': 'Monitor for adequate moisture. This is critical for pollen production.',
            'sw': 'Angalia kama kuna maji ya kutosha. Hii ni muhimu kwa uzalishaji wa chavua.'
        },
        'silking': {
            'en': 'Ensure good pollination. Watch for pest attacks on silks.',
            'sw': 'Hakikisha uchavushaji mzuri. Chunga wadudu kwenye nyuzi za mahindi.'
        },
        'grain_filling': {
            'en': 'Maintain soil moisture. Consider disease prevention measures.',
            'sw': 'Dumisha unyevu wa udongo. Fikiria njia za kuzuia magonjwa.'
        }
    },
    'beans': {
        'flowering': {
            'en': 'Avoid overhead irrigation to prevent flower drop. Monitor for aphids.',
            'sw': 'Epuka kumwagilia juu ili kuzuia maua kuanguka. Chunga wadudu wadogo.'
        },
        'pod_formation': {
            'en': 'Ensure adequate phosphorus. Watch for pod borers.',
            'sw': 'Hakikisha phosphorus ya kutosha. Chunga wadudu wa miharagwe.'
        },
        'pod_filling': {
            'en': 'Maintain consistent moisture. Prepare for harvest in 2-3 weeks.',
            'sw': 'Dumisha unyevu sawa. Andaa kwa mavuno katika wiki 2-3.'
        }
    },
    'coffee': {
        'flowering': {
            'en': 'Maintain consistent moisture. Avoid disturbance during bloom.',
            'sw': 'Dumisha unyevu sawa. Epuka kusumbua wakati wa kuchanua.'
        },
        'pin_head': {
            'en': 'Critical stage for fruit set. Monitor for coffee berry disease.',
            'sw': 'Hatua muhimu ya kuanza matunda. Chunga ugonjwa wa coffee berry.'
        },
        'cherry_development': {
            'en': 'Ensure adequate nutrients. Begin pest control measures.',
            'sw': 'Hakikisha virutubishi vya kutosha. Anza hatua za kudhibiti wadudu.'
        }
    }
}

# ============================================================================
# SAMPLE FARMERS FOR TESTING
# ============================================================================

SAMPLE_FARMERS = [
    {
        'name': 'John Kamau',
        'phone': '+254712345678',
        'email': 'john.kamau@example.com',
        'region': 'central',
        'crops': ['maize', 'beans', 'coffee'],
        'language': 'en',
        'location_lat': -1.2921,
        'location_lon': 36.8219,
        'sms_enabled': True,
        'registered_via': 'web'
    },
    {
        'name': 'Mary Wanjiku',
        'phone': '+254723456789',
        'email': 'mary.wanjiku@example.com',
        'region': 'central',
        'crops': ['coffee', 'tea'],
        'language': 'sw',
        'location_lat': -0.9833,
        'location_lon': 37.0833,
        'sms_enabled': True,
        'registered_via': 'ussd'
    },
    {
        'name': 'Peter Odhiambo',
        'phone': '+254734567890',
        'email': 'peter.odhiambo@example.com',
        'region': 'western',
        'crops': ['maize', 'beans', 'sugarcane'],
        'language': 'en',
        'location_lat': 0.2833,
        'location_lon': 34.7519,
        'sms_enabled': True,
        'registered_via': 'web'
    },
    {
        'name': 'Sarah Muthoni',
        'phone': '+254745678901',
        'email': 'sarah.muthoni@example.com',
        'region': 'rift_valley',
        'crops': ['wheat', 'maize', 'tea'],
        'language': 'sw',
        'location_lat': -0.0917,
        'location_lon': 34.7680,
        'sms_enabled': True,
        'registered_via': 'web'
    },
    {
        'name': 'David Mutua',
        'phone': '+254756789012',
        'email': 'david.mutua@example.com',
        'region': 'eastern',
        'crops': ['sorghum', 'beans', 'maize'],
        'language': 'en',
        'location_lat': -1.5177,
        'location_lon': 37.2634,
        'sms_enabled': True,
        'registered_via': 'ussd'
    }
]

# ============================================================================
# SEED FUNCTIONS
# ============================================================================

def seed_crops(db):
    """Seed crops collection with crop data"""
    logger.info("Seeding crops collection...")
    
    crops_collection = db['crops']
    crops_collection.delete_many({})  # Clear existing
    
    for crop_id, crop_data in CROPS_DATA.items():
        crop_doc = {
            'crop_id': crop_id,
            **crop_data,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        crops_collection.insert_one(crop_doc)
    
    crops_collection.create_index('crop_id', unique=True)
    logger.info(f"✓ Seeded {len(CROPS_DATA)} crops")

def seed_regions(db):
    """Seed regions collection with Kenya regions data"""
    logger.info("Seeding regions collection...")
    
    regions_collection = db['regions']
    regions_collection.delete_many({})  # Clear existing
    
    for region_id, region_data in KENYA_REGIONS.items():
        region_doc = {
            'region_id': region_id,
            'name': region_id.replace('_', ' ').title(),
            **region_data,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        regions_collection.insert_one(region_doc)
    
    regions_collection.create_index('region_id', unique=True)
    logger.info(f"✓ Seeded {len(KENYA_REGIONS)} regions")

def seed_templates(db):
    """Seed message templates collection"""
    logger.info("Seeding templates collection...")
    
    templates_collection = db['message_templates']
    templates_collection.delete_many({})  # Clear existing
    
    for template_id, template_data in MESSAGE_TEMPLATES.items():
        template_doc = {
            'template_id': template_id,
            **template_data,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        templates_collection.insert_one(template_doc)
    
    templates_collection.create_index('template_id', unique=True)
    templates_collection.create_index('category')
    templates_collection.create_index('type')
    logger.info(f"✓ Seeded {len(MESSAGE_TEMPLATES)} templates")

def seed_advice(db):
    """Seed agricultural advice collection"""
    logger.info("Seeding agricultural advice collection...")
    
    advice_collection = db['agricultural_advice']
    advice_collection.delete_many({})  # Clear existing
    
    for crop, stages in AGRICULTURAL_ADVICE.items():
        for stage, advice in stages.items():
            advice_doc = {
                'crop': crop,
                'stage': stage,
                'advice_en': advice['en'],
                'advice_sw': advice['sw'],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            advice_collection.insert_one(advice_doc)
    
    advice_collection.create_index([('crop', ASCENDING), ('stage', ASCENDING)])
    logger.info(f"✓ Seeded agricultural advice")

def seed_sample_farmers(mongo_service):
    """Seed sample farmers for testing (with passwords)"""
    logger.info("Seeding sample farmers...")
    
    from auth_service import AuthService
    auth_service = AuthService()
    
    count = 0
    for farmer_data in SAMPLE_FARMERS:
        # Check if farmer already exists
        existing = mongo_service.get_farmer_by_phone(farmer_data['phone'])
        if existing:
            logger.info(f"  Skipping {farmer_data['name']} - already exists")
            continue
        
        # Register farmer with default password
        result = auth_service.register_farmer(farmer_data.copy(), 'password123')
        if result['success']:
            count += 1
            logger.info(f"  ✓ Added {farmer_data['name']}")
        else:
            logger.warning(f"  ✗ Failed to add {farmer_data['name']}: {result.get('message')}")
    
    logger.info(f"✓ Seeded {count} sample farmers")

def seed_system_config(db):
    """Seed system configuration"""
    logger.info("Seeding system configuration...")
    
    config_collection = db['system_config']
    config_collection.delete_many({})  # Clear existing
    
    config = {
        'app_name': 'BloomWatch Kenya',
        'version': '2.0.0',
        'supported_languages': ['en', 'sw'],
        'default_language': 'en',
        'default_alert_radius_km': 10,
        'max_alert_radius_km': 50,
        'bloom_intensity_threshold': 0.5,
        'notification_settings': {
            'sms_enabled': True,
            'email_enabled': True,
            'max_alerts_per_day': 5,
            'quiet_hours': {'start': 21, 'end': 7}
        },
        'contact': {
            'email': 'support@bloomwatch.ke',
            'phone': '+254700000000',
            'website': 'https://bloomwatch.ke'
        },
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    config_collection.insert_one(config)
    logger.info("✓ Seeded system configuration")

# ============================================================================
# MAIN SEED FUNCTION
# ============================================================================

def seed_all():
    """Run all seed functions"""
    logger.info("=" * 60)
    logger.info("BloomWatch Kenya - Database Seeding")
    logger.info("=" * 60)
    
    # Initialize MongoDB service
    mongo_service = MongoDBService()
    
    if not mongo_service.is_connected():
        logger.error("❌ MongoDB connection failed. Please check your connection.")
        return False
    
    db = mongo_service.get_db()
    
    try:
        # Seed reference data
        seed_crops(db)
        seed_regions(db)
        seed_templates(db)
        seed_advice(db)
        seed_system_config(db)
        
        # Seed sample farmers (requires auth service)
        seed_sample_farmers(mongo_service)
        
        logger.info("=" * 60)
        logger.info("✅ Database seeding completed successfully!")
        logger.info("=" * 60)
        logger.info("\nSample Farmer Credentials:")
        logger.info("  Phone: +254712345678")
        logger.info("  Password: password123")
        logger.info("\n  (All sample farmers use password: password123)")
        logger.info("=" * 60)
        
        # Display statistics
        stats = mongo_service.get_farmer_statistics()
        logger.info("\n📊 Database Statistics:")
        logger.info(f"  Total Farmers: {stats.get('total_farmers', 0)}")
        logger.info(f"  Crops: {db['crops'].count_documents({})}")
        logger.info(f"  Regions: {db['regions'].count_documents({})}")
        logger.info(f"  Templates: {db['message_templates'].count_documents({})}")
        
        mongo_service.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        mongo_service.close()
        return False

# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed BloomWatch Kenya database')
    parser.add_argument('--reset', action='store_true', help='Reset and reseed all data')
    
    args = parser.parse_args()
    
    if args.reset:
        logger.warning("⚠️  Resetting database - all existing data will be cleared!")
        response = input("Are you sure? Type 'yes' to continue: ")
        if response.lower() != 'yes':
            logger.info("Seeding cancelled")
            sys.exit(0)
    
    success = seed_all()
    sys.exit(0 if success else 1)

