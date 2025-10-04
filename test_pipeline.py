#!/usr/bin/env python3
"""
Complete Pipeline Test for BloomWatch Kenya
Tests: MongoDB → GEE Data → Bloom Detection → Notifications
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 70)
print("🌸 BloomWatch Kenya - Complete Pipeline Test")
print("=" * 70)

# Test 1: MongoDB Connection
print("\n1️⃣ Testing MongoDB Connection...")
print("-" * 70)

try:
    from backend.mongodb_service import MongoDBService
    
    mongo = MongoDBService()
    
    if mongo.is_connected():
        print("✅ MongoDB: CONNECTED")
        
        # Try to get collections
        farmers = mongo.get_farmers_collection()
        sessions = mongo.get_sessions_collection()
        alerts = mongo.get_alerts_collection()
        
        # Count documents
        farmer_count = farmers.count_documents({})
        session_count = sessions.count_documents({})
        alert_count = alerts.count_documents({})
        
        print(f"   📊 Farmers: {farmer_count}")
        print(f"   🔐 Sessions: {session_count}")
        print(f"   🔔 Alerts: {alert_count}")
        
        # Get database info
        db = mongo.get_db()
        print(f"   🗄️  Database: {db.name}")
        print(f"   📁 Collections: {db.list_collection_names()}")
        
    else:
        print("⚠️  MongoDB: NOT CONNECTED (using demo mode)")
        print("   This is OK for development/testing")
        
except Exception as e:
    print(f"❌ MongoDB Error: {e}")
    print("   Check .env file for MONGODB_URI")

# Test 2: GEE Data Loader
print("\n2️⃣ Testing GEE Data Loader...")
print("-" * 70)

try:
    from backend.gee_data_loader import GEEDataLoader
    
    loader = GEEDataLoader()
    info = loader.get_data_info()
    
    print(f"✅ Data Loader: READY")
    print(f"   📁 Export Dir: {info['export_directory']}")
    print(f"   📊 Total Files: {info['total_files']}")
    print(f"   🛰️  Sentinel-2: {'✓' if info['has_sentinel2'] else '✗'}")
    print(f"   🛰️  Landsat: {'✓' if info['has_landsat'] else '✗'}")
    print(f"   🛰️  MODIS: {'✓' if info['has_modis'] else '✗'}")
    print(f"   🌸 ARI Data: {'✓' if info['has_ari'] else '✗'}")
    
    # Try loading data
    kenya_data = loader.load_kenya_data()
    print(f"\n   📡 Data Source: {kenya_data.get('source')}")
    print(f"   📏 NDVI Shape: {kenya_data['ndvi'].shape}")
    print(f"   📈 NDVI Range: {kenya_data['ndvi'].min():.3f} - {kenya_data['ndvi'].max():.3f}")
    
    if info['total_files'] == 0:
        print("\n   💡 Tip: Export data from GEE to use real satellite data")
        print("      See: GEE_INTEGRATION_GUIDE.md")
    
except Exception as e:
    print(f"❌ Data Loader Error: {e}")

# Test 3: Bloom Detection
print("\n3️⃣ Testing Bloom Detection...")
print("-" * 70)

try:
    from backend.bloom_processor import BloomProcessor
    
    processor = BloomProcessor()
    results = processor.detect_bloom_events('kenya')
    
    print(f"✅ Bloom Processor: WORKING")
    print(f"   📊 Data Source: {results['data_source']}")
    print(f"   🌱 Health Score: {results.get('health_score', 0):.1f}/100")
    print(f"   🌸 Bloom Events: {len(results['bloom_months'])}")
    
    if results['bloom_dates']:
        print(f"\n   📅 Predicted Blooms:")
        for i, date in enumerate(results['bloom_dates'][:3]):  # Show first 3
            month_idx = results['bloom_months'][i]
            score = results['bloom_scores'][month_idx]
            print(f"      • {date} ({score:.0%} confidence)")
    
except Exception as e:
    print(f"❌ Bloom Processor Error: {e}")

# Test 4: Notification Services
print("\n4️⃣ Testing Notification Services...")
print("-" * 70)

try:
    from backend.africastalking_service import AfricasTalkingService
    
    at_service = AfricasTalkingService()
    print(f"✅ Africa's Talking: INITIALIZED")
    print(f"   📱 Username: {at_service.username}")
    print(f"   ⚠️  Note: SMS sending requires live credentials")
    
except Exception as e:
    print(f"⚠️  Africa's Talking: {e}")
    print("   Set AT_USERNAME and AT_API_KEY in .env for SMS")

try:
    from backend.notification_service import NotificationService
    
    notif = NotificationService()
    print(f"✅ Notification Service: READY")
    
except Exception as e:
    print(f"⚠️  Notification Service: {e}")

# Test 5: Authentication Service
print("\n5️⃣ Testing Authentication Service...")
print("-" * 70)

try:
    from backend.auth_service import AuthService
    
    if mongo.is_connected():
        auth = AuthService(mongo)
        print(f"✅ Auth Service: READY")
        print(f"   🔐 Using MongoDB for sessions")
    else:
        print(f"⚠️  Auth Service: Demo mode (no MongoDB)")
    
except Exception as e:
    print(f"❌ Auth Service Error: {e}")

# Test 6: Environment Configuration
print("\n6️⃣ Checking Environment Configuration...")
print("-" * 70)

from dotenv import load_dotenv
load_dotenv()

required_vars = {
    'MONGODB_URI': 'MongoDB connection',
    'AT_USERNAME': 'Africa\'s Talking username',
    'AT_API_KEY': 'Africa\'s Talking API key'
}

optional_vars = {
    'TWILIO_ACCOUNT_SID': 'Twilio (optional)',
    'SENDGRID_API_KEY': 'SendGrid (optional)'
}

print("Required variables:")
for var, desc in required_vars.items():
    value = os.getenv(var)
    if value:
        # Mask sensitive data
        if 'KEY' in var or 'URI' in var:
            display = value[:8] + '...' if len(value) > 8 else '***'
        else:
            display = value
        print(f"   ✓ {var}: {display}")
    else:
        print(f"   ✗ {var}: Not set ({desc})")

print("\nOptional variables:")
for var, desc in optional_vars.items():
    value = os.getenv(var)
    status = "✓ Set" if value else "○ Not set"
    print(f"   {status} {var} ({desc})")

# Summary
print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)

components_status = {
    'MongoDB': mongo.is_connected() if 'mongo' in locals() else False,
    'GEE Data Loader': 'loader' in locals(),
    'Bloom Processor': 'processor' in locals(),
    'Notifications': 'notif' in locals() or 'at_service' in locals(),
    'Authentication': 'auth' in locals()
}

working = sum(components_status.values())
total = len(components_status)

for component, status in components_status.items():
    icon = "✅" if status else "⚠️"
    print(f"{icon} {component}")

print(f"\n🎯 System Status: {working}/{total} components ready")

if working == total:
    print("🎉 All systems GO! Ready for production.")
elif working >= 3:
    print("✨ Core systems working! App can run in demo mode.")
else:
    print("⚠️  Some components need configuration.")
    print("   See .env.example and setup guides for details.")

print("\n💡 Next Steps:")
if not components_status.get('MongoDB'):
    print("   • Set up MongoDB (local or Atlas)")
    print("   • Update MONGODB_URI in .env")
if info.get('total_files', 0) == 0:
    print("   • Export data from GEE (see GEE_INTEGRATION_GUIDE.md)")
    print("   • Or use synthetic data for demo")
if not os.getenv('AT_API_KEY'):
    print("   • Get Africa's Talking credentials for SMS")
    print("   • See AFRICA_TALKING_SETUP.md")

print("\n🚀 Run the app: ./RUN_APP.sh")
print("=" * 70)

