"""
Bloom Detection Processor for BloomWatch Kenya
Processes GEE exported data and detects bloom events
"""

import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from scipy.signal import find_peaks
from gee_data_loader import GEEDataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BloomProcessor:
    """Process satellite data and detect bloom events"""
    
    def __init__(self, data_dir: str = None):
        """Initialize processor"""
        self.loader = GEEDataLoader(export_dir=data_dir)
        logger.info("Bloom Processor initialized")
    
    def detect_bloom_events(self, region: str = 'kenya') -> Dict:
        """
        Detect bloom events from GEE data
        
        Returns:
            Dict with bloom information including:
            - bloom_dates: List of detected bloom dates
            - bloom_scores: Confidence scores
            - ndvi_time_series: NDVI over time
            - data_source: Which satellite data was used
        """
        logger.info(f"Detecting blooms for region: {region}")
        
        # Load data
        kenya_data = self.loader.load_kenya_data()
        
        result = {
            'data_source': kenya_data.get('source', 'Unknown'),
            'processed_at': datetime.now().isoformat(),
            'region': region
        }
        
        # Get NDVI and ARI
        ndvi = kenya_data.get('ndvi')
        ari = kenya_data.get('ari')
        
        if ndvi is None:
            logger.error("No NDVI data available")
            return self._get_empty_result(region)
        
        # Calculate NDVI statistics
        result['ndvi_mean'] = float(np.nanmean(ndvi))
        result['ndvi_std'] = float(np.nanstd(ndvi))
        result['ndvi_min'] = float(np.nanmin(ndvi))
        result['ndvi_max'] = float(np.nanmax(ndvi))
        
        # Health score (based on NDVI)
        result['health_score'] = self._calculate_health_score(ndvi)
        
        # Detect blooms from time series if available
        if 'time_series' in kenya_data:
            ts = kenya_data['time_series']
            bloom_months, scores = self._detect_from_time_series(ts, ari)
            result['bloom_months'] = bloom_months
            result['bloom_scores'] = scores.tolist()
            result['time_series_mean'] = [float(np.nanmean(ts[i])) for i in range(len(ts))]
        else:
            # Single-image bloom detection
            bloom_months, scores = self._detect_from_single_image(ndvi, ari)
            result['bloom_months'] = bloom_months
            result['bloom_scores'] = scores.tolist()
        
        # Generate bloom dates
        result['bloom_dates'] = self._get_bloom_dates(result['bloom_months'])
        
        # Identify bloom hotspots
        if ari is not None:
            result['bloom_hotspots'] = self._identify_hotspots(ari)
        
        logger.info(f"Detected {len(result['bloom_months'])} bloom events")
        
        return result
    
    def _calculate_health_score(self, ndvi: np.ndarray) -> float:
        """Calculate vegetation health score (0-100)"""
        # Normalize NDVI to health score
        mean_ndvi = np.nanmean(ndvi)
        
        # NDVI interpretation:
        # < 0.2: bare soil/low vegetation
        # 0.2-0.4: sparse vegetation
        # 0.4-0.6: moderate vegetation
        # 0.6-0.8: healthy vegetation
        # > 0.8: very healthy/dense vegetation
        
        if mean_ndvi < 0.2:
            score = mean_ndvi * 100  # 0-20
        elif mean_ndvi < 0.4:
            score = 20 + (mean_ndvi - 0.2) * 150  # 20-50
        elif mean_ndvi < 0.6:
            score = 50 + (mean_ndvi - 0.4) * 125  # 50-75
        else:
            score = 75 + (mean_ndvi - 0.6) * 62.5  # 75-100
        
        return min(100.0, max(0.0, float(score)))
    
    def _detect_from_time_series(self, ts: np.ndarray, ari: np.ndarray = None) -> Tuple[List[int], np.ndarray]:
        """
        Detect bloom events from NDVI time series
        
        Args:
            ts: Time series array (time, height, width)
            ari: Anthocyanin Reflectance Index (optional)
        
        Returns:
            bloom_months: List of month indices with blooms
            scores: Confidence scores for each month
        """
        # Calculate mean NDVI for each time step
        ndvi_mean = np.array([np.nanmean(ts[i]) for i in range(len(ts))])
        
        # Find peaks in NDVI (high vegetation)
        peaks, properties = find_peaks(
            ndvi_mean,
            prominence=0.05,  # Minimum prominence
            width=1  # Minimum width
        )
        
        # Score based on NDVI values
        scores = np.zeros(len(ts))
        
        for peak in peaks:
            # Score based on NDVI value and prominence
            ndvi_score = min(1.0, ndvi_mean[peak] / 0.8)  # Normalize to 0.8
            
            # Bonus for ARI if available
            ari_bonus = 0.0
            if ari is not None:
                ari_mean = np.nanmean(ari)
                ari_bonus = min(0.2, ari_mean)  # Up to 0.2 bonus
            
            scores[peak] = min(1.0, ndvi_score + ari_bonus)
        
        # Filter low scores
        bloom_months = [int(peak) for peak in peaks if scores[peak] > 0.4]
        
        # Add Kenya-specific bloom season adjustments
        bloom_months = self._adjust_for_kenya_seasons(bloom_months, scores)
        
        return bloom_months, scores
    
    def _detect_from_single_image(self, ndvi: np.ndarray, ari: np.ndarray = None) -> Tuple[List[int], np.ndarray]:
        """Detect likely bloom months from single NDVI image"""
        # Estimate bloom months based on current NDVI and Kenya crop calendar
        current_month = datetime.now().month
        mean_ndvi = np.nanmean(ndvi)
        
        scores = np.zeros(12)
        bloom_months = []
        
        # Kenya bloom seasons:
        # Long rains: March-May (3-5)
        # Short rains: October-December (10-12)
        
        if mean_ndvi > 0.5:  # Healthy vegetation
            # Current season
            if 2 <= current_month <= 5:  # Long rains
                bloom_months = [3, 4]
                scores[3] = 0.8
                scores[4] = 0.7
            elif 9 <= current_month <= 12:  # Short rains
                bloom_months = [10, 11]
                scores[10] = 0.7
                scores[11] = 0.6
            else:  # Dry season - predict next season
                if current_month < 3:
                    bloom_months = [3, 4]
                    scores[3] = 0.6
                    scores[4] = 0.5
                else:
                    bloom_months = [10, 11]
                    scores[10] = 0.6
                    scores[11] = 0.5
        
        # Boost score if ARI is high
        if ari is not None:
            ari_mean = np.nanmean(ari)
            if ari_mean > 0.15:
                for month in bloom_months:
                    scores[month] += 0.2
        
        return bloom_months, scores
    
    def _adjust_for_kenya_seasons(self, bloom_months: List[int], scores: np.ndarray) -> List[int]:
        """Adjust bloom detections based on Kenya crop calendar"""
        # Kenya's main bloom periods
        long_rains = [2, 3, 4]  # March-May (0-indexed)
        short_rains = [9, 10, 11]  # Oct-Dec
        
        adjusted = []
        
        for month in bloom_months:
            # Keep if in known bloom season
            if month in long_rains or month in short_rains:
                adjusted.append(month)
            # Otherwise, check if score is very high
            elif scores[month] > 0.7:
                adjusted.append(month)
        
        return adjusted
    
    def _get_bloom_dates(self, bloom_months: List[int]) -> List[str]:
        """Convert month indices to actual dates"""
        current_year = datetime.now().year
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        bloom_dates = []
        for month_idx in bloom_months:
            # Adjust for 0-indexed months
            month_num = month_idx + 1 if month_idx < 12 else 1
            year = current_year
            
            # If month is in past, assume next year
            if month_num < datetime.now().month:
                year += 1
            
            bloom_dates.append(f"{month_names[month_idx]} {year}")
        
        return bloom_dates
    
    def _identify_hotspots(self, ari: np.ndarray, threshold: float = 0.2) -> List[Dict]:
        """Identify bloom hotspots from ARI data"""
        # Find regions with high ARI (flower pigments)
        hotspots = []
        
        # Simple threshold-based detection
        high_ari = ari > threshold
        
        if np.any(high_ari):
            # Count hotspot pixels
            num_hotspots = int(np.sum(high_ari))
            max_ari = float(np.nanmax(ari))
            
            hotspots.append({
                'intensity': max_ari,
                'area_pixels': num_hotspots,
                'location': 'Central Kenya',  # Would be more specific with actual coords
                'confidence': min(1.0, max_ari / 0.3)
            })
        
        return hotspots
    
    def _get_empty_result(self, region: str) -> Dict:
        """Return empty result structure"""
        return {
            'data_source': 'None',
            'processed_at': datetime.now().isoformat(),
            'region': region,
            'bloom_months': [],
            'bloom_scores': [],
            'bloom_dates': [],
            'error': 'No data available'
        }
    
    def get_region_summary(self, region: str = 'kenya') -> Dict:
        """Get summary statistics for a region"""
        bloom_data = self.detect_bloom_events(region)
        
        summary = {
            'region': region,
            'data_source': bloom_data.get('data_source'),
            'health_score': bloom_data.get('health_score', 0),
            'num_bloom_events': len(bloom_data.get('bloom_months', [])),
            'next_bloom': bloom_data['bloom_dates'][0] if bloom_data.get('bloom_dates') else 'Unknown',
            'updated_at': bloom_data.get('processed_at')
        }
        
        return summary


