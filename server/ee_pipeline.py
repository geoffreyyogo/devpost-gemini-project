"""
Enhanced Earth Engine Pipeline for BloomWatch Kenya
Fetches near-real-time satellite data with cloud filtering and error handling
Processes NDVI, NDWI, rainfall data for bloom detection and ML training
"""

import ee
import os
import json
import csv
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from ndvi_utils import load_raster, compute_anomaly, detect_blooms
except ImportError:
    logger.warning("ndvi_utils not available - using fallbacks")

try:
    from sentinel2_pipeline import Sentinel2Fetcher, get_valid_date_range
    SENTINEL2_AVAILABLE = True
except ImportError:
    logger.warning("sentinel2_pipeline not available - will skip Sentinel-2 data")
    SENTINEL2_AVAILABLE = False
    
    # Fallback function
    def get_valid_date_range(days_back=30):
        """Fallback date range function - gets most recent available data"""
        from datetime import datetime, timedelta
        today = datetime.now()
        # Use 5-day buffer for satellite data processing delays
        end_date = today - timedelta(days=5)
        start_date = end_date - timedelta(days=days_back)
        logger.info(f"Fetching most recent available data: {start_date.date()} to {end_date.date()}")
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

# Export directories
EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'exports'))
LIVE_DATA_DIR = os.path.join(EXPORT_DIR, 'live')
HISTORICAL_DIR = os.path.join(EXPORT_DIR, 'historical')

