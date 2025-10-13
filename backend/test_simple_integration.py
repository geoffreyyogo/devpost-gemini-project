"""
Simple Integration Test for BloomWatch Kenya
Tests the system without requiring heavy dependencies
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_python_environment():
    """Test basic Python environment"""
    print("🐍 Testing Python Environment")
    print("-" * 40)
    
    print(f"✅ Python Version: {sys.version.split()[0]}")
    print(f"✅ Working Directory: {os.getcwd()}")
    print(f"✅ Virtual Environment: {'venv' in sys.prefix}")
    
    return True

def test_basic_imports():
    """Test basic imports"""
    print("\n📦 Testing Basic Imports")
    print("-" * 40)
    
    imports_status = {}
    
    # Test standard library
    try:
        import json
        import csv
        from datetime import datetime, timedelta
        imports_status['standard_library'] = True
        print("✅ Standard Library: OK")
    except ImportError as e:
        imports_status['standard_library'] = False
        print(f"❌ Standard Library: {e}")
    
    # Test numpy
    try:
        import numpy as np
        imports_status['numpy'] = True
        print(f"✅ NumPy: {np.__version__}")
    except ImportError:
        imports_status['numpy'] = False
        print("❌ NumPy: Not installed")
    
    # Test pandas
    try:
        import pandas as pd
        imports_status['pandas'] = True
        print(f"✅ Pandas: {pd.__version__}")
    except ImportError:
        imports_status['pandas'] = False
        print("❌ Pandas: Not installed")
    
    # Test scikit-learn
    try:
        import sklearn
        imports_status['sklearn'] = True
        print(f"✅ Scikit-learn: {sklearn.__version__}")
    except ImportError:
        imports_status['sklearn'] = False
        print("❌ Scikit-learn: Not installed")
    
    # Test Earth Engine
    try:
        import ee
        imports_status['earthengine'] = True
        print(f"✅ Earth Engine: {ee.__version__}")
    except ImportError:
        imports_status['earthengine'] = False
        print("❌ Earth Engine: Not installed")
    
    return imports_status

def test_file_structure():
    """Test file structure"""
    print("\n📁 Testing File Structure")
    print("-" * 40)
    
    files_to_check = [
        'ee_pipeline.py',
        'bloom_processor.py', 
        'train_model.py',
        'gee_data_loader.py',
        'test_integration.py'
    ]
    
    structure_status = {}
    
    for filename in files_to_check:
        if os.path.exists(filename):
            structure_status[filename] = True
            print(f"✅ {filename}: Found")
        else:
            structure_status[filename] = False
            print(f"❌ {filename}: Missing")
    
    # Check data directories
    data_dir = os.path.join('..', 'data')
    exports_dir = os.path.join(data_dir, 'exports')
    
    if os.path.exists(data_dir):
        print(f"✅ Data directory: Found")
        structure_status['data_dir'] = True
    else:
        print(f"❌ Data directory: Missing")
        structure_status['data_dir'] = False
    
    return structure_status

def test_synthetic_data_generation():
    """Test synthetic data generation without dependencies"""
    print("\n🎲 Testing Synthetic Data Generation")
    print("-" * 40)
    
    try:
        # Simple synthetic data generation
        import random
        import json
        from datetime import datetime, timedelta
        
        # Generate synthetic bloom data
        current_month = datetime.now().month
        
        # Kenya seasonal patterns
        if 3 <= current_month <= 5:  # Long rains
            bloom_probability = random.uniform(60, 90)
            ndvi_value = random.uniform(0.5, 0.8)
        elif 10 <= current_month <= 12:  # Short rains
            bloom_probability = random.uniform(40, 70)
            ndvi_value = random.uniform(0.4, 0.7)
        else:  # Dry seasons
            bloom_probability = random.uniform(10, 40)
            ndvi_value = random.uniform(0.2, 0.5)
        
        synthetic_data = {
            'date': datetime.now().isoformat(),
            'region': 'Kenya',
            'bloom_probability_percent': bloom_probability,
            'ndvi_mean': ndvi_value,
            'season': 'long_rains' if 3 <= current_month <= 5 else 'short_rains' if 10 <= current_month <= 12 else 'dry',
            'synthetic': True
        }
        
        print(f"✅ Synthetic Data Generated:")
        print(f"   📅 Date: {synthetic_data['date'][:10]}")
        print(f"   🌍 Region: {synthetic_data['region']}")
        print(f"   🌸 Bloom Probability: {synthetic_data['bloom_probability_percent']:.1f}%")
        print(f"   🌱 NDVI: {synthetic_data['ndvi_mean']:.3f}")
        print(f"   🌧️ Season: {synthetic_data['season']}")
        
        # Test CSV writing
        csv_file = 'test_synthetic_data.csv'
        try:
            import csv
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=synthetic_data.keys())
                writer.writeheader()
                writer.writerow(synthetic_data)
            print(f"✅ CSV Export: {csv_file}")
            
            # Clean up
            os.remove(csv_file)
            
        except Exception as e:
            print(f"❌ CSV Export Failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Synthetic Data Generation Failed: {e}")
        return False

def test_ml_fallback():
    """Test ML fallback logic without scikit-learn"""
    print("\n🤖 Testing ML Fallback Logic")
    print("-" * 40)
    
    try:
        # Simple rule-based bloom prediction
        import random
        
        # Sample input features (normally from satellite data)
        ndvi = random.uniform(0.2, 0.8)
        ndwi = random.uniform(0.1, 0.6)
        rainfall = random.uniform(0, 150)
        temperature = random.uniform(18, 28)
        
        print(f"📊 Input Features:")
        print(f"   NDVI: {ndvi:.3f}")
        print(f"   NDWI: {ndwi:.3f}")
        print(f"   Rainfall: {rainfall:.1f} mm")
        print(f"   Temperature: {temperature:.1f}°C")
        
        # Simple rule-based prediction
        bloom_score = 0
        
        # NDVI contribution (0-40 points)
        if ndvi > 0.5:
            bloom_score += 30
        elif ndvi > 0.3:
            bloom_score += 15
        
        # NDWI contribution (0-30 points)
        if ndwi > 0.3:
            bloom_score += 25
        elif ndwi > 0.2:
            bloom_score += 10
        
        # Rainfall contribution (0-20 points)
        if rainfall > 50:
            bloom_score += 15
        elif rainfall > 20:
            bloom_score += 8
        
        # Temperature contribution (0-10 points)
        if 20 <= temperature <= 26:
            bloom_score += 8
        elif 18 <= temperature <= 28:
            bloom_score += 5
        
        bloom_probability = min(100, bloom_score)
        
        prediction = {
            'bloom_probability_percent': bloom_probability,
            'bloom_prediction': 1 if bloom_probability > 50 else 0,
            'confidence': 'High' if bloom_probability > 70 or bloom_probability < 30 else 'Medium',
            'method': 'Rule-based fallback'
        }
        
        print(f"\n🔮 Prediction Results:")
        print(f"   🌸 Bloom Probability: {prediction['bloom_probability_percent']:.0f}%")
        print(f"   📊 Prediction: {'Bloom Expected' if prediction['bloom_prediction'] == 1 else 'No Bloom Expected'}")
        print(f"   📈 Confidence: {prediction['confidence']}")
        print(f"   🔧 Method: {prediction['method']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Fallback Failed: {e}")
        return False

def main():
    """Run simple integration tests"""
    print("🌸 BLOOMWATCH KENYA - SIMPLE INTEGRATION TEST")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    tests = []
    
    tests.append(('Python Environment', test_python_environment()))
    
    imports_status = test_basic_imports()
    tests.append(('Basic Imports', any(imports_status.values())))
    
    structure_status = test_file_structure()
    tests.append(('File Structure', all(structure_status.values())))
    
    tests.append(('Synthetic Data', test_synthetic_data_generation()))
    tests.append(('ML Fallback', test_ml_fallback()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, status in tests if status)
    total = len(tests)
    
    for test_name, status in tests:
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready for development.")
    elif passed >= total * 0.6:
        print("⚠️ MOST TESTS PASSED. Install missing dependencies to unlock full functionality.")
    else:
        print("🚨 SEVERAL TESTS FAILED. Check dependencies and file structure.")
    
    # Installation guidance
    print(f"\n💡 NEXT STEPS:")
    
    if not imports_status.get('numpy', False):
        print("   pip install numpy pandas scikit-learn")
    
    if not imports_status.get('earthengine', False):
        print("   pip install earthengine-api")
        print("   earthengine authenticate")
    
    print("   python3 test_integration.py  # Run full test suite")
    
    return passed, total

if __name__ == "__main__":
    main()