# Testing
if __name__ == "__main__":
    print("🌸 Bloom Processor Test")
    print("=" * 60)
    
    processor = BloomProcessor()
    
    # Detect blooms
    print("\n🔍 Detecting bloom events...")
    results = processor.detect_bloom_events('kenya')
    
    print(f"\n📊 Data Source: {results['data_source']}")
    print(f"🌱 Health Score: {results.get('health_score', 0):.1f}/100")
    print(f"🌸 Bloom Events: {len(results['bloom_months'])}")
    
    if results['bloom_dates']:
        print("\n📅 Predicted Bloom Dates:")
        for i, date in enumerate(results['bloom_dates']):
            score = results['bloom_scores'][results['bloom_months'][i]]
            print(f"  • {date} (confidence: {score:.0%})")
    
    if results.get('ndvi_mean'):
        print(f"\n📈 NDVI Statistics:")
        print(f"  Mean: {results['ndvi_mean']:.3f}")
        print(f"  Range: {results['ndvi_min']:.3f} - {results['ndvi_max']:.3f}")
    
    if results.get('bloom_hotspots'):
        print(f"\n🎯 Bloom Hotspots: {len(results['bloom_hotspots'])}")
        for hotspot in results['bloom_hotspots']:
            print(f"  • {hotspot['location']}: {hotspot['confidence']:.0%} confidence")
    
    # Get summary
    print("\n📋 Region Summary:")
    summary = processor.get_region_summary('kenya')
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ Bloom Processor test complete!")


