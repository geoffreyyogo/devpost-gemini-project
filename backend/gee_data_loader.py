"""
GEE Data Loader for BloomWatch Kenya
Loads exported GeoTIFF files from Google Earth Engine
"""

import os
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import rasterio for reading GeoTIFF files
try:
    import rasterio
    from rasterio.plot import show
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    logger.warning("rasterio not available - using fallback data loader")

class GEEDataLoader:
    """Load and process GEE exported data"""
    
    def __init__(self, export_dir: str = None):
        """Initialize data loader"""
        if export_dir is None:
            # Try multiple possible export directories
            possible_dirs = [
                '../data/exports',
                './data/exports',
                '/home/yogo/bloom-detector/data/exports',
                os.path.join(os.path.dirname(__file__), '..', 'data', 'exports')
            ]
            for d in possible_dirs:
                if os.path.exists(d):
                    export_dir = d
                    break
            
            if export_dir is None:
                export_dir = '../data/exports'
                os.makedirs(export_dir, exist_ok=True)
        
        self.export_dir = export_dir
        logger.info(f"GEE Data Loader initialized: {self.export_dir}")
    
    def load_geotiff(self, filename: str) -> Optional[np.ndarray]:
        """Load a GeoTIFF file"""
        filepath = os.path.join(self.export_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return None
        
        if RASTERIO_AVAILABLE:
            try:
                with rasterio.open(filepath) as src:
                    data = src.read(1)  # Read first band
                    logger.info(f"Loaded GeoTIFF: {filename}, shape: {data.shape}")
                    return data
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
                return None
        else:
            # Fallback: try to load as numpy array if it was saved as .npy
            npy_path = filepath.replace('.tif', '.npy')
            if os.path.exists(npy_path):
                try:
                    data = np.load(npy_path)
                    logger.info(f"Loaded numpy array: {npy_path}, shape: {data.shape}")
                    return data
                except Exception as e:
                    logger.error(f"Error loading {npy_path}: {e}")
                    return None
            
            logger.warning(f"Cannot load {filename} - rasterio not available and no .npy fallback")
            return None
    
    def get_available_exports(self) -> Dict[str, list]:
        """List all available GEE exports"""
        available = {
            'sentinel2_ndvi': [],
            'landsat_ndvi': [],
            'landsat_ari': [],
            'modis_ndvi': [],
            'viirs_ndvi': []
        }
        
        if not os.path.exists(self.export_dir):
            logger.warning(f"Export directory not found: {self.export_dir}")
            return available
        
        # Scan for exported files
        patterns = {
            'sentinel2_ndvi': ['*sentinel*ndvi*.tif', '*s2*ndvi*.tif'],
            'landsat_ndvi': ['*landsat*ndvi*.tif', '*l8*ndvi*.tif', '*l9*ndvi*.tif'],
            'landsat_ari': ['*landsat*ari*.tif', '*l8*ari*.tif', '*l9*ari*.tif'],
            'modis_ndvi': ['*modis*ndvi*.tif', '*mod13*.tif'],
            'viirs_ndvi': ['*viirs*ndvi*.tif', '*vnp13*.tif']
        }
        
        for data_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                files = glob.glob(os.path.join(self.export_dir, pattern))
                available[data_type].extend([os.path.basename(f) for f in files])
        
        # Also check for .npy files (our fallback format)
        for data_type in available.keys():
            npy_files = glob.glob(os.path.join(self.export_dir, f'*{data_type}*.npy'))
            available[data_type].extend([os.path.basename(f) for f in npy_files])
        
        logger.info(f"Available exports: {available}")
        return available
    
    def load_kenya_data(self) -> Dict[str, np.ndarray]:
        """Load Kenya-specific exported data"""
        data = {}
        
        # Try to load NDVI data (prefer Sentinel-2 for Kenya)
        available = self.get_available_exports()
        
        # Load Sentinel-2 NDVI (best for Kenya - 10m resolution)
        if available['sentinel2_ndvi']:
            ndvi = self.load_geotiff(available['sentinel2_ndvi'][0])
            if ndvi is not None:
                data['ndvi'] = ndvi
                data['source'] = 'Sentinel-2'
                logger.info("Using Sentinel-2 NDVI data")
        
        # Fallback to Landsat NDVI
        if 'ndvi' not in data and available['landsat_ndvi']:
            ndvi = self.load_geotiff(available['landsat_ndvi'][0])
            if ndvi is not None:
                data['ndvi'] = ndvi
                data['source'] = 'Landsat'
                logger.info("Using Landsat NDVI data")
        
        # Fallback to MODIS NDVI
        if 'ndvi' not in data and available['modis_ndvi']:
            ndvi = self.load_geotiff(available['modis_ndvi'][0])
            if ndvi is not None:
                data['ndvi'] = ndvi
                data['source'] = 'MODIS'
                logger.info("Using MODIS NDVI data")
        
        # Load ARI data (for flower detection)
        if available['landsat_ari']:
            ari = self.load_geotiff(available['landsat_ari'][0])
            if ari is not None:
                data['ari'] = ari
                logger.info("Loaded Landsat ARI data")
        
        # If no data loaded, generate synthetic Kenya data
        if 'ndvi' not in data:
            logger.warning("No GEE exports found - generating synthetic Kenya data")
            data = self._generate_synthetic_kenya_data()
        
        return data
    
    def _generate_synthetic_kenya_data(self) -> Dict[str, np.ndarray]:
        """Generate realistic synthetic data for Kenya when no exports available"""
        logger.info("Generating synthetic Kenya agricultural data")
        
        # Generate Kenya-like NDVI patterns (account for seasons)
        current_month = datetime.now().month
        
        # Base NDVI
        ndvi = np.random.rand(100, 100) * 0.6 + 0.2  # 0.2 to 0.8
        
        # Seasonal adjustment
        if 3 <= current_month <= 5:  # Long rains (March-May)
            ndvi *= 1.4  # Higher vegetation
        elif 10 <= current_month <= 12:  # Short rains (Oct-Dec)
            ndvi *= 1.2
        else:  # Dry seasons
            ndvi *= 0.8
        
        # Add spatial patterns (simulate agricultural fields)
        for i in range(0, 100, 20):
            for j in range(0, 100, 20):
                # Create field-like patterns
                field_boost = np.random.uniform(0.9, 1.1)
                ndvi[i:i+18, j:j+18] *= field_boost
        
        # Generate ARI data (flower pigments)
        ari = np.random.rand(100, 100) * 0.25
        
        # Add bloom hotspots
        for _ in range(5):
            x, y = np.random.randint(10, 90), np.random.randint(10, 90)
            ari[x:x+8, y:y+8] += 0.15
        
        # Generate time series (12 months)
        time_series = []
        for month in range(12):
            monthly_ndvi = np.random.rand(100, 100) * 0.6 + 0.2
            
            # Long rains boost
            if 2 <= month <= 4:  # March-May (0-indexed)
                monthly_ndvi *= 1.4
            # Short rains boost
            elif 9 <= month <= 11:  # Oct-Dec
                monthly_ndvi *= 1.2
            
            time_series.append(monthly_ndvi)
        
        return {
            'ndvi': ndvi,
            'ari': ari,
            'time_series': np.array(time_series),
            'source': 'Synthetic (Demo)',
            'generated_at': datetime.now().isoformat()
        }
    
    def load_time_series(self, data_type: str = 'ndvi', num_months: int = 12) -> Optional[np.ndarray]:
        """Load time series data if available"""
        available = self.get_available_exports()
        
        files = available.get(f'modis_{data_type}', []) or available.get(f'landsat_{data_type}', [])
        
        if not files:
            logger.warning(f"No time series data found for {data_type}")
            return None
        
        # Load multiple files if available
        time_series = []
        for filename in sorted(files)[:num_months]:
            data = self.load_geotiff(filename)
            if data is not None:
                time_series.append(data)
        
        if time_series:
            return np.array(time_series)
        
        return None
    
    def get_data_info(self) -> Dict:
        """Get information about available data"""
        available = self.get_available_exports()
        
        info = {
            'export_directory': self.export_dir,
            'has_sentinel2': len(available['sentinel2_ndvi']) > 0,
            'has_landsat': len(available['landsat_ndvi']) > 0,
            'has_modis': len(available['modis_ndvi']) > 0,
            'has_ari': len(available['landsat_ari']) > 0,
            'total_files': sum(len(files) for files in available.values()),
            'available_data': available
        }
        
        return info

# Testing
if __name__ == "__main__":
    print("🛰️ GEE Data Loader Test")
    print("=" * 60)
    
    loader = GEEDataLoader()
    
    # Check available data
    info = loader.get_data_info()
    print(f"\n📁 Export Directory: {info['export_directory']}")
    print(f"📊 Total Files: {info['total_files']}")
    print(f"✓ Sentinel-2: {info['has_sentinel2']}")
    print(f"✓ Landsat: {info['has_landsat']}")
    print(f"✓ MODIS: {info['has_modis']}")
    print(f"✓ ARI Data: {info['has_ari']}")
    
    # Load Kenya data
    print("\n🌾 Loading Kenya Data...")
    kenya_data = loader.load_kenya_data()
    
    print(f"\n✓ Data Source: {kenya_data.get('source', 'Unknown')}")
    print(f"✓ NDVI Shape: {kenya_data['ndvi'].shape}")
    print(f"✓ NDVI Range: {kenya_data['ndvi'].min():.3f} - {kenya_data['ndvi'].max():.3f}")
    
    if 'ari' in kenya_data:
        print(f"✓ ARI Shape: {kenya_data['ari'].shape}")
        print(f"✓ ARI Range: {kenya_data['ari'].min():.3f} - {kenya_data['ari'].max():.3f}")
    
    if 'time_series' in kenya_data:
        print(f"✓ Time Series Shape: {kenya_data['time_series'].shape}")
    
    print("\n" + "=" * 60)
    print("🎉 GEE Data Loader test complete!")
    
    if kenya_data.get('source') == 'Synthetic (Demo)':
        print("\n⚠️  Note: Using synthetic data")
        print("To use real GEE data:")
        print("1. Run gee/gee_bloom_detector.js in GEE Code Editor")
        print("2. Export data to Google Drive")
        print("3. Download to data/exports/")


