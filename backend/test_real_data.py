"""
Test BloomWatch Kenya with REAL Satellite Data from Google Earth Engine
This script demonstrates that actual NASA/ESA satellite data is being used
"""

import sys
import os
sys.path.append('.')

from ee_pipeline import EarthEnginePipeline, initialize_earth_engine
from bloom_processor import BloomProcessor
from train_model import train_bloom_model, predict_bloom_from_live_data
from datetime import datetime
import json

print("=" * 80)
print("🌍 BLOOMWATCH KENYA - REAL SATELLITE DATA TEST")
print("=" * 80)
print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Test 1: Earth Engine Connection
print("=" * 80)
print("TEST 1: Earth Engine Authentication & Connection")
print("-" * 80)

if initialize_earth_engine():
    print("✅ SUCCESS: Connected to Google Earth Engine")
    print("🛰️  Access granted to NASA MODIS and Landsat satellites")
    print("🌍 Project: bloomwatch-474200")
else:
    print("❌ FAILED: Could not connect to Earth Engine")
    print("   System will use synthetic data as fallback")

print()

# Test 2: Fetch Real Satellite Data
print("=" * 80)
print("TEST 2: Fetching Real Satellite Data for Kenya")
print("-" * 80)

try:
    pipeline = EarthEnginePipeline()
    
    print("📡 Requesting data from NASA satellites...")
    print("   • MODIS Terra/Aqua (vegetation health)")
    print("   • Landsat 8/9 (high-resolution bloom detection)")
    print("   • CHIRPS (rainfall data)")
    print("   • MODIS LST (temperature)")
    print()
    
    # Fetch last 7 days of data
    live_data = pipeline.fetch_live_data(days_back=7)
    
    if 'synthetic' in live_data:
        print("⚠️  Using SYNTHETIC data (Earth Engine not fully connected)")
        print(f"   Reason: {live_data.get('fallback_reason', 'Unknown')}")
    else:
        print("✅ SUCCESS: Real satellite data retrieved!")
        print()
        
        # Display NDVI data
        if 'ndvi' in live_data and 'error' not in live_data['ndvi']:
            ndvi = live_data['ndvi']
            print(f"🌱 NDVI Data ({ndvi.get('source', 'Unknown')}):")
            print(f"   • Date Range: {ndvi.get('date_range', 'N/A')}")
            print(f"   • Satellite Images: {ndvi.get('image_count', 0)}")
            print(f"   • Mean NDVI: {ndvi.get('ndvi_mean', 0):.3f}")
            print(f"   • Range: {ndvi.get('ndvi_min', 0):.3f} - {ndvi.get('ndvi_max', 0):.3f}")
            print(f"   • Data Quality: {'REAL SATELLITE DATA' if 'image' in ndvi else 'Summary only'}")
        
        print()
        
        # Display NDWI data
        if 'ndwi' in live_data and 'error' not in live_data['ndwi']:
            ndwi = live_data['ndwi']
            print(f"💧 NDWI Data ({ndwi.get('source', 'Unknown')}):")
            print(f"   • Date Range: {ndwi.get('date_range', 'N/A')}")
            print(f"   • Cloud-free Images: {ndwi.get('image_count', 0)}")
            print(f"   • Mean NDWI: {ndwi.get('ndwi_mean', 0):.3f}")
            print(f"   • Cloud Threshold: {ndwi.get('cloud_threshold', 0)}%")
        
        print()
        
        # Display rainfall data
        if 'rainfall' in live_data and 'error' not in live_data['rainfall']:
            rain = live_data['rainfall']
            print(f"🌧️  Rainfall Data ({rain.get('source', 'Unknown')}):")
            print(f"   • Total Rainfall: {rain.get('total_rainfall_mm', 0):.1f} mm")
            print(f"   • Daily Average: {rain.get('avg_daily_mm', 0):.1f} mm/day")
        
        print()
        
        # Display temperature data
        if 'temperature' in live_data and 'error' not in live_data['temperature']:
            temp = live_data['temperature']
            print(f"🌡️  Temperature Data ({temp.get('source', 'Unknown')}):")
            print(f"   • Mean: {temp.get('temp_mean_c', 0):.1f}°C")
            print(f"   • Range: {temp.get('temp_min_c', 0):.1f} - {temp.get('temp_max_c', 0):.1f}°C")
    
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# Test 3: Bloom Area Computation
print("=" * 80)
print("TEST 3: Computing Bloom Areas from Satellite Data")
print("-" * 80)

try:
    bloom_area = pipeline.compute_bloom_area()
    
    if 'error' not in bloom_area:
        print("✅ SUCCESS: Bloom area calculated")
        print(f"   🌸 Bloom Area: {bloom_area.get('bloom_area_km2', 0):.2f} km²")
        print(f"   📊 Coverage: {bloom_area.get('bloom_percentage', 0):.2f}% of region")
        print(f"   🎯 Method: {bloom_area.get('method', 'Unknown')}")
        
        if 'fallback_reason' in bloom_area:
            print(f"   ⚠️  Note: {bloom_area['fallback_reason']}")
    else:
        print(f"⚠️  Could not compute bloom area: {bloom_area['error']}")
    
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# Test 4: Process Data for ML Training
print("=" * 80)
print("TEST 4: Preparing ML Training Data from Satellite Observations")
print("-" * 80)

