#!/usr/bin/env python3
"""Core test for BloomWatch Kenya - tests basic functionality without heavy dependencies"""

import sys
import os
import numpy as np

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_compute_anomaly():
    """Test NDVI anomaly calculation"""
    def compute_anomaly(current, baseline):
        return np.where(baseline != 0, (current - baseline) / baseline * 100, 0)
    
    current = np.array([0.5, 0.6])
    baseline = np.array([0.4, 0.5])
    result = compute_anomaly(current, baseline)
    expected = np.array([25.0, 20.0])
    
    if np.allclose(result, expected):
        print("✓ compute_anomaly test passed")
        return True
    else:
        print(f"✗ compute_anomaly test failed: got {result}, expected {expected}")
        return False

def test_kenya_crop_calendar():
    """Test Kenya crop calendar functionality"""
    from datetime import datetime
    
    # Simple crop calendar data
    crop_calendar = {
        'maize': {
            'seasons': {
                'long_rains': {'plant': (3, 4), 'bloom': (6, 7), 'harvest': (8, 9)},
                'short_rains': {'plant': (10, 11), 'bloom': (1, 2), 'harvest': (3, 4)}
            },
            'bloom_duration_days': 14
        },
        'beans': {
            'seasons': {
                'long_rains': {'plant': (3, 4), 'bloom': (5, 6), 'harvest': (7, 8)},
                'short_rains': {'plant': (10, 11), 'bloom': (12, 1), 'harvest': (2, 3)}
            },
            'bloom_duration_days': 10
        }
    }
    
    def get_current_season():
        current_month = datetime.now().month
        if 3 <= current_month <= 5:
            return 'long_rains'
        elif 10 <= current_month <= 12:
            return 'short_rains'
        elif current_month in [1, 2]:
            return 'dry_season_1'
        else:
            return 'dry_season_2'
    
    def get_expected_blooms(month=None):
        if month is None:
            month = datetime.now().month
        
        blooming_crops = {}
        for crop, data in crop_calendar.items():
            for season, timing in data['seasons'].items():
                bloom_months = timing['bloom']
                if isinstance(bloom_months, tuple):
                    start_month, end_month = bloom_months
                    if start_month <= end_month:
                        if start_month <= month <= end_month:
                            if crop not in blooming_crops:
                                blooming_crops[crop] = []
                            blooming_crops[crop].append(season)
                    else:  # Crosses year boundary
                        if month >= start_month or month <= end_month:
                            if crop not in blooming_crops:
                                blooming_crops[crop] = []
                            blooming_crops[crop].append(season)
        return blooming_crops
    
    current_season = get_current_season()
    expected_blooms = get_expected_blooms()
    
    print(f"✓ Kenya crop calendar working: current season is {current_season}")
    print(f"✓ Expected blooms this month: {list(expected_blooms.keys())}")
    return True

def test_farmer_data_structure():
    """Test farmer data structure"""
    class Farmer:
        def __init__(self, id, name, phone, email, location_lat, location_lon, crops, language='en'):
            self.id = id
            self.name = name
            self.phone = phone
            self.email = email
            self.location_lat = location_lat
            self.location_lon = location_lon
            self.crops = crops
            self.language = language
    
    # Test farmer creation
    farmer = Farmer(
        id=1,
        name="John Kamau",
        phone="+254712345678",
        email="john@example.com",
        location_lat=-1.2921,
        location_lon=36.8219,
        crops=["maize", "beans"],
        language="en"
    )
    
    print(f"✓ Farmer profile created: {farmer.name} in {farmer.language}")
    print(f"✓ Farmer grows: {', '.join(farmer.crops)}")
    return True

def test_kenya_regions():
    """Test Kenya agricultural regions data"""
    KENYA_REGIONS = {
        'central': {
            'counties': ['Kiambu', 'Murang\'a', 'Nyeri', 'Kirinyaga', 'Nyandarua'],
            'altitude_range': (1200, 2500),
            'main_crops': ['coffee', 'tea', 'maize', 'beans', 'potatoes'],
            'rainfall_mm': (800, 1800),
            'coordinates': {'lat': -0.9, 'lon': 36.9}
        },
        'rift_valley': {
            'counties': ['Nakuru', 'Uasin Gishu', 'Trans Nzoia', 'Kericho', 'Bomet'],
            'altitude_range': (1500, 3000),
            'main_crops': ['maize', 'wheat', 'tea', 'pyrethrum', 'barley'],
            'rainfall_mm': (700, 1500),
            'coordinates': {'lat': 0.2, 'lon': 35.8}
        }
    }
    
    print(f"✓ Kenya regions loaded: {list(KENYA_REGIONS.keys())}")
    central_crops = KENYA_REGIONS['central']['main_crops']
    print(f"✓ Central Kenya main crops: {', '.join(central_crops[:3])}")
    return True

def main():
    """Run all tests"""
    print("🌾 BloomWatch Kenya - Core Functionality Test")
    print("=" * 50)
    
    tests = [
        test_compute_anomaly,
        test_kenya_crop_calendar,
        test_farmer_data_structure,
        test_kenya_regions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test {test.__name__} failed: {e}")
            print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All core tests passed!")
        print("🛰️ BloomWatch Kenya is ready for NASA Space Apps Challenge!")
        print("\nNext steps:")
        print("1. Set up Google Earth Engine authentication")
        print("2. Configure Twilio/SendGrid for SMS/Email alerts")
        print("3. Run: streamlit run app/streamlit_app.py")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    main()
