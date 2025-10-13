"""
Streamlit Data Loader
Provides real satellite data to Streamlit app
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from kenya_counties_config import KENYA_COUNTIES, KENYA_REGIONS
from kenya_data_fetcher import KenyaDataFetcher


class StreamlitDataLoader:
    """Load and format data for Streamlit visualizations"""
    
    def __init__(self):
        """Initialize the loader"""
        self.fetcher = KenyaDataFetcher()
    
    def get_landing_page_map_data(self) -> Dict:
        """
        Get formatted data for the landing page interactive map
        
        Returns:
            Dict with county markers for map display
        """
        map_data = self.fetcher.load_map_data()
        
        if not map_data.get('counties'):
            # Return empty structure if no data
            return {
                'markers': [],
                'last_updated': None,
                'has_real_data': False
            }
        
        markers = []
        for county in map_data['counties']:
            # Format for map display with enhanced bloom data
            markers.append({
                'name': county['county_name'],
                'lat': county['lat'],
                'lon': county['lon'],
                'bloom_probability': f"{county['bloom_probability']:.0f}%",
                'temperature': f"{county['temperature_c']:.1f}°C",
                'rainfall': f"{county['rainfall_mm']:.1f}mm",
                'ndvi': f"{county['ndvi']:.3f}",
                'confidence': county['confidence'],
                'is_real_data': county['is_real_data'],
                'data_source': 'NASA Satellite' if county['is_real_data'] else 'Demo',
                # New fields for enhanced modal display
                'bloom_area_km2': county.get('bloom_area_km2', 0),
                'bloom_percentage': county.get('bloom_percentage', 0),
                'bloom_prediction': county.get('bloom_prediction', 0),
                'message': county.get('message', 'N/A')
            })
        
        return {
            'markers': markers,
            'last_updated': map_data.get('last_updated'),
            'has_real_data': any(m['is_real_data'] for m in markers)
        }
    
    def get_farmer_dashboard_data(self, farmer_region: str = None) -> Dict:
        """
        Get formatted data for farmer dashboard
        
        Args:
            farmer_region: Region filter (e.g., 'central', 'rift_valley')
        
        Returns:
            Dict with bloom markers and regional data
        """
        all_data = self.fetcher.load_all_counties_data()
        
        if not all_data:
            return {
                'bloom_markers': [],
                'region_summary': {},
                'has_real_data': False
            }
        
        bloom_markers = []
        region_data = {}
        
        for county_id, county_data in all_data.items():
            if 'error' in county_data:
                continue
            
            # Filter by farmer region if specified
            if farmer_region and county_data.get('region') != farmer_region:
                continue
            
            # Create bloom markers
            bloom_prob = county_data['bloom_data']['bloom_probability']
            
            bloom_markers.append({
                'lat': county_data['coordinates']['lat'],
                'lon': county_data['coordinates']['lon'],
                'intensity': bloom_prob / 100.0,  # Convert to 0-1 scale
                'location': county_data['county_name'],
                'region': county_data['region'],
                'data_source': 'NASA Satellite' if county_data['satellite_data']['is_real_data'] else 'Demo',
                'bloom_area_km2': county_data['bloom_data']['bloom_area_km2'],
                'confidence': county_data['bloom_data']['confidence']
            })
            
            # Aggregate region summary
            region_key = county_data['region']
            if region_key not in region_data:
                region_data[region_key] = {
                    'counties': [],
                    'avg_bloom_prob': 0,
                    'total_bloom_area': 0,
                    'avg_temp': 0,
                    'avg_rainfall': 0
                }
            
            region_data[region_key]['counties'].append(county_data['county_name'])
            region_data[region_key]['avg_bloom_prob'] += bloom_prob
            region_data[region_key]['total_bloom_area'] += county_data['bloom_data']['bloom_area_km2']
            region_data[region_key]['avg_temp'] += county_data['satellite_data']['temperature_c']
            region_data[region_key]['avg_rainfall'] += county_data['satellite_data']['rainfall_mm']
        
        # Calculate averages
        for region_key, data in region_data.items():
            count = len(data['counties'])
            if count > 0:
                data['avg_bloom_prob'] /= count
                data['avg_temp'] /= count
                data['avg_rainfall'] /= count
        
        return {
            'bloom_markers': bloom_markers,
            'region_summary': region_data,
            'has_real_data': any(m['data_source'] == 'NASA Satellite' for m in bloom_markers)
        }
    
    def get_county_details(self, county_id: str) -> Dict:
        """
        Get detailed data for a specific county
        
        Args:
            county_id: County identifier
        
        Returns:
            Dict with detailed county data
        """
        county_data = self.fetcher.load_county_data(county_id)
        
        if not county_data or 'error' in county_data:
            return {'error': f'No data available for {county_id}'}
        
        return county_data
    
    def get_time_series_data(self, county_id: str, months: int = 12) -> pd.DataFrame:
        """
        Get historical time-series data for a county
        
        Args:
            county_id: County identifier
            months: Number of months of historical data
        
        Returns:
            DataFrame with time-series data
        """
        # This would need to aggregate historical data from exports
        # For now, return a placeholder
        
        from bloom_processor import BloomProcessor
        processor = BloomProcessor()
        
        ts_data = processor.generate_time_series_data(months=months)
        
        return ts_data
    
    def get_bloom_prediction_summary(self) -> Dict:
        """
        Get summary of bloom predictions across all counties
        
        Returns:
            Dict with prediction statistics
        """
        all_data = self.fetcher.load_all_counties_data()
        
        if not all_data:
            return {'error': 'No data available'}
        
        predictions = []
        high_risk_counties = []
        moderate_risk_counties = []
        low_risk_counties = []
        
        for county_id, county_data in all_data.items():
            if 'error' not in county_data:
                prob = county_data['bloom_data']['bloom_probability']
                predictions.append(prob)
                
                county_name = county_data['county_name']
                
                if prob > 70:
                    high_risk_counties.append({'name': county_name, 'probability': prob})
                elif prob > 40:
                    moderate_risk_counties.append({'name': county_name, 'probability': prob})
                else:
                    low_risk_counties.append({'name': county_name, 'probability': prob})
        
        return {
            'avg_bloom_probability': sum(predictions) / len(predictions) if predictions else 0,
            'max_bloom_probability': max(predictions) if predictions else 0,
            'min_bloom_probability': min(predictions) if predictions else 0,
            'high_risk_counties': sorted(high_risk_counties, key=lambda x: x['probability'], reverse=True)[:5],
            'moderate_risk_counties': sorted(moderate_risk_counties, key=lambda x: x['probability'], reverse=True)[:5],
            'low_risk_counties': sorted(low_risk_counties, key=lambda x: x['probability'])[:5],
            'total_counties_analyzed': len(predictions)
        }
    
    def get_climate_summary_stats(self) -> Dict:
        """
        Get aggregated climate statistics for metrics display
        
        Returns:
            Dict with climate stats
        """
        all_data = self.fetcher.load_all_counties_data()
        
        if not all_data:
            return {
                'avg_bloom_level': "N/A",
                'avg_temperature': "N/A",
                'avg_rainfall': "N/A",
                'total_bloom_area': "N/A"
            }
        
        bloom_percentages = []  # Actual current bloom levels from satellite
        temperatures = []
        rainfalls = []
        bloom_areas = []
        
        for county_data in all_data.values():
            if 'error' not in county_data:
                # Use bloom_percentage (actual current blooms) not bloom_probability (forecast)
                bloom_percentages.append(county_data['bloom_data']['bloom_percentage'])
                temperatures.append(county_data['satellite_data']['temperature_c'])
                rainfalls.append(county_data['satellite_data']['rainfall_mm'])
                bloom_areas.append(county_data['bloom_data']['bloom_area_km2'])
        
        return {
            'avg_bloom_level': f"{sum(bloom_percentages)/len(bloom_percentages):.1f}%" if bloom_percentages else "N/A",
            'avg_temperature': f"{sum(temperatures)/len(temperatures):.1f}°C" if temperatures else "N/A",
            'avg_rainfall': f"{sum(rainfalls)/len(rainfalls):.1f}mm" if rainfalls else "N/A",
            'total_bloom_area': f"{sum(bloom_areas):.0f} km²" if bloom_areas else "N/A",
            'bloom_level_delta': "+5%",  # Could calculate from historical data
            'temperature_delta': "+1°C",
            'rainfall_delta': "+15mm"
        }
    
    def is_data_fresh(self, max_age_hours: int = 6) -> bool:
        """
        Check if the data is fresh (recently fetched)
        
        Args:
            max_age_hours: Maximum age in hours to consider fresh
        
        Returns:
            True if data is fresh, False otherwise
        """
        map_data = self.fetcher.load_map_data()
        
        if not map_data.get('last_updated'):
            return False
        
        try:
            last_updated = datetime.fromisoformat(map_data['last_updated'])
            age_hours = (datetime.now() - last_updated).total_seconds() / 3600
            return age_hours <= max_age_hours
        except:
            return False
    
    def get_data_freshness_info(self) -> Dict:
        """
        Get information about data freshness
        
        Returns:
            Dict with freshness information
        """
        map_data = self.fetcher.load_map_data()
        
        if not map_data.get('last_updated'):
            return {
                'is_fresh': False,
                'last_updated': 'Never',
                'age_hours': None,
                'message': 'No data available. Please run data fetch.'
            }
        
        try:
            last_updated = datetime.fromisoformat(map_data['last_updated'])
            age_hours = (datetime.now() - last_updated).total_seconds() / 3600
            
            is_fresh = age_hours <= 6
            
            if age_hours < 1:
                age_str = f"{int(age_hours * 60)} minutes ago"
            elif age_hours < 24:
                age_str = f"{int(age_hours)} hours ago"
            else:
                age_str = f"{int(age_hours / 24)} days ago"
            
            return {
                'is_fresh': is_fresh,
                'last_updated': last_updated.strftime('%Y-%m-%d %H:%M:%S'),
                'age_hours': age_hours,
                'age_str': age_str,
                'message': 'Data is fresh' if is_fresh else 'Data may be outdated. Consider refreshing.'
            }
        except:
            return {
                'is_fresh': False,
                'last_updated': 'Unknown',
                'age_hours': None,
                'message': 'Error reading data timestamp'
            }


# Convenience function for Streamlit import
def load_streamlit_data():
    """Convenience function to get a data loader instance"""
    return StreamlitDataLoader()