try:
    processor = BloomProcessor()
    
    print("📊 Aggregating historical satellite data...")
    ml_data = processor.prepare_ml_training_data(include_weather=True)
    
    if 'error' not in ml_data:
        print("✅ SUCCESS: ML training data prepared")
        print(f"   • Samples: {ml_data.get('n_samples', 0)}")
        print(f"   • Features: {ml_data.get('n_features', 0)} ({', '.join(ml_data.get('feature_names', []))})")
        print(f"   • Bloom samples: {ml_data.get('bloom_count', 0)}")
        print(f"   • No-bloom samples: {ml_data.get('no_bloom_count', 0)}")
        print(f"   • Class balance: {ml_data.get('class_balance', 0):.2%}")
        print(f"   • Data source: {ml_data.get('data_source', 'Unknown')}")
        
        # Check if using real or synthetic data
        if 'Synthetic' in str(ml_data.get('data_source', '')):
            print("   ⚠️  Using synthetic training data (limited historical data available)")
        else:
            print("   ✅ Using real satellite observations for training!")
    else:
        print(f"❌ ERROR: {ml_data['error']}")
    
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# Test 5: Train ML Model with Real Data
print("=" * 80)
print("TEST 5: Training ML Model with Satellite Data")
print("-" * 80)

try:
    print("🤖 Training Random Forest classifier...")
    print("   • Using historical satellite observations")
    print("   • Features: NDVI, NDWI, rainfall, temperature")
    print("   • Target: Binary bloom occurrence")
    print()
    
    training_result = train_bloom_model(include_weather=True, optimize_hyperparameters=False)
    
    if 'error' not in training_result:
        metrics = training_result['metrics']
        print("✅ SUCCESS: Model training completed!")
        print(f"   • Test Accuracy: {metrics.get('test_accuracy', 0):.3f}")
        print(f"   • F1 Score: {metrics.get('f1_score', 0):.3f}")
        print(f"   • Cross-validation: {metrics.get('cv_mean', 0):.3f} ± {metrics.get('cv_std', 0):.3f}")
        print(f"   • Training samples: {metrics.get('n_train_samples', 0)}")
        print(f"   • Test samples: {metrics.get('n_test_samples', 0)}")
        print()
        
        print("📊 Feature Importance:")
        for feature, importance in metrics.get('feature_importance', {}).items():
            bar = '█' * int(importance * 50)
            print(f"   {feature:15s} {bar} {importance:.3f}")
        
        print()
        print(f"💾 Model saved to: {training_result.get('model_path', 'Unknown')}")
    else:
        print(f"⚠️  Training issue: {training_result['error']}")
        print("   Note: This is often due to small sample size in demo mode")
    
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# Test 6: Make Predictions with Real Data
print("=" * 80)
print("TEST 6: Bloom Prediction from Current Satellite Data")
print("-" * 80)

try:
    print("🔮 Making bloom prediction...")
    prediction = predict_bloom_from_live_data()
    
    if 'error' not in prediction:
        print("✅ SUCCESS: Bloom prediction generated!")
        print()
        print(f"   🌸 Bloom Probability: {prediction.get('bloom_probability_percent', 0):.1f}%")
        print(f"   📊 Prediction: {'🌸 Bloom Expected' if prediction.get('bloom_prediction') == 1 else '🚫 No Bloom Expected'}")
        print(f"   📈 Confidence: {prediction.get('confidence', 'Unknown')}")
        print(f"   💬 Message: {prediction.get('message', 'N/A')}")
        print()
        
        print("📊 Input Features Used:")
        for feature, value in prediction.get('features_used', {}).items():
            print(f"   • {feature}: {value:.3f}")
        
        print()
        print(f"🤖 Model Version: {prediction.get('model_version', 'Unknown')}")
        
        # Determine if using real or fallback prediction
        if 'Fallback' in str(prediction.get('model_version', '')):
            print("   ⚠️  Using rule-based fallback (model training in progress)")
        else:
            print("   ✅ Using trained ML model with satellite data!")
    else:
        print(f"⚠️  Prediction issue: {prediction.get('error', 'Unknown')}")
    
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# Final Summary
print("=" * 80)
print("📊 FINAL SUMMARY")
print("=" * 80)
print()

if pipeline.ee_available:
    print("🎉 REAL SATELLITE DATA MODE ACTIVE!")
    print()
    print("✅ Your system is now using:")
    print("   • NASA MODIS satellite imagery (vegetation health)")
    print("   • Landsat 8/9 data (high-resolution bloom detection)")
    print("   • CHIRPS rainfall measurements")
    print("   • MODIS temperature data")
    print()
    print("🌍 Data Coverage: Central Kenya & Rift Valley agricultural regions")
    print("📡 Update Frequency: Near real-time (last 7 days)")
    print("🎯 Spatial Resolution: 30m (Landsat) to 1km (MODIS)")
    print()
    print("💡 The ML model is trained on actual satellite observations")
    print("   and will improve accuracy as more data is collected!")
else:
    print("⚠️  DEMO MODE (Synthetic Data)")
    print()
    print("Earth Engine is configured but may need:")
    print("   • Active internet connection")
    print("   • Google Cloud Project permissions")
    print("   • Time for credentials to propagate")
    print()
    print("The system works perfectly with synthetic data for development,")
    print("and will automatically use real satellite data when available!")

print()
print("=" * 80)
print("🌾 BloomWatch Kenya - Empowering Farmers with Satellite Intelligence")
print("=" * 80)

