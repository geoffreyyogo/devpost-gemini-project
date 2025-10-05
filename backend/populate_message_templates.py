"""
Populate MongoDB with SMS Message Templates for BloomWatch Kenya
These templates can be customized and used for various alert types
"""

from mongodb_service import MongoDBService
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MESSAGE_TEMPLATES = [
    # Welcome messages
    {
        'template_id': 'welcome_en',
        'name': 'Welcome Message - English',
        'language': 'en',
        'category': 'welcome',
        'template': "🌾 Welcome to BloomWatch Kenya! Hello {farmer_name}, thank you for registering. You'll receive satellite-based crop alerts for {crops} in {region}. — BloomWatch Kenya",
        'variables': ['farmer_name', 'crops', 'region'],
        'active': True
    },
    {
        'template_id': 'welcome_sw',
        'name': 'Welcome Message - Swahili',
        'language': 'sw',
        'category': 'welcome',
        'template': "🌾 Karibu BloomWatch Kenya! Habari {farmer_name}, asante kwa kujisajili. Utapokea taarifa za mazao kutoka kwa satelaiti kwa {crops} katika {region}. — BloomWatch Kenya",
        'variables': ['farmer_name', 'crops', 'region'],
        'active': True
    },
    
    # Bloom alerts - High Risk
    {
        'template_id': 'bloom_high_en',
        'name': 'High Bloom Risk - English',
        'language': 'en',
        'category': 'bloom_alert',
        'risk_level': 'high',
        'template': "🔴 URGENT: BloomWatch Kenya Alert\n{farmer_name}, HIGH bloom activity detected near your {crop} farm (NDVI: {ndvi}).\n👉 {advice}\nData: {data_source}\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'crop', 'ndvi', 'advice', 'data_source'],
        'active': True
    },
    {
        'template_id': 'bloom_high_sw',
        'name': 'High Bloom Risk - Swahili',
        'language': 'sw',
        'category': 'bloom_alert',
        'risk_level': 'high',
        'template': "🔴 HARAKA: Taarifa ya BloomWatch Kenya\n{farmer_name}, shughuli KUBWA ya kuchanua imegunduliwa karibu na shamba lako la {crop} (NDVI: {ndvi}).\n💡 {advice}\nData: {data_source}\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'crop', 'ndvi', 'advice', 'data_source'],
        'active': True
    },
    
    # Bloom alerts - Moderate Risk
    {
        'template_id': 'bloom_moderate_en',
        'name': 'Moderate Bloom Risk - English',
        'language': 'en',
        'category': 'bloom_alert',
        'risk_level': 'moderate',
        'template': "🟡 BloomWatch Kenya Alert\n{farmer_name}, moderate bloom activity for {crop} in {region}. Health: {health_score}/100.\n👉 {advice}\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'crop', 'region', 'health_score', 'advice'],
        'active': True
    },
    {
        'template_id': 'bloom_moderate_sw',
        'name': 'Moderate Bloom Risk - Swahili',
        'language': 'sw',
        'category': 'bloom_alert',
        'risk_level': 'moderate',
        'template': "🟡 Taarifa ya BloomWatch Kenya\n{farmer_name}, shughuli ya wastani ya kuchanua kwa {crop} katika {region}. Afya: {health_score}/100.\n💡 {advice}\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'crop', 'region', 'health_score', 'advice'],
        'active': True
    },
    
    # Regional specific templates
    {
        'template_id': 'central_maize_en',
        'name': 'Central Highlands - Maize',
        'language': 'en',
        'region': 'central',
        'crop': 'maize',
        'category': 'regional_alert',
        'template': "🌾 Central Highlands Alert\n{farmer_name}, satellite data shows {health_score}/100 health for maize. {advice} Frost expected this week - protect young plants.\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'health_score', 'advice'],
        'active': True
    },
    {
        'template_id': 'nyanza_rice_en',
        'name': 'Lake Victoria - Rice',
        'language': 'en',
        'region': 'nyanza',
        'crop': 'rice',
        'category': 'regional_alert',
        'template': "🌾 Lake Victoria Basin Alert\n{farmer_name}, rice health: {health_score}/100. {advice} Monitor water levels in paddies.\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'health_score', 'advice'],
        'active': True
    },
    {
        'template_id': 'rift_wheat_en',
        'name': 'Rift Valley - Wheat',
        'language': 'en',
        'region': 'rift_valley',
        'crop': 'wheat',
        'category': 'regional_alert',
        'template': "🌾 Rift Valley Alert\n{farmer_name}, wheat status: {health_score}/100. {advice} Watch for rust disease in current weather.\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'health_score', 'advice'],
        'active': True
    },
    
    # Weekly summaries
    {
        'template_id': 'weekly_summary_en',
        'name': 'Weekly Summary - English',
        'language': 'en',
        'category': 'summary',
        'template': "📊 BloomWatch Weekly Report\nHello {farmer_name},\nCrop health: {health_score}/100\nBlooms detected: {bloom_count}\nAdvice: {weekly_advice}\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'health_score', 'bloom_count', 'weekly_advice'],
        'active': True
    },
    {
        'template_id': 'weekly_summary_sw',
        'name': 'Weekly Summary - Swahili',
        'language': 'sw',
        'category': 'summary',
        'template': "📊 Ripoti ya Wiki ya BloomWatch\nHabari {farmer_name},\nAfya ya mazao: {health_score}/100\nKuchanua kuligunduliwa: {bloom_count}\nUshauri: {weekly_advice}\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'health_score', 'bloom_count', 'weekly_advice'],
        'active': True
    },
    
    # Seasonal advisories
    {
        'template_id': 'long_rains_en',
        'name': 'Long Rains Advisory - English',
        'language': 'en',
        'category': 'seasonal',
        'season': 'long_rains',
        'template': "🌧️ Long Rains Season Alert\n{farmer_name}, prepare for planting season. {crop} recommended actions: {seasonal_advice}\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'crop', 'seasonal_advice'],
        'active': True
    },
    {
        'template_id': 'short_rains_en',
        'name': 'Short Rains Advisory - English',
        'language': 'en',
        'category': 'seasonal',
        'season': 'short_rains',
        'template': "🌧️ Short Rains Season Alert\n{farmer_name}, second planting season. {crop} status: {health_score}/100. {seasonal_advice}\n— BloomWatch Kenya",
        'variables': ['farmer_name', 'crop', 'health_score', 'seasonal_advice'],
        'active': True
    },
    
    # Emergency alerts
    {
        'template_id': 'drought_alert_en',
        'name': 'Drought Alert - English',
        'language': 'en',
        'category': 'emergency',
        'template': "⚠️ DROUGHT ALERT - {region}\n{farmer_name}, severe water stress detected (NDVI: {ndvi}). Immediate action: {emergency_advice}\nContact: +254-700-BLOOM\n— BloomWatch Kenya",
        'variables': ['region', 'farmer_name', 'ndvi', 'emergency_advice'],
        'active': True
    },
    {
        'template_id': 'flood_alert_en',
        'name': 'Flood Alert - English',
        'language': 'en',
        'category': 'emergency',
        'template': "⚠️ FLOOD RISK - {region}\n{farmer_name}, excessive water detected. Protect {crop} crops. {emergency_advice}\nContact: +254-700-BLOOM\n— BloomWatch Kenya",
        'variables': ['region', 'farmer_name', 'crop', 'emergency_advice'],
        'active': True
    }
]


