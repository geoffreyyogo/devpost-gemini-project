#!/usr/bin/env python3
"""
Test script to fetch data for a single county and verify county-specific ML predictions
"""

import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from kenya_data_fetcher import KenyaDataFetcher
from train_model import BloomPredictor
import json

def test_single_county_fetch(county_id='nairobi'):
    """Fetch data for a single county and show the prediction"""
    
    print(f"\n{'='*70}")
    print(f"Testing County-Specific Data Fetch: {county_id.upper()}")
    print(f"{'='*70}\n")
    
    try:
        # Initialize fetcher
        fetcher = KenyaDataFetcher()
        
        print(f"📡 Fetching satellite data for {county_id}...")
        county_data = fetcher.fetch_county_data(county_id, days_back=7)
        
        if 'error' in county_data:
            print(f"❌ Error: {county_data['error']}")
            return
        
        print(f"✅ Data fetched successfully!\n")
        
        # Display results
        print(f"{'='*70}")
        print(f"RESULTS FOR: {county_data['county_name']}")
        print(f"{'='*70}\n")
        
        print("📊 SATELLITE DATA:")
        sat = county_data['satellite_data']
        print(f"  • NDVI (Vegetation):     {sat['ndvi']:.4f}")
        print(f"  • NDWI (Water/Blooms):   {sat.get('ndwi', 0):.4f}")
        print(f"  • Temperature:           {sat['temperature_c']:.1f}°C")
        print(f"  • Rainfall:              {sat['rainfall_mm']:.1f}mm")
        print(f"  • Data Source:           {sat['data_source']}")
        print(f"  • Real Data:             {sat['is_real_data']}")
        
        print(f"\n🌸 BLOOM DATA:")
        bloom = county_data['bloom_data']
        print(f"  • Current Bloom Level:   {bloom['bloom_percentage']:.2f}%")
        print(f"  • Bloom Area:            {bloom['bloom_area_km2']:.2f} km²")
        print(f"  • Bloom Forecast (ML):   {bloom['bloom_probability']:.2f}%")
        print(f"  • Prediction:            {bloom['bloom_prediction']}")
        print(f"  • Confidence:            {bloom['confidence']}")
        print(f"  • Message:               {bloom['message']}")
        
        print(f"\n{'='*70}\n")
        
        return county_data
        
    except Exception as e:
        print(f"❌ Error during fetch: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_multiple_counties():
    """Test 3 different counties to show predictions vary"""
    
    print(f"\n{'='*70}")
    print(f"TESTING MULTIPLE COUNTIES - Verify Different Predictions")
    print(f"{'='*70}\n")
    
    test_counties = ['nairobi', 'garissa', 'mombasa']
    results = []
    
    for county_id in test_counties:
        print(f"\n📍 Testing {county_id.upper()}...")
        print("-" * 70)
        
        county_data = test_single_county_fetch(county_id)
        if county_data:
            results.append({
                'name': county_data['county_name'],
                'ndvi': county_data['satellite_data']['ndvi'],
                'temp': county_data['satellite_data']['temperature_c'],
                'bloom_forecast': county_data['bloom_data']['bloom_probability'],
                'bloom_current': county_data['bloom_data']['bloom_percentage'],
                'message': county_data['bloom_data']['message']
            })
    
    # Summary comparison
    if len(results) > 1:
        print(f"\n{'='*70}")
        print(f"COMPARISON SUMMARY - County-Specific Predictions")
        print(f"{'='*70}\n")
        
        print(f"{'County':<15} {'NDVI':<10} {'Temp':<10} {'Forecast':<12} {'Current':<10}")
        print("-" * 70)
        for r in results:
            print(f"{r['name']:<15} {r['ndvi']:<10.3f} {r['temp']:<10.1f} {r['bloom_forecast']:<12.2f}% {r['bloom_current']:<10.2f}%")
        
        # Check if predictions vary
        forecasts = [r['bloom_forecast'] for r in results]
        if len(set(forecasts)) == 1:
            print(f"\n⚠️  WARNING: All counties have same forecast ({forecasts[0]:.2f}%)")
            print("   This suggests the fix may not be working correctly.")
        else:
            print(f"\n✅ SUCCESS: Counties have different forecasts!")
            print(f"   Range: {min(forecasts):.2f}% to {max(forecasts):.2f}%")
            print("   This confirms county-specific predictions are working!")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test single county data fetch')
    parser.add_argument('--county', type=str, default='nairobi', 
                       help='County ID to test (default: nairobi)')
    parser.add_argument('--multiple', action='store_true',
                       help='Test multiple counties to verify different predictions')
    
    args = parser.parse_args()
    
    if args.multiple:
        test_multiple_counties()
    else:
        test_single_county_fetch(args.county)

