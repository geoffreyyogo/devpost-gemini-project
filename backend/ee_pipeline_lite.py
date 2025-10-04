"""
Lightweight Earth Engine pipeline for BloomWatch Kenya demo
Works without Earth Engine authentication for demo purposes
"""

import os
import numpy as np
from datetime import datetime
from ndvi_utils_lite import load_raster_demo, compute_anomaly, detect_blooms

EXPORT_DIR = '../data/exports'
os.makedirs(EXPORT_DIR, exist_ok=True)

def generate_kenya_demo_data():
    """Generate realistic demo data for Kenya agricultural regions"""
    
    # Kenya agricultural regions coordinates
    regions = {
        'central': {'lat': -0.9, 'lon': 36.9, 'crops': ['coffee', 'tea', 'maize']},
        'rift_valley': {'lat': 0.2, 'lon': 35.8, 'crops': ['maize', 'wheat', 'tea']},
        'western': {'lat': 0.5, 'lon': 34.8, 'crops': ['maize', 'sugarcane', 'bananas']},
        'eastern': {'lat': -1.5, 'lon': 37.5, 'crops': ['maize', 'beans', 'sorghum']}
    }
    
    # Generate seasonal NDVI patterns for Kenya
    months = 12
    ndvi_data = np.random.rand(months, 100, 100) * 0.6 + 0.2  # Base NDVI 0.2-0.8
    
    # Add seasonal patterns
    for month in range(months):
        # Long rains boost (March-May)
        if 2 <= month <= 4:  # March-May (0-indexed)
            ndvi_data[month] *= 1.4  # 40% increase during long rains
        # Short rains boost (October-December)  
        elif 9 <= month <= 11:  # October-December
            ndvi_data[month] *= 1.2  # 20% increase during short rains
        # Dry seasons
        elif month in [0, 1, 5, 6, 7, 8]:  # Dry periods
            ndvi_data[month] *= 0.8  # 20% decrease during dry seasons
    
    # Generate ARI data (Anthocyanin Reflectance Index for flowers)
    ari_data = np.random.rand(100, 100) * 0.3  # 0-0.3 range
    
    # Add bloom hotspots in agricultural areas
    for i in range(20, 80, 20):
        for j in range(20, 80, 20):
            ari_data[i:i+10, j:j+10] += 0.2  # Bloom hotspots
    
    return ndvi_data, ari_data, regions

def process_exports_for_detection(export_dir: str) -> dict:
    """Process demo data for bloom detection"""
    
    # Generate demo data
    ndvi_ts, ari, regions = generate_kenya_demo_data()
    
    # Use latest month for current NDVI
    current_month = datetime.now().month - 1  # 0-indexed
    ndvi = ndvi_ts[current_month % 12]
    
    # Compute baseline (average of all months)
    baseline = np.mean(ndvi_ts, axis=0)
    anomaly = compute_anomaly(ndvi, baseline)
    
    # Generate ARI time series
    ari_list = [ari.mean() + np.random.normal(0, 0.05) for _ in range(12)]
    
    # Detect blooms
    peaks, scores = detect_blooms(ndvi_ts, ari_list)
    
    return {
        'peaks': peaks, 
        'anomaly': anomaly.mean(), 
        'bloom_scores': scores,
        'ndvi': ndvi,
        'ari': ari,
        'ndvi_ts': ndvi_ts,
        'regions': regions
    }

def export_modis_ndvi_demo(bbox: list, start: str, end: str, description: str):
    """Demo version of MODIS export - generates synthetic data"""
    print(f"Demo: Would export MODIS NDVI for bbox {bbox} from {start} to {end}")
    print(f"Description: {description}")
    
    # Generate demo file
    demo_data = np.random.rand(100, 100) * 0.8 + 0.1
    export_path = os.path.join(EXPORT_DIR, f'{description}.npy')
    np.save(export_path, demo_data)
    print(f"Demo data saved to: {export_path}")
    
    return {"status": "demo_completed", "file": export_path}

if __name__ == "__main__":
    # Demo the pipeline
    print("🌾 BloomWatch Kenya - Demo Data Pipeline")
    print("=" * 50)
    
    # Generate demo export
    bbox = [36.5, -1.5, 37.5, -0.5]  # Central Kenya
    export_modis_ndvi_demo(bbox, '2024-01-01', '2024-12-31', 'kenya_demo_ndvi')
    
    # Process for detection
    results = process_exports_for_detection(EXPORT_DIR)
    print(f"\nDetection Results:")
    print(f"- Bloom peaks found: {len(results['peaks'])}")
    print(f"- Peak months: {results['peaks']}")
    print(f"- Mean anomaly: {results['anomaly']:.2f}%")
    print(f"- NDVI range: {results['ndvi'].min():.3f} - {results['ndvi'].max():.3f}")
    print(f"- ARI range: {results['ari'].min():.3f} - {results['ari'].max():.3f}")
    
    print("\n🛰️ Demo pipeline completed successfully!")
