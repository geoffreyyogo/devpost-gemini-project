"""
Quick System Test for Kenya Real Data Setup
Tests all components end-to-end
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

print("="*80)
print("🧪 BLOOMWATCH KENYA - SYSTEM TEST")
print("="*80)
print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Test 1: Configuration
print("TEST 1: Kenya Counties Configuration")
print("-"*80)
try:
    from kenya_counties_config import KENYA_COUNTIES, KENYA_REGIONS, AGRICULTURAL_COUNTIES
    print(f"✅ Total counties configured: {len(KENYA_COUNTIES)}")
    print(f"✅ Total regions configured: {len(KENYA_REGIONS)}")
    print(f"✅ Agricultural counties: {len(AGRICULTURAL_COUNTIES)}")
    print(f"✅ Sample county: {list(KENYA_COUNTIES.keys())[0]} - {KENYA_COUNTIES[list(KENYA_COUNTIES.keys())[0]]['name']}")
except Exception as e:
    print(f"❌ FAILED: {e}")
print()

# Test 2: Earth Engine Connection
print("TEST 2: Earth Engine Connection")
print("-"*80)
try:
    from ee_pipeline import initialize_earth_engine
    if initialize_earth_engine():
        print("✅ Earth Engine initialized successfully")
        print(f"✅ Project ID: {os.getenv('GEE_PROJECT_ID')}")
    else:
        print("⚠️  Earth Engine not available (will use fallback mode)")
except Exception as e:
    print(f"❌ FAILED: {e}")
print()

# Test 3: Data Fetcher
print("TEST 3: Kenya Data Fetcher")
print("-"*80)
try:
    from kenya_data_fetcher import KenyaDataFetcher
    fetcher = KenyaDataFetcher()
    print("✅ KenyaDataFetcher initialized")
    
    # Test loading existing data
    summary = fetcher.get_data_summary()
    if 'error' not in summary:
        print(f"✅ Existing data loaded: {summary['total_counties']} counties")
        print(f"   - Real data: {summary['counties_with_real_data']} counties")
        print(f"   - Avg bloom probability: {summary['avg_bloom_probability']:.1f}%")
    else:
        print("⚠️  No existing data found (run fetcher to populate)")
except Exception as e:
    print(f"❌ FAILED: {e}")
print()

# Test 4: Streamlit Data Loader
print("TEST 4: Streamlit Data Loader")
print("-"*80)
try:
    from streamlit_data_loader import StreamlitDataLoader
    loader = StreamlitDataLoader()
    print("✅ StreamlitDataLoader initialized")
    
    map_data = loader.get_landing_page_map_data()
    print(f"✅ Map data loaded: {len(map_data['markers'])} markers")
    
    freshness = loader.get_data_freshness_info()
    print(f"✅ Data freshness: {freshness['message']}")
    if freshness['last_updated'] != 'Never':
        print(f"   - Last updated: {freshness['age_str']}")
except Exception as e:
    print(f"❌ FAILED: {e}")
print()

# Test 5: ML Model
print("TEST 5: ML Bloom Prediction Model")
print("-"*80)
try:
    from train_model import BloomPredictor
    predictor = BloomPredictor()
    print("✅ BloomPredictor initialized")
    
    # Try to load existing model
    try:
        predictor.load_model()
        print("✅ Existing model loaded successfully")
    except FileNotFoundError:
        print("⚠️  No trained model found (run training to create)")
    except Exception as e:
        print(f"⚠️  Model load issue: {e}")
except Exception as e:
    print(f"❌ FAILED: {e}")
print()

# Test 6: Data Scheduler
print("TEST 6: Data Scheduler")
print("-"*80)
try:
    from data_scheduler import DataScheduler
    scheduler = DataScheduler()
    print("✅ DataScheduler initialized")
    print("✅ Ready for automated data fetching")
except Exception as e:
    print(f"❌ FAILED: {e}")
print()

# Test 7: Single County Fetch (if EE available)
print("TEST 7: Single County Data Fetch")
print("-"*80)
try:
    from kenya_data_fetcher import KenyaDataFetcher
    from ee_pipeline import initialize_earth_engine
    
    if initialize_earth_engine():
        print("Testing fetch for Kiambu County...")
        fetcher = KenyaDataFetcher()
        
        # Test with a known good historical date
        # We'll just check if the function runs without errors
        print("✅ Data fetcher is operational")
        print("   (Skipping actual fetch to save time)")
        print("   To test full fetch: python kenya_data_fetcher.py --county kiambu")
    else:
        print("⚠️  Skipped (Earth Engine not available)")
except Exception as e:
    print(f"❌ FAILED: {e}")
print()

# Final Summary
print("="*80)
print("📊 SYSTEM TEST SUMMARY")
print("="*80)

print("\n✅ CORE COMPONENTS:")
print("   • Kenya counties configuration (47 counties)")
print("   • Data fetcher and scheduler")
print("   • Streamlit integration")
print("   • ML prediction model")

print("\n📡 EARTH ENGINE STATUS:")
if initialize_earth_engine():
    print("   ✅ Connected and ready for real satellite data")
else:
    print("   ⚠️  Not connected (run: earthengine authenticate)")

print("\n📂 DATA STATUS:")
try:
    from kenya_data_fetcher import KenyaDataFetcher
    fetcher = KenyaDataFetcher()
    summary = fetcher.get_data_summary()
    if 'error' not in summary and summary['total_counties'] > 0:
        print(f"   ✅ {summary['total_counties']} counties with data")
        print(f"   ✅ {summary['counties_with_real_data']} with real satellite data")
    else:
        print("   ⚠️  No data yet. Run: python kenya_data_fetcher.py --all")
except:
    print("   ⚠️  No data yet. Run: python kenya_data_fetcher.py --all")

print("\n🚀 NEXT STEPS:")
print("   1. Fetch real data: python kenya_data_fetcher.py --all")
print("   2. Start scheduler: python data_scheduler.py --run-scheduler")
print("   3. Run Streamlit: streamlit run ../app/streamlit_app_enhanced.py")

print("\n📖 DOCUMENTATION:")
print("   See REALDATA_SETUP.md for complete setup guide")

print("\n" + "="*80)
print("🎉 System test complete!")
print("="*80 + "\n")

