"""
Kenya Crop Calendar and Agricultural Intelligence
Integrates local crop seasons, varieties, and bloom patterns
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import calendar

class KenyaCropCalendar:
    """Kenya-specific crop calendar with bloom timing and agricultural insights"""
    
    def __init__(self):
        self.crop_calendar = {
            'maize': {
                'seasons': {
                    'long_rains': {'plant': (3, 4), 'bloom': (6, 7), 'harvest': (8, 9)},
                    'short_rains': {'plant': (10, 11), 'bloom': (1, 2), 'harvest': (3, 4)}
                },
                'varieties': ['H614', 'H629', 'DK8031', 'Local varieties'],
                'bloom_duration_days': 14,
                'critical_stages': ['tasseling', 'silking', 'grain_filling'],
                'regions': ['Central', 'Rift Valley', 'Eastern', 'Western']
            },
            'beans': {
                'seasons': {
                    'long_rains': {'plant': (3, 4), 'bloom': (5, 6), 'harvest': (7, 8)},
                    'short_rains': {'plant': (10, 11), 'bloom': (12, 1), 'harvest': (2, 3)}
                },
                'varieties': ['Rose coco', 'Canadian wonder', 'Mwitemania', 'GLP-2'],
                'bloom_duration_days': 10,
                'critical_stages': ['flowering', 'pod_formation', 'pod_filling'],
                'regions': ['Central', 'Eastern', 'Western']
            },
            'coffee': {
                'seasons': {
                    'main_bloom': {'plant': 'perennial', 'bloom': (3, 5), 'harvest': (10, 12)},
                    'fly_bloom': {'plant': 'perennial', 'bloom': (9, 11), 'harvest': (5, 7)}
                },
                'varieties': ['SL28', 'SL34', 'K7', 'Ruiru 11', 'Batian'],
                'bloom_duration_days': 21,
                'critical_stages': ['flowering', 'pin_head', 'cherry_development'],
                'regions': ['Central', 'Eastern', 'Nyanza']
            },
            'tea': {
                'seasons': {
                    'continuous': {'plant': 'perennial', 'bloom': (1, 12), 'harvest': (1, 12)}
                },
                'varieties': ['TRFK 6/8', 'TRFK 31/8', 'Purple tea'],
                'bloom_duration_days': 365,  # Continuous
                'critical_stages': ['flush_growth', 'leaf_maturity'],
                'regions': ['Central', 'Rift Valley', 'Western']
            },
            'wheat': {
                'seasons': {
                    'long_rains': {'plant': (6, 7), 'bloom': (9, 10), 'harvest': (11, 12)},
                    'short_rains': {'plant': (1, 2), 'bloom': (4, 5), 'harvest': (6, 7)}
                },
                'varieties': ['Kenya Kudu', 'Kenya Tai', 'Njoro BW II'],
                'bloom_duration_days': 7,
                'critical_stages': ['heading', 'flowering', 'grain_filling'],
                'regions': ['Rift Valley', 'Central']
            },
            'sorghum': {
                'seasons': {
                    'long_rains': {'plant': (3, 4), 'bloom': (6, 7), 'harvest': (8, 9)},
                    'short_rains': {'plant': (10, 11), 'bloom': (1, 2), 'harvest': (3, 4)}
                },
                'varieties': ['Gadam', 'Serena', 'Kari Mtama 1'],
                'bloom_duration_days': 10,
                'critical_stages': ['panicle_emergence', 'flowering', 'grain_filling'],
                'regions': ['Eastern', 'Coast', 'Northern']
            }
        }
        
        # Kenya rainfall patterns
        self.rainfall_seasons = {
            'long_rains': (3, 5),  # March-May
            'short_rains': (10, 12),  # October-December
            'dry_season_1': (1, 2),  # January-February
            'dry_season_2': (6, 9)   # June-September
        }
    
    def get_current_season(self) -> str:
        """Determine current agricultural season in Kenya"""
        current_month = datetime.now().month
        
        if 3 <= current_month <= 5:
            return 'long_rains'
        elif 10 <= current_month <= 12:
            return 'short_rains'
        elif current_month in [1, 2]:
            return 'dry_season_1'
        else:
            return 'dry_season_2'
    
    def get_expected_blooms(self, month: int = None) -> Dict[str, List[str]]:
        """Get crops expected to bloom in given month"""
        if month is None:
            month = datetime.now().month
        
        blooming_crops = {}
        
        for crop, data in self.crop_calendar.items():
            for season, timing in data['seasons'].items():
                bloom_months = timing['bloom']
                if isinstance(bloom_months, tuple):
                    start_month, end_month = bloom_months
                    # Handle year wrap-around
                    if start_month <= end_month:
                        if start_month <= month <= end_month:
                            if crop not in blooming_crops:
                                blooming_crops[crop] = []
                            blooming_crops[crop].append(season)
                    else:  # Crosses year boundary
                        if month >= start_month or month <= end_month:
                            if crop not in blooming_crops:
                                blooming_crops[crop] = []
                            blooming_crops[crop].append(season)
        
        return blooming_crops
    
    def get_crop_info(self, crop: str) -> Dict:
        """Get detailed information about a specific crop"""
        return self.crop_calendar.get(crop.lower(), {})
    
    def predict_bloom_window(self, crop: str, planting_date: datetime) -> List[Tuple[datetime, datetime]]:
        """Predict bloom windows based on planting date"""
        crop_info = self.get_crop_info(crop)
        if not crop_info:
            return []
        
        bloom_windows = []
        for season, timing in crop_info['seasons'].items():
            if timing['plant'] == 'perennial':
                # For perennial crops, use standard bloom months
                bloom_months = timing['bloom']
                if isinstance(bloom_months, tuple):
                    start_month, end_month = bloom_months
                    year = planting_date.year
                    
                    # Handle year transitions
                    if start_month > end_month:
                        if planting_date.month >= start_month:
                            bloom_start = datetime(year, start_month, 1)
                            bloom_end = datetime(year + 1, end_month, 
                                               calendar.monthrange(year + 1, end_month)[1])
                        else:
                            bloom_start = datetime(year, start_month, 1)
                            bloom_end = datetime(year, end_month, 
                                               calendar.monthrange(year, end_month)[1])
                    else:
                        bloom_start = datetime(year, start_month, 1)
                        bloom_end = datetime(year, end_month, 
                                           calendar.monthrange(year, end_month)[1])
                    
                    bloom_windows.append((bloom_start, bloom_end))
            else:
                # Calculate bloom window based on planting date
                bloom_months = timing['bloom']
                if isinstance(bloom_months, tuple):
                    # Estimate days from planting to bloom
                    plant_months = timing['plant']
                    if isinstance(plant_months, tuple):
                        avg_plant_month = sum(plant_months) / 2
                        avg_bloom_month = sum(bloom_months) / 2
                        months_to_bloom = avg_bloom_month - avg_plant_month
                        if months_to_bloom < 0:
                            months_to_bloom += 12
                        
                        days_to_bloom = int(months_to_bloom * 30.44)  # Average days per month
                        bloom_start = planting_date + timedelta(days=days_to_bloom)
                        bloom_end = bloom_start + timedelta(days=crop_info['bloom_duration_days'])
                        
                        bloom_windows.append((bloom_start, bloom_end))
        
        return bloom_windows
    
    def get_agricultural_advice(self, crop: str, current_stage: str) -> Dict[str, str]:
        """Get agricultural advice based on crop and growth stage"""
        advice = {
            'maize': {
                'tasseling': {
                    'en': "Monitor for adequate moisture. This is critical for pollen production.",
                    'sw': "Angalia kama kuna maji ya kutosha. Hii ni muhimu kwa uzalishaji wa chavua."
                },
                'silking': {
                    'en': "Ensure good pollination. Watch for pest attacks on silks.",
                    'sw': "Hakikisha uchavushaji mzuri. Chunga wadudu kwenye nyuzi za mahindi."
                },
                'grain_filling': {
                    'en': "Maintain soil moisture. Consider disease prevention measures.",
                    'sw': "Dumisha unyevu wa udongo. Fikiria njia za kuzuia magonjwa."
                }
            },
            'beans': {
                'flowering': {
                    'en': "Avoid overhead irrigation to prevent flower drop. Monitor for aphids.",
                    'sw': "Epuka kumwagilia juu ili kuzuia maua kuanguka. Chunga wadudu wadogo."
                },
                'pod_formation': {
                    'en': "Ensure adequate phosphorus. Watch for pod borers.",
                    'sw': "Hakikisha phosphorus ya kutosha. Chunga wadudu wa miharagwe."
                }
            },
            'coffee': {
                'flowering': {
                    'en': "Maintain consistent moisture. Avoid disturbance during bloom.",
                    'sw': "Dumisha unyevu sawa. Epuka kusumbua wakati wa kuchanua."
                },
                'pin_head': {
                    'en': "Critical stage for fruit set. Monitor for coffee berry disease.",
                    'sw': "Hatua muhimu ya kuanza matunda. Chunga ugonjwa wa coffee berry."
                }
            }
        }
        
        return advice.get(crop.lower(), {}).get(current_stage, {
            'en': f"Monitor {crop} carefully during {current_stage} stage.",
            'sw': f"Fuatilia {crop} kwa makini wakati wa hatua ya {current_stage}."
        })

# Kenya agricultural regions and their characteristics
KENYA_REGIONS = {
    'central': {
        'counties': ['Kiambu', 'Murang\'a', 'Nyeri', 'Kirinyaga', 'Nyandarua'],
        'altitude_range': (1200, 2500),
        'main_crops': ['coffee', 'tea', 'maize', 'beans', 'potatoes'],
        'rainfall_mm': (800, 1800),
        'coordinates': {'lat': -0.9, 'lon': 36.9}
    },
    'rift_valley': {
        'counties': ['Nakuru', 'Uasin Gishu', 'Trans Nzoia', 'Kericho', 'Bomet'],
        'altitude_range': (1500, 3000),
        'main_crops': ['maize', 'wheat', 'tea', 'pyrethrum', 'barley'],
        'rainfall_mm': (700, 1500),
        'coordinates': {'lat': 0.2, 'lon': 35.8}
    },
    'western': {
        'counties': ['Kakamega', 'Bungoma', 'Busia', 'Vihiga'],
        'altitude_range': (1200, 2000),
        'main_crops': ['maize', 'beans', 'sugarcane', 'tea', 'bananas'],
        'rainfall_mm': (1200, 2000),
        'coordinates': {'lat': 0.5, 'lon': 34.8}
    },
    'eastern': {
        'counties': ['Machakos', 'Kitui', 'Makueni', 'Embu', 'Tharaka-Nithi'],
        'altitude_range': (500, 2000),
        'main_crops': ['maize', 'beans', 'sorghum', 'millet', 'cotton'],
        'rainfall_mm': (400, 1200),
        'coordinates': {'lat': -1.5, 'lon': 37.5}
    }
}

if __name__ == "__main__":
    # Test the crop calendar
    calendar = KenyaCropCalendar()
    
    print("Current season:", calendar.get_current_season())
    print("Expected blooms this month:", calendar.get_expected_blooms())
    
    # Test bloom prediction
    planting_date = datetime(2024, 3, 15)  # March planting
    maize_blooms = calendar.predict_bloom_window('maize', planting_date)
    print(f"Maize bloom windows from {planting_date.date()}: {maize_blooms}")
    
    # Test agricultural advice
    advice = calendar.get_agricultural_advice('maize', 'tasseling')
    print("Maize tasseling advice:", advice)
