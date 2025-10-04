import ee
import os
import numpy as np
from datetime import datetime
from ndvi_utils import load_raster, compute_anomaly, detect_blooms  # For post-export processing

# Auth (run once: ee.Authenticate())
# ee.Initialize(project='your-gee-project-id')  # Set your project ID

EXPORT_DIR = '../data/exports'
os.makedirs(EXPORT_DIR, exist_ok=True)

def export_modis_ndvi(bbox: list, start: str, end: str, description: str):
    """Export MODIS NDVI median as COG."""
    geom = ee.Geometry.Rectangle(bbox)
    collection = (ee.ImageCollection('MODIS/061/MOD13A2')
                  .filterBounds(geom)
                  .filterDate(start, end)
                  .select('NDVI')
                  .map(lambda img: ee.Image(img.multiply(0.0001))))
    median = collection.median().clip(geom)
    
    task = ee.batch.Export.image.toDrive({
        'image': median,
        'description': description,
        'folder': 'bloomwatch',
        'fileNamePrefix': f'{description}.tif',
        'region': geom,
        'scale': 1000,
        'maxPixels': 1e9,
        'fileFormat': 'GeoTIFF'
    })
    task.start()
    print(f"Export task started: {description}")
    return task

def process_exports_for_detection(export_dir: str) -> dict:
    """Load exports, run detection."""
    ndvi_file = os.path.join(export_dir, 'modis_ndvi_median.tif')
    ari_file = os.path.join(export_dir, 'landsat_ari_median.tif')
    
    # Check if files exist, create dummy data if not
    if os.path.exists(ndvi_file):
        ndvi = load_raster(ndvi_file)
    else:
        print(f"Warning: {ndvi_file} not found, using dummy data")
        ndvi = np.random.rand(100, 100) * 0.8
    
    if os.path.exists(ari_file):
        ari = load_raster(ari_file)
    else:
        print(f"Warning: {ari_file} not found, using dummy data")
        ari = np.random.rand(100, 100) * 0.2
    
    # Placeholder baseline (load or compute)
    baseline = np.full_like(ndvi, 0.3)  # Avg NDVI
    anomaly = compute_anomaly(ndvi, baseline)
    
    # For TS: Assume multiple files; here single for MVP
    dummy_ts = np.tile(ndvi, (5, 1, 1))  # Fake 5 steps
    dummy_ari_list = [ari.mean()] * 5
    peaks, scores = detect_blooms(dummy_ts, dummy_ari_list)
    
    return {'peaks': peaks, 'anomaly': anomaly.mean(), 'bloom_scores': scores, 'ndvi': ndvi, 'ari': ari}

if __name__ == "__main__":
    # Initialize Earth Engine (commented out for now)
    # ee.Initialize()
    
    bbox = [-120, 35, -118, 37]  # CA example
    # export_modis_ndvi(bbox, '2024-03-01', '2025-05-01', 'modis_ndvi_ca')
    
    # After export (monitor tasks in console), process
    results = process_exports_for_detection(EXPORT_DIR)
    print(results)
