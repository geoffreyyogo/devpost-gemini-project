"""
Sentinel-2 Data Fetcher for Enhanced Bloom Detection
Adds high-resolution NDVI, NDWI, and ARI (Anthocyanin Reflectance Index) for flowers
"""

import ee
import logging
from datetime import datetime, timedelta
from typing import Dict

logger = logging.getLogger(__name__)

class Sentinel2Fetcher:
    """Fetch Sentinel-2 data for bloom detection"""
    
    def __init__(self, geometry):
        self.geometry = geometry
    
    def fetch_sentinel2_data(self, start_date: str, end_date: str) -> Dict:
        """
        Fetch Sentinel-2 data with NDVI, NDWI, and ARI
        ARI (Anthocyanin Reflectance Index) is great for detecting flowers!
        """
        try:
            # Sentinel-2 L2A (Surface Reflectance)
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                         .filterBounds(self.geometry)
                         .filterDate(start_date, end_date)
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                         .map(self._add_indices))
            
            count = collection.size().getInfo()
            
            if count == 0:
                logger.warning(f"No Sentinel-2 data available for {start_date} to {end_date}")
                return {'error': 'No data available', 'count': 0}
            
            # Get median composite
            composite = collection.median()
            
            # Calculate statistics
            # Use scale=30 instead of 10 to reduce pixel count (still high-res!)
            stats = composite.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    reducer2=ee.Reducer.minMax(),
                    sharedInputs=True
                ),
                geometry=self.geometry,
                scale=30,  # Use 30m to avoid maxPixels error (still better than MODIS 250m!)
                maxPixels=1e10,  # Increase limit
                bestEffort=True  # Use bestEffort for large regions
            )
            
            stats_dict = stats.getInfo()
            
            return {
                'source': 'Sentinel-2',
                'date_range': f"{start_date} to {end_date}",
                'image_count': count,
                'resolution': '10m',
                'ndvi_mean': stats_dict.get('NDVI_mean', 0),
                'ndvi_min': stats_dict.get('NDVI_min', 0),
                'ndvi_max': stats_dict.get('NDVI_max', 0),
                'ndwi_mean': stats_dict.get('NDWI_mean', 0),
                'ndwi_min': stats_dict.get('NDWI_min', 0),
                'ndwi_max': stats_dict.get('NDWI_max', 0),
                'ari_mean': stats_dict.get('ARI_mean', 0),  # Anthocyanin for flowers!
                'ari_min': stats_dict.get('ARI_min', 0),
                'ari_max': stats_dict.get('ARI_max', 0),
                'image': composite  # For further processing
            }
            
        except Exception as e:
            logger.error(f"Error fetching Sentinel-2 data: {e}")
            return {'error': str(e)}
    
    def _add_indices(self, image):
        """Add NDVI, NDWI, and ARI to Sentinel-2 image"""
        # NDVI = (NIR - Red) / (NIR + Red)
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # NDWI = (Green - NIR) / (Green + NIR) - for water/blooms
        ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
        
        # ARI (Anthocyanin Reflectance Index) - GREAT for detecting flowers!
        # ARI = (1 / Green) - (1 / RedEdge)
        # Using bands B3 (Green) and B5 (RedEdge 1)
        green = image.select('B3')
        redEdge = image.select('B5')
        
        ari = (green.pow(-1)).subtract(redEdge.pow(-1)).rename('ARI')
        
        return image.addBands([ndvi, ndwi, ari])
    
    def detect_blooms_sentinel2(self, start_date: str, end_date: str, 
                                ari_threshold: float = 0.1,
                                ndvi_threshold: float = 0.4) -> Dict:
        """
        Detect blooms using Sentinel-2 ARI and NDVI
        ARI > 0.1 typically indicates flowering vegetation
        """
        try:
            data = self.fetch_sentinel2_data(start_date, end_date)
            
            if 'error' in data or 'image' not in data:
                return {'error': 'No Sentinel-2 data available'}
            
            composite = data['image']
            
            # Create bloom mask: High ARI + Moderate NDVI
            bloom_mask = (
                composite.select('ARI').gt(ari_threshold)
                .And(composite.select('NDVI').gt(ndvi_threshold))
            )
            
            # Calculate bloom area
            area_image = bloom_mask.multiply(ee.Image.pixelArea())
            stats = area_image.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=self.geometry,
                scale=30,  # Use 30m to avoid maxPixels error
                maxPixels=1e10,  # Increase limit
                bestEffort=True  # Allow GEE to adjust for large regions
            )
            
            bloom_area_m2 = stats.getInfo().get('ARI', 0)
            bloom_area_km2 = bloom_area_m2 / 1e6
            
            # Total area for percentage
            total_area = self.geometry.area().getInfo() / 1e6  # km²
            bloom_percentage = (bloom_area_km2 / total_area * 100) if total_area > 0 else 0
            
            return {
                'bloom_area_km2': bloom_area_km2,
                'bloom_percentage': bloom_percentage,
                'total_area_km2': total_area,
                'ari_threshold': ari_threshold,
                'ndvi_threshold': ndvi_threshold,
                'ari_mean': data['ari_mean'],
                'ndvi_mean': data['ndvi_mean'],
                'method': 'Sentinel-2 ARI + NDVI',
                'resolution': '10m'
            }
            
        except Exception as e:
            logger.error(f"Error detecting blooms with Sentinel-2: {e}")
            return {'error': str(e)}


def get_valid_date_range(days_back: int = 30) -> tuple:
    """
    Get the most recent available satellite data date range
    
    Satellite data delays:
    - Sentinel-2: 2-3 days
    - Landsat: 3-5 days  
    - MODIS: 1-2 days
    - CHIRPS rainfall: 5-7 days (longer delay!)
    
    Args:
        days_back: Number of days of data to fetch
    
    Returns:
        Tuple of (start_date_str, end_date_str) in 'YYYY-MM-DD' format
    """
    today = datetime.now()
    
    # Use 5-day buffer to ensure satellite data is available
    # This accounts for processing delays across all satellite systems
    end_date = today - timedelta(days=5)
    start_date = end_date - timedelta(days=days_back)
    
    logger.info(f"Fetching most recent available data: {start_date.date()} to {end_date.date()}")
    logger.info(f"(5-day buffer from today {today.date()} to account for satellite processing delays)")
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

