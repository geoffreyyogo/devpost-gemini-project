"""
Kenya-wide Real Satellite Data Fetcher
Fetches and processes satellite data at country / region / county / sub-county
level and persists results to both JSON (legacy) and PostgreSQL.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, date as date_type, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from kenya_counties_config import KENYA_COUNTIES, KENYA_REGIONS, AGRICULTURAL_COUNTIES
from ee_pipeline import EarthEnginePipeline, initialize_earth_engine
from bloom_processor import BloomProcessor
from train_model_pytorch import BloomPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data directory (models only)
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

# Sub-county helpers (optional import — graceful if missing)
try:
    from kenya_sub_counties import (
        get_sub_counties,
        get_sub_county_info,
        get_sub_county_bbox,
        get_all_sub_county_ids,
        KENYA_SUB_COUNTIES,
    )
    SUB_COUNTIES_AVAILABLE = True
except ImportError:
    SUB_COUNTIES_AVAILABLE = False
    KENYA_SUB_COUNTIES = {}


class KenyaDataFetcher:
    """Fetch and process satellite data for Kenya at multiple granularities."""

    def __init__(self, db_service=None):
        """
        Args:
            db_service: Optional PostgresService for persisting to DB.
                        When None, data is saved to JSON files only.
        """
        self.ee_available = initialize_earth_engine()
        self.processor = BloomProcessor(db_service=db_service)
        self.predictor = BloomPredictor()
        self.db = db_service

        # Load existing ML model if available
        self.predictor.load_model()

        logger.info(
            f"Kenya Data Fetcher initialized "
            f"(EE={self.ee_available}, PG={'yes' if db_service else 'no'}, "
            f"Sub-counties={'yes' if SUB_COUNTIES_AVAILABLE else 'no'})"
        )
    
    def fetch_county_data(self, county_id: str, days_back: int = 7) -> Dict:
        """
        Fetch satellite data for a specific county.

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

            # Make bloom prediction using county-specific live_data
            prediction = self.predictor.predict_bloom_probability(live_data)

            # Extract soil data from live_data
            soil = live_data.get('soil', {})

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
                    'is_real_data': 'synthetic' not in live_data,
                    # Soil properties
                    'soil_type': soil.get('soil_type'),
                    'soil_moisture_pct': soil.get('soil_moisture_pct'),
                    'soil_organic_carbon': soil.get('soil_organic_carbon'),
                    'soil_ph': soil.get('soil_ph'),
                    'soil_clay_pct': soil.get('soil_clay_pct'),
                    'soil_sand_pct': soil.get('soil_sand_pct'),
                },
                'bloom_data': {
                    'bloom_area_km2': bloom_area.get('bloom_area_km2', 0),
                    'bloom_percentage': bloom_area.get('bloom_percentage', 0),
                    'bloom_probability': prediction.get('bloom_probability_percent', prediction.get('bloom_probability', 0)),
                    'bloom_prediction': prediction.get('bloom_prediction', prediction.get('prediction', 'Unknown')),
                    'confidence': prediction.get('confidence', 'Low'),
                    'message': prediction.get('message', 'N/A')
                }
            }

            # Persist to PostgreSQL (single source of truth)
            self._persist_to_pg(
                county=county_info['name'],
                region=county_info['region'],
                sub_county=None,
                satellite=county_data['satellite_data'],
                bloom=county_data['bloom_data'],
                main_crops=county_info['main_crops'],
                center_lat=county_info['coordinates']['lat'],
                center_lon=county_info['coordinates']['lon'],
            )

            return county_data

        except Exception as e:
            logger.error(f"Error fetching data for {county_id}: {e}")
            return {
                'error': str(e),
                'county_id': county_id,
                'county_name': county_info['name']
            }

    # ------------------------------------------------------------------ #
    # Sub-county level fetch
    # ------------------------------------------------------------------ #

    def fetch_sub_county_data(
        self, county_id: str, sub_county_id: str, days_back: int = 7
    ) -> Dict:
        """
        Fetch satellite data for a specific sub-county.

        Args:
            county_id: County identifier (e.g., 'kiambu')
            sub_county_id: Sub-county key from kenya_sub_counties.py
            days_back: Days of historical data to fetch

        Returns:
            Dict with sub-county satellite data and predictions
        """
        if not SUB_COUNTIES_AVAILABLE:
            return {'error': 'Sub-county data not available'}

        county_info = KENYA_COUNTIES.get(county_id)
        if not county_info:
            return {'error': f'County not found: {county_id}'}

        sc_info = get_sub_county_info(county_id, sub_county_id)
        if not sc_info:
            return {'error': f'Sub-county not found: {sub_county_id} in {county_id}'}

        sc_bbox = get_sub_county_bbox(county_id, sub_county_id)
        if not sc_bbox:
            return {'error': f'No bbox for sub-county: {sub_county_id}'}

        logger.info(
            f"Fetching data for sub-county {sc_info['name']} "
            f"({county_info['name']} County)"
        )

        try:
            pipeline = EarthEnginePipeline(region_bbox=sc_bbox)
            live_data = pipeline.fetch_live_data(days_back=days_back)
            bloom_area = pipeline.compute_bloom_area()
            prediction = self.predictor.predict_bloom_probability(live_data)

            sc_data = {
                'county_id': county_id,
                'county_name': county_info['name'],
                'sub_county_id': sub_county_id,
                'sub_county_name': sc_info['name'],
                'region': county_info['region'],
                'coordinates': sc_info['coordinates'],
                'main_crops': county_info['main_crops'],
                'last_updated': datetime.now().isoformat(),
                'satellite_data': {
                    'ndvi': live_data.get('ndvi', {}).get('ndvi_mean', 0),
                    'ndwi': live_data.get('ndwi', {}).get('ndwi_mean', 0),
                    'rainfall_mm': live_data.get('rainfall', {}).get('total_rainfall_mm', 0),
                    'temperature_c': live_data.get('temperature', {}).get('temp_mean_c', 0),
                    'data_source': live_data.get('ndvi', {}).get('source', 'Unknown'),
                    'is_real_data': 'synthetic' not in live_data,
                },
                'bloom_data': {
                    'bloom_area_km2': bloom_area.get('bloom_area_km2', 0),
                    'bloom_percentage': bloom_area.get('bloom_percentage', 0),
                    'bloom_probability': prediction.get(
                        'bloom_probability_percent',
                        prediction.get('bloom_probability', 0),
                    ),
                    'bloom_prediction': prediction.get(
                        'bloom_prediction',
                        prediction.get('prediction', 'Unknown'),
                    ),
                    'confidence': prediction.get('confidence', 'Low'),
                    'message': prediction.get('message', 'N/A'),
                },
            }

            # Persist to PostgreSQL
            self._persist_to_pg(
                county=county_info['name'],
                region=county_info['region'],
                sub_county=sc_info['name'],
                satellite=sc_data['satellite_data'],
                bloom=sc_data['bloom_data'],
                main_crops=county_info['main_crops'],
                center_lat=sc_info['coordinates']['lat'],
                center_lon=sc_info['coordinates']['lon'],
            )

            return sc_data

        except Exception as e:
            logger.error(
                f"Error fetching sub-county {sub_county_id} in {county_id}: {e}"
            )
            return {'error': str(e), 'sub_county_id': sub_county_id}

    def fetch_county_with_sub_counties(
        self, county_id: str, days_back: int = 7
    ) -> Dict:
        """
        Fetch data for a county AND all its sub-counties.

        Returns:
            Dict with 'county' (county-level data) and 'sub_counties' dict.
        """
        county_data = self.fetch_county_data(county_id, days_back)
        result = {'county': county_data, 'sub_counties': {}}

        if SUB_COUNTIES_AVAILABLE:
            sc_ids = get_all_sub_county_ids(county_id)
            for sc_id in sc_ids:
                sc_data = self.fetch_sub_county_data(county_id, sc_id, days_back)
                result['sub_counties'][sc_id] = sc_data
                logger.info(
                    f"  Sub-county {sc_id}: done "
                    f"({'error' not in sc_data and 'OK' or 'FAIL'})"
                )

        return result
    
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
            
            # Save progress periodically (logged only)
            if idx % 10 == 0:
                logger.info(f"Progress: {idx}/{total} counties persisted to PG")
        
        # Generate map data in PG
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
        """Save individual county data to PostgreSQL (legacy compat wrapper)."""
        # Data is persisted via _persist_to_pg() — this is now a no-op
        logger.debug(f"County data for {county_id} persisted via PG")

    def _save_all_counties_data(self, counties_data: Dict):
        """All data is saved via _persist_to_pg() during fetch — no-op."""
        logger.debug(f"All counties data persisted to PG ({len(counties_data)} counties)")
    
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
                        'bloom_percentage': data['bloom_data']['bloom_percentage'],
                        'bloom_area_km2': data['bloom_data']['bloom_area_km2'],
                        'bloom_prediction': data['bloom_data']['bloom_prediction'],
                        'message': data['bloom_data']['message'],
                        'ndvi': data['satellite_data']['ndvi'],
                        'temperature_c': data['satellite_data']['temperature_c'],
                        'rainfall_mm': data['satellite_data']['rainfall_mm'],
                        'confidence': data['bloom_data']['confidence'],
                        'is_real_data': data['satellite_data']['is_real_data']
                    })
            
            # Map data is derived from PG on-the-fly via db_service.get_map_data()
            logger.info(f"Generated map data with {len(map_data['counties'])} counties (in-memory)")
            
        except Exception as e:
            logger.error(f"Error generating map data: {e}")

    # ------------------------------------------------------------------ #
    # PostgreSQL persistence
    # ------------------------------------------------------------------ #

    def _persist_to_pg(
        self,
        county: str,
        region: str,
        sub_county: Optional[str],
        satellite: Dict,
        bloom: Dict,
        main_crops: List[str],
        center_lat: float,
        center_lon: float,
    ):
        """Save fetched data to PostgreSQL via db_service.save_county_data."""
        if not self.db:
            return
        try:
            obs_date = date_type.today()
            # Clamp bloom_probability to [0, 1] range
            raw_bp = bloom.get('bloom_probability', 0) or 0
            clamped_bp = max(0.0, min(1.0, float(raw_bp)))

            data = {
                'region': region,
                'ndvi': satellite.get('ndvi'),
                'ndwi': satellite.get('ndwi'),
                'rainfall_mm': satellite.get('rainfall_mm'),
                'temperature_mean_c': satellite.get('temperature_c'),
                'bloom_area_km2': bloom.get('bloom_area_km2'),
                'bloom_percentage': bloom.get('bloom_percentage'),
                'bloom_probability': clamped_bp,
                'bloom_prediction': bloom.get('bloom_prediction'),
                'bloom_confidence': bloom.get('confidence'),
                'center_lat': center_lat,
                'center_lon': center_lon,
                'main_crops': main_crops,
                'data_source': satellite.get('data_source', 'Unknown'),
                # Soil data
                'soil_type': satellite.get('soil_type'),
                'soil_moisture_pct': satellite.get('soil_moisture_pct'),
                'soil_organic_carbon': satellite.get('soil_organic_carbon'),
                'soil_ph': satellite.get('soil_ph'),
                'soil_clay_pct': satellite.get('soil_clay_pct'),
                'soil_sand_pct': satellite.get('soil_sand_pct'),
            }
            self.db.save_county_data(
                county=county,
                obs_date=obs_date,
                data=data,
                sub_county=sub_county,
            )
            scope_label = f"{county}/{sub_county}" if sub_county else county
            logger.debug(f"Persisted to PG: {scope_label} ({obs_date})")
        except Exception as e:
            logger.error(f"Error persisting to PG: {e}")
    
    def load_county_data(self, county_id: str) -> Dict:
        """Load county data from PostgreSQL."""
        try:
            if self.db:
                data = self.db.get_county_data(county_id)
                if data:
                    return data
        except Exception as e:
            logger.error(f"Error loading county data from PG: {e}")
        return {}
    
    def load_all_counties_data(self) -> Dict:
        """Load all counties data from PostgreSQL."""
        try:
            if self.db:
                rows = self.db.get_all_counties_latest()
                if rows:
                    result = {}
                    for row in rows:
                        cid = row.get('county', '').lower().replace(' ', '_').replace('-', '_').replace("'", '')
                        result[cid] = row
                    return result
        except Exception as e:
            logger.error(f"Error loading all counties data from PG: {e}")
        return {}
    
    def load_map_data(self) -> Dict:
        """Load map-ready data from PostgreSQL."""
        try:
            if self.db:
                return self.db.get_map_data()
        except Exception as e:
            logger.error(f"Error loading map data from PG: {e}")
        return {'counties': [], 'last_updated': None}
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics for all county data from PostgreSQL."""
        all_data = self.load_all_counties_data()
        
        if not all_data:
            return {'error': 'No data available'}
        
        total_counties = len(all_data)
        counties_with_real_data = sum(
            1 for d in all_data.values()
            if d.get('is_real_data', False)
        )
        
        bloom_probs = [
            d.get('bloom_probability', 0) or d.get('bloom_data', {}).get('bloom_probability', 0)
            for d in all_data.values()
        ]
        avg_bloom_prob = float(np.mean(bloom_probs)) if bloom_probs else 0.0
        
        total_bloom_area = sum(
            d.get('bloom_area_km2', 0) or d.get('bloom_data', {}).get('bloom_area_km2', 0)
            for d in all_data.values()
        )
        
        return {
            'total_counties': total_counties,
            'counties_with_real_data': counties_with_real_data,
            'real_data_percentage': (counties_with_real_data / total_counties * 100) if total_counties > 0 else 0,
            'avg_bloom_probability': avg_bloom_prob,
            'total_bloom_area_km2': total_bloom_area,
            'last_updated': all_data[list(all_data.keys())[0]].get('observation_date') if all_data else None
        }


# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch satellite data for Kenya counties')
    parser.add_argument('--county', type=str, help='Fetch data for specific county')
    parser.add_argument('--sub-county', type=str, dest='sub_county',
                        help='Fetch data for a sub-county (requires --county)')
    parser.add_argument('--region', type=str, help='Fetch data for specific region')
    parser.add_argument('--all', action='store_true', help='Fetch data for all counties')
    parser.add_argument('--with-sub-counties', action='store_true', dest='with_subs',
                        help='Also fetch sub-county data (use with --county or --all)')
    parser.add_argument('--summary', action='store_true', help='Show data summary')
    parser.add_argument('--pg', action='store_true',
                        help='Persist to PostgreSQL (requires running DB)')
    
    args = parser.parse_args()

    # Optionally connect to PG
    _db = None
    if args.pg:
        try:
            from database.postgres_service import PostgresService
            _db = PostgresService()
            print("✓ PostgreSQL connected")
        except Exception as exc:
            print(f"⚠ PostgreSQL not available: {exc}")

    fetcher = KenyaDataFetcher(db_service=_db)
    
    if args.summary:
        print("\n" + "="*60)
        print("KENYA COUNTIES DATA SUMMARY")
        print("="*60)
        summary = fetcher.get_data_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("="*60)
    
    elif args.county and args.sub_county:
        print(f"\nFetching sub-county {args.sub_county} in {args.county}...")
        data = fetcher.fetch_sub_county_data(args.county, args.sub_county)
        print(json.dumps(data, indent=2))

    elif args.county and args.with_subs:
        print(f"\nFetching {args.county} with all sub-counties...")
        data = fetcher.fetch_county_with_sub_counties(args.county)
        print(f"County data + {len(data.get('sub_counties', {}))} sub-counties")

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
        
        summary = fetcher.get_data_summary()
        print("\nSUMMARY:")
        print(f"  Real satellite data: {summary['counties_with_real_data']}/{summary['total_counties']} counties")
        print(f"  Avg bloom probability: {summary['avg_bloom_probability']:.1f}%")
        print(f"  Total bloom area: {summary['total_bloom_area_km2']:.2f} km²")
    
    else:
        print("Usage:")
        print("  python kenya_data_fetcher.py --all                            # All counties")
        print("  python kenya_data_fetcher.py --county kiambu                  # Single county")
        print("  python kenya_data_fetcher.py --county kiambu --with-sub-counties  # County + sub-counties")
        print("  python kenya_data_fetcher.py --county kiambu --sub-county limuru  # Single sub-county")
        print("  python kenya_data_fetcher.py --region central                 # Region")
        print("  python kenya_data_fetcher.py --summary                        # Summary")
        print("  python kenya_data_fetcher.py --all --pg                       # All + save to PostgreSQL")