def populate_templates(mongo_service: MongoDBService):
    """Populate MongoDB with message templates"""
    
    if not mongo_service.is_connected():
        logger.error("MongoDB not connected. Cannot populate templates.")
        return False
    
    collection = mongo_service.message_templates
    
    logger.info("Populating message templates...")
    
    inserted = 0
    updated = 0
    
    for template in MESSAGE_TEMPLATES:
        template['created_at'] = datetime.now()
        template['updated_at'] = datetime.now()
        
        # Check if template exists
        existing = collection.find_one({'template_id': template['template_id']})
        
        if existing:
            # Update existing template
            collection.update_one(
                {'template_id': template['template_id']},
                {'$set': template}
            )
            updated += 1
            logger.info(f"  ✓ Updated: {template['name']}")
        else:
            # Insert new template
            collection.insert_one(template)
            inserted += 1
            logger.info(f"  ✓ Inserted: {template['name']}")
    
    logger.info(f"\n📊 Summary:")
    logger.info(f"  Inserted: {inserted}")
    logger.info(f"  Updated: {updated}")
    logger.info(f"  Total: {len(MESSAGE_TEMPLATES)}")
    
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("📝 Populating Message Templates for BloomWatch Kenya")
    print("=" * 70)
    
    mongo = MongoDBService()
    
    if mongo.is_connected():
        print(f"\n✓ Connected to MongoDB: {mongo.db.name}")
        success = populate_templates(mongo)
        
        if success:
            print("\n" + "=" * 70)
            print("✅ Message templates populated successfully!")
            print("=" * 70)
            
            # Show sample templates
            print("\n📋 Sample Templates:")
            print("-" * 70)
            
            samples = mongo.message_templates.find({'category': 'welcome'}).limit(2)
            for template in samples:
                print(f"\n{template['name']}:")
                print(f"  {template['template']}")
    else:
        print("❌ Could not connect to MongoDB")
        print("   Check your MONGODB_URI in .env file")