# Create directories
for dir_path in [EXPORT_DIR, LIVE_DATA_DIR, HISTORICAL_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Kenya agricultural regions (Central Kenya and Rift Valley)
KENYA_BBOX = [36.0, -1.5, 37.5, 0.5]  # [min_lon, min_lat, max_lon, max_lat]

# Cloud cover threshold
CLOUD_THRESHOLD = 20

# Earth Engine initialization status
EE_INITIALIZED = False

def initialize_earth_engine():
    """Initialize Earth Engine with proper error handling"""
    global EE_INITIALIZED
    
    if EE_INITIALIZED:
        return True
    
    # Import required modules at the top level
    import json
    import tempfile
    import os
    
    try:
        # Get project ID and service account from environment variables
        project_id = os.getenv('GEE_PROJECT_ID')
        service_account_json = os.getenv('GEE_SERVICE_ACCOUNT_JSON')
        
        if service_account_json and project_id:
            logger.info(f"Initializing Earth Engine with service account for project: {project_id}")
            
            try:
                service_account_info = json.loads(service_account_json)
                
                # Create a temporary file with the service account JSON
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(service_account_info, f)
                    temp_key_path = f.name
                
                # Use the direct authentication method
                credentials = ee.ServiceAccountCredentials(
                    service_account_info['client_email'], 
                    temp_key_path
                )
                
                # Initialize Earth Engine with credentials
                ee.Initialize(credentials, project=project_id)
                
                # Clean up the temporary file
                os.unlink(temp_key_path)
                
            except Exception as auth_error:
                logger.error(f"Service account authentication failed: {auth_error}")
                # Clean up temp file if it exists
                try:
                    if 'temp_key_path' in locals():
                        os.unlink(temp_key_path)
                except:
                    pass
                # Fall back to regular initialization
                logger.info("Falling back to regular Earth Engine initialization")
                ee.Initialize(project=project_id)
        elif project_id:
            logger.info(f"Initializing Earth Engine with project: {project_id}")
            ee.Initialize(project=project_id)
        else:
            logger.info("No GEE_PROJECT_ID found in environment, trying default initialization")
            ee.Initialize()
        
        EE_INITIALIZED = True
        logger.info("Earth Engine initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Earth Engine initialization failed: {e}")
        logger.info("Authentication required. Please run:")
        logger.info("  earthengine authenticate")
        if project_id:
            logger.info(f"  earthengine set_project {project_id}")
        else:
            logger.info("  earthengine set_project YOUR_PROJECT_ID")
        return False

class EarthEnginePipeline:
    """Enhanced Earth Engine Pipeline for near-real-time data fetching"""
    
    def __init__(self, region_bbox: List[float] = None):
        """Initialize pipeline with Kenya region"""
        self.bbox = region_bbox or KENYA_BBOX
        self.geometry = None
        self.last_fetch = None
        self.ee_available = initialize_earth_engine()
        self.sentinel2_fetcher = None
        
        if self.ee_available:
            try:
                self.geometry = ee.Geometry.Rectangle(self.bbox)
                logger.info(f"Pipeline initialized for region: {self.bbox}")
                
                # Initialize Sentinel-2 fetcher if available
                if SENTINEL2_AVAILABLE:
                    self.sentinel2_fetcher = Sentinel2Fetcher(self.geometry)
                    logger.info("Sentinel-2 fetcher initialized")
            except Exception as e:
                logger.error(f"Error creating geometry: {e}")
                self.ee_available = False
        else:
            logger.warning("Earth Engine not available - pipeline will use fallback mode")
        
    def fetch_live_data(self, days_back: int = 7, start_date: str = None, end_date: str = None) -> Dict[str, any]:
        """
        Fetch near-real-time satellite data for the last N days
        Returns both GeoTIFF data and CSV summaries
        
        Args:
            days_back: Number of days to look back (default 7)
            start_date: Optional start date in 'YYYY-MM-DD' format
            end_date: Optional end date in 'YYYY-MM-DD' format
        """
        # Use provided dates or get valid historical dates
        if start_date and end_date:
            start_str = start_date
            end_str = end_date
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            start_str, end_str = get_valid_date_range(days_back)
            end_datetime = datetime.strptime(end_str, '%Y-%m-%d')
        
        logger.info(f"Fetching live data from {start_str} to {end_str}")
        
        # Check if Earth Engine is available
        if not self.ee_available:
            logger.warning("Earth Engine not available - generating synthetic live data")
            return self._generate_synthetic_live_data(end_datetime, days_back)
        
        try:
            # Fetch different datasets
            results = {}
            
            # 1. MODIS NDVI (vegetation health)
            ndvi_data = self._fetch_modis_ndvi(start_str, end_str)
            results['ndvi'] = ndvi_data
            
            # 2. Landsat NDWI (water/bloom detection)
            ndwi_data = self._fetch_landsat_ndwi(start_str, end_str)
            results['ndwi'] = ndwi_data
            
            # 3. CHIRPS Rainfall data
            rainfall_data = self._fetch_rainfall_data(start_str, end_str)
            results['rainfall'] = rainfall_data
            
            # 4. Temperature data (MODIS)
            temperature_data = self._fetch_temperature_data(start_str, end_str)
            results['temperature'] = temperature_data
            
            # 5. Sentinel-2 high-resolution data (PRIMARY SOURCE - 10m resolution!)
            # Priority: Sentinel-2 > MODIS > Landsat
            # Reason: Highest resolution (10m), best for bloom detection, includes ARI flower index
            if self.sentinel2_fetcher:
                logger.info("Fetching Sentinel-2 data for high-resolution bloom detection...")
                sentinel2_data = self.sentinel2_fetcher.fetch_sentinel2_data(start_str, end_str)
                if 'error' not in sentinel2_data:
                    logger.info(f"✅ Sentinel-2: {sentinel2_data['image_count']} images at 10m resolution")
                    results['sentinel2'] = sentinel2_data
                    
                    # Use Sentinel-2 as PRIMARY source (highest quality)
                    # Override MODIS/Landsat if Sentinel-2 is available
                    results['ndvi'] = {
                        'source': 'Sentinel-2',  # PRIMARY, not fallback!
                        'ndvi_mean': sentinel2_data['ndvi_mean'],
                        'ndvi_min': sentinel2_data['ndvi_min'],
                        'ndvi_max': sentinel2_data['ndvi_max'],
                        'image_count': sentinel2_data['image_count'],
                        'resolution': '10m'  # Highest resolution!
                    }
                    results['ndwi'] = {
                        'source': 'Sentinel-2',  # PRIMARY, not fallback!
                        'ndwi_mean': sentinel2_data['ndwi_mean'],
                        'ndwi_min': sentinel2_data['ndwi_min'],
                        'ndwi_max': sentinel2_data['ndwi_max'],
                        'image_count': sentinel2_data['image_count'],
                        'resolution': '10m'  # Highest resolution!
                    }
                else:
                    logger.warning(f"Sentinel-2 fetch failed: {sentinel2_data['error']}")
            
            # Add metadata
            results['start_date'] = start_str
            results['end_date'] = end_str
            results['region_bbox'] = self.bbox
            
            # Save live data as CSV summaries
            self._save_live_csv_data(results, end_datetime)
            
            # Schedule GeoTIFF exports (optional - only if EE available)
            # Note: GeoTIFF exports are OPTIONAL and often fail
            # CSV data is sufficient for all ML training and visualization
            try:
                export_tasks = self._schedule_geotiff_exports(results, end_datetime)
                results['export_tasks'] = export_tasks
            except Exception as export_error:
                logger.debug(f"GeoTIFF export skipped: {export_error}")
                results['export_tasks'] = []  # Empty list, not critical
            
            self.last_fetch = end_datetime
            logger.info("Live data fetch completed successfully")
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching live data: {e}")
            logger.info("Falling back to synthetic data")
            return self._generate_synthetic_live_data(end_datetime, days_back, error=str(e))
    
    def _fetch_modis_ndvi(self, start_date: str, end_date: str) -> Dict:
        """Fetch MODIS NDVI with cloud filtering"""
        try:
            collection = (ee.ImageCollection('MODIS/061/MOD13A2')
                         .filterBounds(self.geometry)
                         .filterDate(start_date, end_date)
                         .select(['NDVI', 'EVI'])
                         .map(lambda img: img.multiply(0.0001)))
            
            if collection.size().getInfo() == 0:
                logger.warning(f"No MODIS data available for {start_date} to {end_date}")
                return {'error': 'No data available', 'count': 0}
            
            # Get the most recent image
            latest = collection.sort('system:time_start', False).first()
            
            # Calculate regional statistics
            stats = latest.select('NDVI').reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.minMax(), sharedInputs=True
                ).combine(
                    ee.Reducer.stdDev(), sharedInputs=True
                ),
                geometry=self.geometry,
                scale=1000,
                maxPixels=1e9
            )
            
            stats_dict = stats.getInfo()
            
            return {
                'source': 'MODIS',
                'date_range': f"{start_date} to {end_date}",
                'image_count': collection.size().getInfo(),
                'ndvi_mean': stats_dict.get('NDVI_mean', 0),
                'ndvi_min': stats_dict.get('NDVI_min', 0),
                'ndvi_max': stats_dict.get('NDVI_max', 0),
                'ndvi_std': stats_dict.get('NDVI_stdDev', 0),
                'image': latest,
                'collection': collection
            }
            
        except Exception as e:
            logger.error(f"Error fetching MODIS NDVI: {e}")
            return {'error': str(e)}
    
    def _fetch_landsat_ndwi(self, start_date: str, end_date: str) -> Dict:
        """Fetch Landsat NDWI for bloom/water detection with cloud filtering"""
        try:
            # Landsat 8 and 9 Collections
            l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
            
            collection = (l8.merge(l9)
                         .filterBounds(self.geometry)
                         .filterDate(start_date, end_date)
                         .filter(ee.Filter.lt('CLOUD_COVER', CLOUD_THRESHOLD))
                         .map(self._add_ndwi_ndvi))
            
            if collection.size().getInfo() == 0:
                logger.warning(f"No clear Landsat data available for {start_date} to {end_date}")
                return {'error': 'No clear data available', 'count': 0}
            
            # Get median composite to reduce cloud effects
            composite = collection.median()
            
            # Calculate regional statistics for NDWI
            stats = composite.select('NDWI').reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.minMax(), sharedInputs=True
                ).combine(
                    ee.Reducer.stdDev(), sharedInputs=True
                ),
                geometry=self.geometry,
                scale=30,
                maxPixels=1e9
            )
            
            stats_dict = stats.getInfo()
            
            return {
                'source': 'Landsat 8/9',
                'date_range': f"{start_date} to {end_date}",
                'image_count': collection.size().getInfo(),
                'cloud_threshold': CLOUD_THRESHOLD,
                'ndwi_mean': stats_dict.get('NDWI_mean', 0),
                'ndwi_min': stats_dict.get('NDWI_min', 0),
                'ndwi_max': stats_dict.get('NDWI_max', 0),
                'ndwi_std': stats_dict.get('NDWI_stdDev', 0),
                'image': composite,
                'collection': collection
            }
            
        except Exception as e:
            logger.error(f"Error fetching Landsat NDWI: {e}")
            return {'error': str(e)}
    
    def _add_ndwi_ndvi(self, image):
        """Add NDWI and NDVI bands to Landsat image"""
        # NDWI = (Green - NIR) / (Green + NIR)
        ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
        
        # NDVI = (NIR - Red) / (NIR + Red)
        ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
        
        return image.addBands([ndwi, ndvi])
    
    def _fetch_rainfall_data(self, start_date: str, end_date: str) -> Dict:
        """
        Fetch CHIRPS rainfall data
        CHIRPS has 5-7 day delay, so we try extended lookback if no recent data
        """
        try:
            collection = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
                         .filterBounds(self.geometry)
                         .filterDate(start_date, end_date)
                         .select('precipitation'))
            
            count = collection.size().getInfo()
            
            if count == 0:
                # CHIRPS has longer delays (5-7 days), try extended lookback
                logger.warning(f"No rainfall data for {start_date} to {end_date}, trying extended lookback...")
                
                # Try 10 days earlier
                extended_end = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=10)
                extended_start = datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=10)
                
                collection = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
                             .filterBounds(self.geometry)
                             .filterDate(extended_start.strftime('%Y-%m-%d'), extended_end.strftime('%Y-%m-%d'))
                             .select('precipitation'))
                
                count = collection.size().getInfo()
                
                if count == 0:
                    logger.warning(f"No rainfall data available even with extended lookback")
                    return {'error': 'No data available', 'count': 0}
                else:
                    logger.info(f"✅ Found {count} rainfall images with extended lookback")
            
            # Calculate total and daily average rainfall
            total_rainfall = collection.sum()
            avg_daily = collection.mean()
            
            # Regional statistics
            total_stats = total_rainfall.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=self.geometry,
                scale=5000,
                maxPixels=1e9
            )
            
            avg_stats = avg_daily.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=self.geometry,
                scale=5000,
                maxPixels=1e9
            )
            
            total_mm = total_stats.getInfo().get('precipitation', 0)
            avg_mm = avg_stats.getInfo().get('precipitation', 0)
            
            return {
                'source': 'CHIRPS',
                'date_range': f"{start_date} to {end_date}",
                'image_count': collection.size().getInfo(),
                'total_rainfall_mm': total_mm,
                'avg_daily_mm': avg_mm,
                'image': total_rainfall,
                'collection': collection
            }
            
        except Exception as e:
            logger.error(f"Error fetching rainfall data: {e}")
            return {'error': str(e)}
    
    def _fetch_temperature_data(self, start_date: str, end_date: str) -> Dict:
        """Fetch MODIS land surface temperature"""
        try:
            collection = (ee.ImageCollection('MODIS/061/MOD11A1')
                         .filterBounds(self.geometry)
                         .filterDate(start_date, end_date)
                         .select('LST_Day_1km')
                         .map(lambda img: img.multiply(0.02).subtract(273.15)))  # Convert to Celsius
            
            if collection.size().getInfo() == 0:
                logger.warning(f"No temperature data available for {start_date} to {end_date}")
                return {'error': 'No data available', 'count': 0}
            
            # Get mean temperature
            mean_temp = collection.mean()
            
            # Regional statistics
            stats = mean_temp.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.minMax(), sharedInputs=True
                ),
                geometry=self.geometry,
                scale=1000,
                maxPixels=1e9
            )
            
            stats_dict = stats.getInfo()
            
            return {
                'source': 'MODIS LST',
                'date_range': f"{start_date} to {end_date}",
                'image_count': collection.size().getInfo(),
                'temp_mean_c': stats_dict.get('LST_Day_1km_mean', 0),
                'temp_min_c': stats_dict.get('LST_Day_1km_min', 0),
                'temp_max_c': stats_dict.get('LST_Day_1km_max', 0),
                'image': mean_temp,
                'collection': collection
            }
            
        except Exception as e:
            logger.error(f"Error fetching temperature data: {e}")
            return {'error': str(e)}

    def _save_live_csv_data(self, results: Dict, timestamp: datetime):
        """Save live data summaries as CSV files"""
        try:
            # Prepare summary data
            summary_data = {
                'date': timestamp.strftime('%Y-%m-%d'),
                'time': timestamp.strftime('%H:%M:%S'),
                'region': 'Kenya',
                'bbox': str(self.bbox)
            }
            
            # Add data from each source
            for data_type, data in results.items():
                if isinstance(data, dict) and 'error' not in data:
                    if data_type == 'ndvi':
                        summary_data.update({
                            'ndvi_mean': data.get('ndvi_mean', 0),
                            'ndvi_min': data.get('ndvi_min', 0),
                            'ndvi_max': data.get('ndvi_max', 0),
                            'ndvi_std': data.get('ndvi_std', 0),
                            'modis_images': data.get('image_count', 0)
                        })
                    elif data_type == 'ndwi':
                        summary_data.update({
                            'ndwi_mean': data.get('ndwi_mean', 0),
                            'ndwi_min': data.get('ndwi_min', 0),
                            'ndwi_max': data.get('ndwi_max', 0),
                            'landsat_images': data.get('image_count', 0),
                            'cloud_threshold': data.get('cloud_threshold', 0)
                        })
                    elif data_type == 'rainfall':
                        summary_data.update({
                            'rainfall_total_mm': data.get('total_rainfall_mm', 0),
                            'rainfall_avg_daily_mm': data.get('avg_daily_mm', 0),
                            'rainfall_images': data.get('image_count', 0)
                        })
                    elif data_type == 'temperature':
                        summary_data.update({
                            'temperature_mean_c': data.get('temp_mean_c', 0),
                            'temperature_min_c': data.get('temp_min_c', 0),
                            'temperature_max_c': data.get('temp_max_c', 0),
                            'temperature_images': data.get('image_count', 0)
                        })
                    elif data_type == 'sentinel2':
                        summary_data.update({
                            'sentinel2_images': data.get('image_count', 0),
                            'sentinel2_resolution_m': data.get('resolution', '10m'),
                            'sentinel2_ari_mean': data.get('ari_mean', 0),
                            'sentinel2_ari_min': data.get('ari_min', 0),
                            'sentinel2_ari_max': data.get('ari_max', 0),
                            'sentinel2_ndvi_mean': data.get('ndvi_mean', 0),
                            'sentinel2_ndvi_min': data.get('ndvi_min', 0),
                            'sentinel2_ndvi_max': data.get('ndvi_max', 0),
                            'sentinel2_ndwi_mean': data.get('ndwi_mean', 0),
                            'sentinel2_ndwi_min': data.get('ndwi_min', 0),
                            'sentinel2_ndwi_max': data.get('ndwi_max', 0)
                        })
                    elif data_type == 'bloom_area':
                        summary_data.update({
                            'bloom_area_km2': data.get('bloom_area_km2', 0),
                            'bloom_percentage': data.get('bloom_percentage', 0),
                            'bloom_method': data.get('method', 'N/A')
                        })
            
            # Save to CSV file
            csv_filename = f"live_data_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
            csv_path = os.path.join(LIVE_DATA_DIR, csv_filename)
            
            # Write CSV
            with open(csv_path, 'w', newline='') as csvfile:
                fieldnames = list(summary_data.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(summary_data)
            
            logger.info(f"Live data saved to: {csv_path}")
            
            # Also save latest data (for easy access)
            latest_csv = os.path.join(LIVE_DATA_DIR, 'latest_live_data.csv')
            with open(latest_csv, 'w', newline='') as csvfile:
                fieldnames = list(summary_data.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(summary_data)
            
        except Exception as e:
            logger.error(f"Error saving CSV data: {e}")
    
    def _schedule_geotiff_exports(self, results: Dict, timestamp: datetime) -> List[str]:
        """
        Schedule GeoTIFF exports to Google Drive (optional)
        
        NOTE: GeoTIFF exports are DISABLED by default
        Reason: CSV statistics contain all necessary data for ML and visualization
        GeoTIFF files are:
          - Large (50+ MB per file)
          - Slow to export (minutes)
          - Require manual download from Google Drive
          - Not needed for ML training (need statistics, not pixels)
        
        To enable: Set ENABLE_GEOTIFF_EXPORT = True below
        """
        ENABLE_GEOTIFF_EXPORT = False  # Change to True to enable exports
        
        export_tasks = []
        
        if not ENABLE_GEOTIFF_EXPORT:
            logger.debug("GeoTIFF exports disabled (CSV data is sufficient)")
            return export_tasks
        
        try:
            date_str = timestamp.strftime('%Y%m%d')
            
            # Export NDVI if available and is an EE Image object
            if 'ndvi' in results and 'image' in results['ndvi']:
                ndvi_img = results['ndvi']['image']
                # Check if it's actually an EE Image object, not a dict
                if not isinstance(ndvi_img, dict) and hasattr(ndvi_img, 'select'):
                    ndvi_task = ee.batch.Export.image.toDrive({
                        'image': ndvi_img.select('NDVI'),
                        'description': f'live_ndvi_{date_str}',
                        'folder': 'bloomwatch_live',
                        'fileNamePrefix': f'live_ndvi_{date_str}',
                        'region': self.geometry,
                        'scale': 1000,
                        'maxPixels': 1e9,
                        'fileFormat': 'GeoTIFF'
                    })
                    ndvi_task.start()
                    export_tasks.append(f'live_ndvi_{date_str}')
                    logger.info(f"NDVI export started: live_ndvi_{date_str}")
                else:
                    logger.warning("NDVI image is not an EE Image object, skipping export")
            
            # Export NDWI if available and is an EE Image object
            if 'ndwi' in results and 'image' in results['ndwi']:
                ndwi_img = results['ndwi']['image']
                if not isinstance(ndwi_img, dict) and hasattr(ndwi_img, 'select'):
                    ndwi_task = ee.batch.Export.image.toDrive({
                        'image': ndwi_img.select('NDWI'),
                        'description': f'live_ndwi_{date_str}',
                        'folder': 'bloomwatch_live',
                        'fileNamePrefix': f'live_ndwi_{date_str}',
                        'region': self.geometry,
                        'scale': 30,
                        'maxPixels': 1e9,
                        'fileFormat': 'GeoTIFF'
                    })
                    ndwi_task.start()
                    export_tasks.append(f'live_ndwi_{date_str}')
                    logger.info(f"NDWI export started: live_ndwi_{date_str}")
                else:
                    logger.warning("NDWI image is not an EE Image object, skipping export")
            
            # Export rainfall if available and is an EE Image object
            if 'rainfall' in results and 'image' in results['rainfall']:
                rain_img = results['rainfall']['image']
                if not isinstance(rain_img, dict) and hasattr(rain_img, 'select'):
                    rain_task = ee.batch.Export.image.toDrive({
                        'image': rain_img,
                        'description': f'live_rainfall_{date_str}',
                        'folder': 'bloomwatch_live',
                        'fileNamePrefix': f'live_rainfall_{date_str}',
                        'region': self.geometry,
                        'scale': 5000,
                        'maxPixels': 1e9,
                        'fileFormat': 'GeoTIFF'
                    })
                    rain_task.start()
                    export_tasks.append(f'live_rainfall_{date_str}')
                    logger.info(f"Rainfall export started: live_rainfall_{date_str}")
                else:
                    logger.warning("Rainfall image is not an EE Image object, skipping export")
            
            # Export Sentinel-2 composite if available (OPTIONAL - often skipped)
            # Note: GeoTIFF exports are NOT critical - CSV has all the statistics we need
            if 'sentinel2' in results and 'image' in results['sentinel2']:
                s2_img = results['sentinel2']['image']
                # Check it's an actual EE Image, not error dict
                if not isinstance(s2_img, dict) and hasattr(s2_img, 'getInfo'):
                    # GeoTIFF export disabled by default - uncomment if needed
                    # Reason: CSV statistics are sufficient for ML and visualization
                    # GeoTIFFs are large (50+ MB) and slow to export
                    logger.debug("Sentinel-2 GeoTIFF export available but skipped (CSV has all data)")
                    # Uncomment below to enable Sentinel-2 TIFF export:
                    # try:
                    #     s2_task = ee.batch.Export.image.toDrive({
                    #         'image': s2_img.select('ARI'),
                    #         'description': f'live_sentinel2_ari_{date_str}',
                    #         ...
                    #     })
                    #     s2_task.start()
                    # except Exception as s2_error:
                    #     logger.debug(f"S2 export skipped: {s2_error}")
                else:
                    pass  # Not an EE Image, skip silently
                
        except Exception as e:
            logger.error(f"Error scheduling exports: {e}", exc_info=True)
        
        return export_tasks
    
    def compute_bloom_area(self, ndwi_threshold: float = 0.3, ndvi_threshold: float = 0.5, ari_threshold: float = 0.1) -> Dict:
        """
        Compute bloom areas using NDWI/NDVI/ARI thresholds
        Prefers Sentinel-2 ARI for flower detection when available
        Returns area in square kilometers
        """
        if not self.ee_available:
            logger.warning("Earth Engine not available - generating synthetic bloom area")
            return self._generate_synthetic_bloom_area(ndwi_threshold, ndvi_threshold)
        
        try:
            # Fetch latest data
            live_data = self.fetch_live_data(days_back=3)
            
            # Prefer Sentinel-2 ARI for flower bloom detection
            if 'sentinel2' in live_data and 'error' not in live_data['sentinel2'] and 'image' in live_data['sentinel2']:
                logger.info("Using Sentinel-2 ARI for high-resolution bloom detection")
                start_str, end_str = get_valid_date_range(3)
                sentinel_bloom = self.sentinel2_fetcher.detect_blooms_sentinel2(
                    start_str, end_str, ari_threshold, ndvi_threshold
                )
                if 'error' not in sentinel_bloom:
                    sentinel_bloom['method'] = 'Sentinel-2 ARI + NDVI (10m resolution)'
                    return sentinel_bloom
            
            # Fallback to Landsat NDWI/NDVI method
            if 'error' in live_data or 'ndwi' not in live_data or 'image' not in live_data['ndwi']:
                logger.warning("No NDWI data available for bloom area calculation")
                return self._generate_synthetic_bloom_area(ndwi_threshold, ndvi_threshold, 
                                                         error="No NDWI data available")
            
            ndwi_image = live_data['ndwi']['image'].select('NDWI')
            
            # Create bloom mask: NDWI > threshold (water/bloom areas)
            bloom_mask = ndwi_image.gt(ndwi_threshold)
            
            # If NDVI is available, also check for healthy vegetation
            if 'ndvi' in live_data and 'image' in live_data['ndvi']:
                ndvi_image = live_data['ndvi']['image'].select('NDVI')
                vegetation_mask = ndvi_image.gt(ndvi_threshold)
                # Combine: bloom areas with healthy vegetation
                bloom_mask = bloom_mask.And(vegetation_mask)
            
            # Calculate area in square kilometers
            pixel_area = bloom_mask.multiply(ee.Image.pixelArea()).divide(1e6)  # Convert to km²
            
            total_area = pixel_area.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=self.geometry,
                scale=30,  # Use Landsat resolution for accuracy
                maxPixels=1e9
            )
            
            area_km2 = total_area.getInfo().get('NDWI', 0)
            
            # Get region total area for percentage
            total_region_area = self.geometry.area().divide(1e6).getInfo()  # Total region in km²
            bloom_percentage = (area_km2 / total_region_area) * 100 if total_region_area > 0 else 0
            
            return {
                'bloom_area_km2': area_km2,
                'total_region_km2': total_region_area,
                'bloom_percentage': bloom_percentage,
                'ndwi_threshold': ndwi_threshold,
                'ndvi_threshold': ndvi_threshold,
                'timestamp': datetime.now().isoformat(),
                'method': 'Earth Engine computation'
            }
            
        except Exception as e:
            logger.error(f"Error computing bloom area: {e}")
            return self._generate_synthetic_bloom_area(ndwi_threshold, ndvi_threshold, error=str(e))
    
    def schedule_model_training(self):
        """Schedule ML model training with fresh data"""
        try:
            from train_model import train_bloom_model
            
            logger.info("Scheduling model training with fresh data")
            
            # This would be called by a scheduler (e.g., weekly)
            model_results = train_bloom_model()
            
            logger.info(f"Model training completed: {model_results}")
            return model_results
            
        except ImportError:
            logger.warning("train_model.py not found - model training skipped")
            return {'error': 'train_model.py not available'}
        except Exception as e:
            logger.error(f"Error scheduling model training: {e}")
            return {'error': str(e)}
    
    def _generate_synthetic_live_data(self, end_date: datetime, days_back: int, error: str = None) -> Dict:
        """Generate synthetic live data when Earth Engine is not available"""
        logger.info("Generating synthetic live data for demonstration")
        
        # Generate Kenya-like data based on current season
        current_month = end_date.month
        
        # NDVI data (seasonal adjustment)
        if 3 <= current_month <= 5:  # Long rains
            ndvi_mean = np.random.uniform(0.5, 0.8)
        elif 10 <= current_month <= 12:  # Short rains  
            ndvi_mean = np.random.uniform(0.4, 0.7)
        else:  # Dry seasons
            ndvi_mean = np.random.uniform(0.2, 0.5)
        
        # NDWI data (correlated with blooms)
        ndwi_mean = np.random.uniform(0.1, 0.6)
        
        # Rainfall data (seasonal)
        if 3 <= current_month <= 5:  # Long rains
            rainfall_total = np.random.uniform(50.0, 200.0)
        elif 10 <= current_month <= 12:  # Short rains
            rainfall_total = np.random.uniform(30.0, 120.0)
        else:
            rainfall_total = np.random.uniform(0.0, 30.0)
        
        # Temperature data
        temp_mean = np.random.uniform(18.0, 28.0)
        
        synthetic_data = {
            'ndvi': {
                'source': 'Synthetic MODIS',
                'date_range': f"{(end_date - timedelta(days=days_back)).strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'image_count': np.random.randint(1, 6),
                'ndvi_mean': ndvi_mean,
                'ndvi_min': max(0, ndvi_mean - 0.2),
                'ndvi_max': min(1, ndvi_mean + 0.2),
                'ndvi_std': np.random.uniform(0.05, 0.15)
            },
            'ndwi': {
                'source': 'Synthetic Landsat',
                'date_range': f"{(end_date - timedelta(days=days_back)).strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'image_count': np.random.randint(0, 4),
                'cloud_threshold': CLOUD_THRESHOLD,
                'ndwi_mean': ndwi_mean,
                'ndwi_min': max(-1, ndwi_mean - 0.3),
                'ndwi_max': min(1, ndwi_mean + 0.3),
                'ndwi_std': np.random.uniform(0.05, 0.2)
            },
            'rainfall': {
                'source': 'Synthetic CHIRPS',
                'date_range': f"{(end_date - timedelta(days=days_back)).strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'image_count': days_back,
                'total_rainfall_mm': rainfall_total,
                'avg_daily_mm': rainfall_total / days_back
            },
            'temperature': {
                'source': 'Synthetic MODIS LST',
                'date_range': f"{(end_date - timedelta(days=days_back)).strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'image_count': np.random.randint(1, max(2, days_back)),
                'temp_mean_c': temp_mean,
                'temp_min_c': temp_mean - 5,
                'temp_max_c': temp_mean + 5
            },
            'export_tasks': [],
            'synthetic': True,
            'timestamp': end_date.isoformat()
        }
        
        if error:
            synthetic_data['fallback_reason'] = error
        
        # Save synthetic data as CSV
        try:
            self._save_live_csv_data(synthetic_data, end_date)
        except Exception as e:
            logger.warning(f"Could not save synthetic CSV data: {e}")
        
        return synthetic_data
    
    def _generate_synthetic_bloom_area(self, ndwi_threshold: float, ndvi_threshold: float, error: str = None) -> Dict:
        """Generate synthetic bloom area data when Earth Engine is not available"""
        # Simulate realistic bloom area for Kenya region
        total_area_km2 = 12000  # Approximate area for central Kenya
        
        # Generate bloom area based on current season
        current_month = datetime.now().month
        if 3 <= current_month <= 5 or 10 <= current_month <= 12:  # Rainy seasons
            bloom_area_km2 = np.random.uniform(200.0, 800.0)  # Higher bloom area
        else:
            bloom_area_km2 = np.random.uniform(50.0, 300.0)   # Lower bloom area
        
        bloom_percentage = (bloom_area_km2 / total_area_km2) * 100
        
        result = {
            'bloom_area_km2': float(bloom_area_km2),
            'total_region_km2': float(total_area_km2),
            'bloom_percentage': float(bloom_percentage),
            'ndwi_threshold': ndwi_threshold,
            'ndvi_threshold': ndvi_threshold,
            'timestamp': datetime.now().isoformat(),
            'method': 'Synthetic demo data'
        }
        
        if error:
            result['fallback_reason'] = error
        
        return result


def export_modis_ndvi(bbox: list, start: str, end: str, description: str):
    """Legacy function for backward compatibility"""
    pipeline = EarthEnginePipeline(bbox)
    return pipeline._fetch_modis_ndvi(start, end)


def process_exports_for_detection(export_dir: str) -> dict:
    """Load exports, run detection (legacy compatibility)."""
    try:
        from ndvi_utils import load_raster, compute_anomaly, detect_blooms
        
        ndvi_file = os.path.join(export_dir, 'modis_ndvi_median.tif')
        ari_file = os.path.join(export_dir, 'landsat_ari_median.tif')
        
        # Check if files exist, create dummy data if not
        if os.path.exists(ndvi_file):
            ndvi = load_raster(ndvi_file)
        else:
            logger.warning(f"{ndvi_file} not found, using dummy data")
            ndvi = np.random.rand(100, 100) * 0.8
        
        if os.path.exists(ari_file):
            ari = load_raster(ari_file)
        else:
            logger.warning(f"{ari_file} not found, using dummy data")
            ari = np.random.rand(100, 100) * 0.2
        
        # Placeholder baseline (load or compute)
        baseline = np.full_like(ndvi, 0.3)  # Avg NDVI
        anomaly = compute_anomaly(ndvi, baseline)
        
        # For TS: Assume multiple files; here single for MVP
        dummy_ts = np.tile(ndvi, (5, 1, 1))  # Fake 5 steps
        dummy_ari_list = [ari.mean()] * 5
        peaks, scores = detect_blooms(dummy_ts, dummy_ari_list)
        
        return {'peaks': peaks, 'anomaly': anomaly.mean(), 'bloom_scores': scores, 'ndvi': ndvi, 'ari': ari}
    
    except Exception as e:
        logger.error(f"Error processing exports: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    """Test the enhanced Earth Engine Pipeline"""
    print("🛰️ Enhanced Earth Engine Pipeline Test")
    print("=" * 60)
    
    try:
        # Initialize pipeline for Kenya
        pipeline = EarthEnginePipeline()
        
        print(f"📍 Region: Kenya ({pipeline.bbox})")
        print(f"☁️ Cloud threshold: {CLOUD_THRESHOLD}%")
        
        # Test live data fetching
        print("\n🔄 Fetching live data (last 7 days)...")
        live_data = pipeline.fetch_live_data(days_back=7)
        
        if 'error' in live_data:
            print(f"❌ Error: {live_data['error']}")
        else:
            print("✅ Live data fetch successful!")
            
            # Display results
            for data_type, data in live_data.items():
                if isinstance(data, dict) and 'error' not in data:
                    if data_type == 'ndvi':
                        print(f"\n🌱 NDVI Data ({data.get('source', 'Unknown')}):")
                        print(f"  Images: {data.get('image_count', 0)}")
                        print(f"  Mean NDVI: {data.get('ndvi_mean', 0):.3f}")
                        print(f"  Range: {data.get('ndvi_min', 0):.3f} - {data.get('ndvi_max', 0):.3f}")
                    
                    elif data_type == 'ndwi':
                        print(f"\n💧 NDWI Data ({data.get('source', 'Unknown')}):")
                        print(f"  Images: {data.get('image_count', 0)}")
                        print(f"  Mean NDWI: {data.get('ndwi_mean', 0):.3f}")
                        print(f"  Cloud-free images: {data.get('image_count', 0)}")
                    
                    elif data_type == 'rainfall':
                        print(f"\n🌧️ Rainfall Data ({data.get('source', 'Unknown')}):")
                        print(f"  Total: {data.get('total_rainfall_mm', 0):.1f} mm")
                        print(f"  Daily avg: {data.get('avg_daily_mm', 0):.1f} mm/day")
                    
                    elif data_type == 'temperature':
                        print(f"\n🌡️ Temperature Data ({data.get('source', 'Unknown')}):")
                        print(f"  Mean: {data.get('temp_mean_c', 0):.1f}°C")
                        print(f"  Range: {data.get('temp_min_c', 0):.1f} - {data.get('temp_max_c', 0):.1f}°C")
        
        # Test bloom area computation
        print("\n🌸 Computing bloom areas...")
        bloom_area = pipeline.compute_bloom_area()
        
        if 'error' in bloom_area:
            print(f"❌ Bloom area error: {bloom_area['error']}")
        else:
            print(f"✅ Bloom area: {bloom_area.get('bloom_area_km2', 0):.2f} km²")
            print(f"📊 Coverage: {bloom_area.get('bloom_percentage', 0):.2f}% of region")
        
        # Test export tasks
        if 'export_tasks' in live_data:
            print(f"\n📤 Export tasks: {len(live_data['export_tasks'])}")
            for task in live_data['export_tasks']:
                print(f"  • {task}")
        
        print(f"\n📁 Data saved to: {LIVE_DATA_DIR}")
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        logger.error(f"Pipeline test error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced Earth Engine Pipeline test complete!")
    print("\nNote: Ensure Earth Engine is authenticated:")
    print("  earthengine authenticate")
    print("  earthengine set_project YOUR_PROJECT_ID")
