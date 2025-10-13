"""
Kenya-wide Real Satellite Data Fetcher
Automatically fetches and processes satellite data for all 47 counties
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from kenya_counties_config import KENYA_COUNTIES, KENYA_REGIONS, AGRICULTURAL_COUNTIES
from ee_pipeline import EarthEnginePipeline, initialize_earth_engine
from bloom_processor import BloomProcessor
from train_model import BloomPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data directories
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
COUNTY_DATA_DIR = os.path.join(DATA_DIR, 'county_data')
LIVE_MAP_DATA = os.path.join(DATA_DIR, 'live_map_data.json')

# Create directories
os.makedirs(COUNTY_DATA_DIR, exist_ok=True)


class KenyaDataFetcher:
    """Fetch and process satellite data for all Kenya counties"""
    
    def __init__(self):
        """Initialize the fetcher"""
        self.ee_available = initialize_earth_engine()
        self.processor = BloomProcessor()
        self.predictor = BloomPredictor()
        
        # Load existing model if available
        self.predictor.load_model()
        
        logger.info(f"Kenya Data Fetcher initialized (EE Available: {self.ee_available})")
    
    def fetch_county_data(self, county_id: str, days_back: int = 7) -> Dict:
        """
        Fetch satellite data for a specific county
        
        Args:
            county_id: County identifier (e.g., 'kiambu')
            days_back: Days of historical data to fetch
        
        Returns:
            Dict with county satellite data and predictions
        """
        county_info = KENYA_COUNTIES.get(county_id)
        
        if not county_info:
            logger.error(f"County not found: {county_id}")
            return {'error': f'County not found: {county_id}'}
        
        logger.info(f"Fetching data for {county_info['name']} County")
        
        try:
            # Initialize pipeline for this county's bounding box
            pipeline = EarthEnginePipeline(region_bbox=county_info['bbox'])
            
            # Fetch live satellite data
            live_data = pipeline.fetch_live_data(days_back=days_back)
            
            # Compute bloom areas
            bloom_area = pipeline.compute_bloom_area()
            
            # Make bloom prediction (predictor fetches its own live data)
            prediction = self.predictor.predict_bloom_probability()
            
            # Combine all data
            county_data = {
                'county_id': county_id,
                'county_name': county_info['name'],
                'region': county_info['region'],
                'coordinates': county_info['coordinates'],
                'main_crops': county_info['main_crops'],
                'last_updated': datetime.now().isoformat(),
                'satellite_data': {
                    'ndvi': live_data.get('ndvi', {}).get('ndvi_mean', 0),
                    'ndwi': live_data.get('ndwi', {}).get('ndwi_mean', 0),
                    'rainfall_mm': live_data.get('rainfall', {}).get('total_rainfall_mm', 0),
                    'temperature_c': live_data.get('temperature', {}).get('temp_mean_c', 0),
                    'data_source': live_data.get('ndvi', {}).get('source', 'Unknown'),
                    'is_real_data': 'synthetic' not in live_data
                },
                'bloom_data': {
                    'bloom_area_km2': bloom_area.get('bloom_area_km2', 0),
                    'bloom_percentage': bloom_area.get('bloom_percentage', 0),
                    'bloom_probability': prediction.get('bloom_probability', 0),
                    'bloom_prediction': prediction.get('prediction', 'Unknown'),
                    'confidence': prediction.get('confidence', 'Low'),
                    'message': prediction.get('message', 'N/A')
                }
            }
            
            # Save county data
            self._save_county_data(county_id, county_data)
            
            return county_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {county_id}: {e}")
            return {
                'error': str(e),
                'county_id': county_id,
                'county_name': county_info['name']
            }
    
    def fetch_all_counties_data(self, priority_agricultural: bool = True) -> Dict[str, Dict]:
        """
        Fetch data for all Kenya counties
        
        Args:
            priority_agricultural: Fetch agricultural counties first
        
        Returns:
            Dict mapping county_id to county data
        """
        logger.info("Starting county-wide data fetch")
        
        counties_data = {}
        
        # Get list of counties to fetch
        if priority_agricultural:
            counties_list = AGRICULTURAL_COUNTIES + [
                c for c in KENYA_COUNTIES.keys() if c not in AGRICULTURAL_COUNTIES
            ]
        else:
            counties_list = list(KENYA_COUNTIES.keys())
        
        # Fetch data for each county
        total = len(counties_list)
        for idx, county_id in enumerate(counties_list, 1):
            logger.info(f"Fetching {idx}/{total}: {KENYA_COUNTIES[county_id]['name']}")
            
            county_data = self.fetch_county_data(county_id)
            counties_data[county_id] = county_data
            
            # Save progress periodically
            if idx % 10 == 0:
                self._save_all_counties_data(counties_data)
        
        # Final save
        self._save_all_counties_data(counties_data)
        
        # Generate map data
        self._generate_map_data(counties_data)
        
        logger.info(f"Completed fetch for {total} counties")
        
        return counties_data
    
    def fetch_region_data(self, region: str) -> Dict[str, Dict]:
        """
        Fetch data for all counties in a region
        
        Args:
            region: Region identifier (e.g., 'central', 'rift_valley')
        
        Returns:
            Dict mapping county_id to county data for the region
        """
        region_info = KENYA_REGIONS.get(region)
        
        if not region_info:
            logger.error(f"Region not found: {region}")
            return {}
        
        logger.info(f"Fetching data for {region_info['name']} region")
        
        counties_data = {}
        county_ids = region_info['counties']
        
        for county_id in county_ids:
            county_data = self.fetch_county_data(county_id)
            counties_data[county_id] = county_data
        
        return counties_data
    
    def _save_county_data(self, county_id: str, data: Dict):
        """Save individual county data to file"""
        try:
            filename = os.path.join(COUNTY_DATA_DIR, f"{county_id}.json")
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved data for {county_id}")
        except Exception as e:
            logger.error(f"Error saving county data: {e}")
    
    def _save_all_counties_data(self, counties_data: Dict):
        """Save aggregated county data"""
        try:
            filename = os.path.join(DATA_DIR, 'all_counties_data.json')
            with open(filename, 'w') as f:
                json.dump(counties_data, f, indent=2)
            logger.info(f"Saved aggregated data for {len(counties_data)} counties")
        except Exception as e:
            logger.error(f"Error saving aggregated data: {e}")
    
    def _generate_map_data(self, counties_data: Dict):
        """Generate map-ready data for Streamlit"""
        try:
            map_data = {
                'last_updated': datetime.now().isoformat(),
                'counties': []
            }
            
            for county_id, data in counties_data.items():
                if 'error' not in data:
                    map_data['counties'].append({
                        'county_id': county_id,
                        'county_name': data['county_name'],
                        'lat': data['coordinates']['lat'],
                        'lon': data['coordinates']['lon'],
                        'bloom_probability': data['bloom_data']['bloom_probability'],
                        'bloom_area_km2': data['bloom_data']['bloom_area_km2'],
                        'ndvi': data['satellite_data']['ndvi'],
                        'temperature_c': data['satellite_data']['temperature_c'],
                        'rainfall_mm': data['satellite_data']['rainfall_mm'],
                        'confidence': data['bloom_data']['confidence'],
                        'is_real_data': data['satellite_data']['is_real_data']
                    })
            
            with open(LIVE_MAP_DATA, 'w') as f:
                json.dump(map_data, f, indent=2)
            
            logger.info(f"Generated map data with {len(map_data['counties'])} counties")
            
        except Exception as e:
            logger.error(f"Error generating map data: {e}")
    
    def load_county_data(self, county_id: str) -> Dict:
        """Load saved county data"""
        try:
            filename = os.path.join(COUNTY_DATA_DIR, f"{county_id}.json")
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading county data: {e}")
        return {}
    
    def load_all_counties_data(self) -> Dict:
        """Load all saved counties data"""
        try:
            filename = os.path.join(DATA_DIR, 'all_counties_data.json')
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading all counties data: {e}")
        return {}
    
    def load_map_data(self) -> Dict:
        """Load map-ready data for Streamlit"""
        try:
            if os.path.exists(LIVE_MAP_DATA):
                with open(LIVE_MAP_DATA, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading map data: {e}")
        return {'counties': [], 'last_updated': None}
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics for all county data"""
        all_data = self.load_all_counties_data()
        
        if not all_data:
            return {'error': 'No data available'}
        
        total_counties = len(all_data)
        counties_with_real_data = sum(
            1 for d in all_data.values() 
            if 'satellite_data' in d and d['satellite_data'].get('is_real_data', False)
        )
        
        avg_bloom_prob = np.mean([
            d['bloom_data']['bloom_probability'] 
            for d in all_data.values() 
            if 'bloom_data' in d
        ])
        
        total_bloom_area = sum([
            d['bloom_data']['bloom_area_km2'] 
            for d in all_data.values() 
            if 'bloom_data' in d
        ])
        
        return {
            'total_counties': total_counties,
            'counties_with_real_data': counties_with_real_data,
            'real_data_percentage': (counties_with_real_data / total_counties * 100) if total_counties > 0 else 0,
            'avg_bloom_probability': avg_bloom_prob,
            'total_bloom_area_km2': total_bloom_area,
            'last_updated': all_data[list(all_data.keys())[0]].get('last_updated') if all_data else None
        }


# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch satellite data for Kenya counties')
    parser.add_argument('--county', type=str, help='Fetch data for specific county')
    parser.add_argument('--region', type=str, help='Fetch data for specific region')
    parser.add_argument('--all', action='store_true', help='Fetch data for all counties')
    parser.add_argument('--summary', action='store_true', help='Show data summary')
    
    args = parser.parse_args()
    
    fetcher = KenyaDataFetcher()
    
    if args.summary:
        print("\n" + "="*60)
        print("KENYA COUNTIES DATA SUMMARY")
        print("="*60)
        summary = fetcher.get_data_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("="*60)
    
    elif args.county:
        print(f"\nFetching data for {args.county}...")
        data = fetcher.fetch_county_data(args.county)
        print(json.dumps(data, indent=2))
    
    elif args.region:
        print(f"\nFetching data for {args.region} region...")
        data = fetcher.fetch_region_data(args.region)
        print(f"Fetched data for {len(data)} counties")
    
    elif args.all:
        print("\nFetching data for ALL 47 counties...")
        print("This may take 15-30 minutes depending on internet connection")
        data = fetcher.fetch_all_counties_data()
        print(f"\n✅ Completed! Fetched data for {len(data)} counties")
        
        # Show summary
        summary = fetcher.get_data_summary()
        print("\nSUMMARY:")
        print(f"  Real satellite data: {summary['counties_with_real_data']}/{summary['total_counties']} counties")
        print(f"  Avg bloom probability: {summary['avg_bloom_probability']:.1f}%")
        print(f"  Total bloom area: {summary['total_bloom_area_km2']:.2f} km²")
    
    else:
        print("Usage:")
        print("  python kenya_data_fetcher.py --all           # Fetch all counties")
        print("  python kenya_data_fetcher.py --county kiambu # Fetch specific county")
        print("  python kenya_data_fetcher.py --region central# Fetch region")
        print("  python kenya_data_fetcher.py --summary       # Show summary")

