"""
Enhanced Bloom Detection Processor for Smart Shamba
Processes satellite data from PostgreSQL, detects bloom events, and prepares ML training data.

Single source of truth: PostgreSQL (gee_county_data, sensor_readings, model_outputs tables).
Model weights are persisted under data/models/.

Features:
- NDWI/NDVI threshold-based bloom area computation
- Historical data aggregation and time-series analysis (from PG)
- ML training data preparation with binary labels
- Integration with enhanced Earth Engine pipeline
"""

import numpy as np
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from scipy.signal import find_peaks
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available — peak detection will use fallback")

# ---------- Database ----------
try:
    from database.connection import get_sync_session
    from database.models import GEECountyData, BloomEvent, SensorReading, ModelOutput
    from sqlmodel import select, text, func, desc, and_
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    get_sync_session = None  # type: ignore[assignment]
    GEECountyData = None  # type: ignore[assignment,misc]
    BloomEvent = None  # type: ignore[assignment,misc]
    SensorReading = None  # type: ignore[assignment,misc]
    ModelOutput = None  # type: ignore[assignment,misc]
    select = None  # type: ignore[assignment]
    text = None  # type: ignore[assignment]
    func = None  # type: ignore[assignment]
    desc = None  # type: ignore[assignment]
    and_ = None  # type: ignore[assignment]
    logger.warning("Database modules not available — bloom processor in demo mode.")

# ---------- Paths (only model weights) ----------
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
MODELS_DIR = os.path.join(DATA_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# Bloom detection thresholds
NDWI_BLOOM_THRESHOLD = 0.3   # Water/bloom areas
NDVI_VEGETATION_THRESHOLD = 0.5  # Healthy vegetation
ARI_FLOWER_THRESHOLD = 0.15  # Flower pigments


class BloomProcessor:
    """Enhanced processor for satellite data, bloom detection, and ML data preparation.

    All reads come from PostgreSQL (gee_county_data table).
    Model weights are stored under data/models/.
    """

    def __init__(self, db_service=None):
        """Initialize enhanced processor.

        Args:
            db_service: Optional PostgresService instance.  When provided the
                        processor uses it for high-level queries (get_county_data,
                        get_all_counties_latest, etc.).  Otherwise falls back to
                        direct SQLModel sessions.
        """
        self.db = db_service

        # Historical data cache
        self.historical_data: Dict = {}
        self.time_series_cache: Dict = {}

        logger.info("✓ Bloom Processor initialized (PostgreSQL mode)")

    # ------------------------------------------------------------------ #
    #  Bloom area computation
    # ------------------------------------------------------------------ #

    def compute_bloom_areas(self, ndwi_threshold: float = NDWI_BLOOM_THRESHOLD,
                            ndvi_threshold: float = NDVI_VEGETATION_THRESHOLD) -> Dict:
        """
        Compute aggregate bloom areas from the latest county data in PostgreSQL.

        Returns:
            Dict with bloom area statistics.
        """
        logger.info(f"Computing bloom areas with NDWI>{ndwi_threshold}, NDVI>{ndvi_threshold}")

        try:
            counties = self._get_all_counties_latest()
            if not counties:
                logger.warning("No county data in database — returning zeros")
                return self._empty_bloom_area(ndwi_threshold, ndvi_threshold)

            total_bloom_km2 = 0.0
            county_count = 0
            for c in counties:
                bloom_area = c.get('bloom_area_km2') or 0.0
                total_bloom_km2 += bloom_area
                county_count += 1

            # Average bloom percentage across counties
            bloom_pcts = [c.get('bloom_percentage', 0) or 0 for c in counties]
            avg_bloom_pct = float(np.mean(bloom_pcts)) if bloom_pcts else 0.0

            return {
                'bloom_area_km2': total_bloom_km2,
                'total_counties': county_count,
                'avg_bloom_percentage': avg_bloom_pct,
                'ndwi_threshold': ndwi_threshold,
                'ndvi_threshold': ndvi_threshold,
                'timestamp': datetime.now().isoformat(),
                'method': 'PostgreSQL gee_county_data aggregation',
                'data_source': 'NASA Satellite (via db)',
            }

        except Exception as e:
            logger.error(f"Error computing bloom areas: {e}")
            return {**self._empty_bloom_area(ndwi_threshold, ndvi_threshold), 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Historical data aggregation (from PG instead of CSVs)
    # ------------------------------------------------------------------ #

    def aggregate_historical_data(self, months_back: int = 12) -> Dict:
        """
        Aggregate historical satellite data from PostgreSQL gee_county_data.

        Returns:
            Dict with time-series and statistics (including soil data when available).
        """
        logger.info(f"Aggregating {months_back} months of historical data from PostgreSQL")

        if not DB_AVAILABLE:
            logger.warning("Database not available — using synthetic data")
            return self._generate_synthetic_historical_data(months_back)

        try:
            from datetime import date as date_type
            cutoff = date_type.today() - timedelta(days=months_back * 30)

            with get_sync_session() as session:  # type: ignore[misc]
                # Aggregate daily averages across all counties (now includes soil)
                sql = text("""
                    SELECT
                        observation_date,
                        AVG(ndvi)                AS ndvi_mean,
                        AVG(ndwi)                AS ndwi_mean,
                        AVG(rainfall_mm)         AS rainfall_mm,
                        AVG(temperature_mean_c)  AS temperature_c,
                        AVG(soil_moisture_pct)   AS soil_moisture_pct,
                        AVG(soil_ph)             AS soil_ph,
                        AVG(soil_clay_pct)       AS soil_clay_pct,
                        COUNT(*)                 AS county_count
                    FROM gee_county_data
                    WHERE observation_date >= :cutoff
                      AND sub_county IS NULL
                    GROUP BY observation_date
                    ORDER BY observation_date
                """)
                rows = session.exec(sql, params={"cutoff": cutoff}).all()  # type: ignore[call-overload]

            if not rows:
                logger.warning("No historical data in PG — generating synthetic")
                return self._generate_synthetic_historical_data(months_back)

            dates = [str(r[0]) for r in rows]
            ndvi_values = [float(r[1] or 0) for r in rows]
            ndwi_values = [float(r[2] or 0) for r in rows]
            rainfall_values = [float(r[3] or 0) for r in rows]
            temperature_values = [float(r[4] or 0) for r in rows]
            soil_moisture_values = [float(r[5]) if r[5] is not None else None for r in rows]
            soil_ph_values = [float(r[6]) if r[6] is not None else None for r in rows]
            soil_clay_values = [float(r[7]) if r[7] is not None else None for r in rows]

            time_series = {
                'dates': dates,
                'ndvi_values': ndvi_values,
                'ndwi_values': ndwi_values,
                'rainfall_values': rainfall_values,
                'temperature_values': temperature_values,
                'soil_moisture_values': soil_moisture_values,
                'soil_ph_values': soil_ph_values,
                'soil_clay_values': soil_clay_values,
                'data_points': len(rows),
            }

            stats = {
                'ndvi_mean': float(np.mean(ndvi_values)) if ndvi_values else 0,
                'ndvi_std': float(np.std(ndvi_values)) if ndvi_values else 0,
                'rainfall_total': float(np.sum(rainfall_values)) if rainfall_values else 0,
                'temperature_avg': float(np.mean(temperature_values)) if temperature_values else 0,
            }

            return {
                'time_series': time_series,
                'statistics': stats,
                'period_months': months_back,
                'data_source': 'PostgreSQL gee_county_data',
                'processed_at': datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error aggregating historical data: {e}")
            return {'error': str(e)}

    # ------------------------------------------------------------------ #
    #  ML training data preparation
    # ------------------------------------------------------------------ #

    def prepare_ml_training_data(self, include_weather: bool = True) -> Dict:
        """
        Prepare ML training data from PostgreSQL historical data.
        Creates binary labels (bloom / no bloom) based on thresholds.
        Includes soil features when available.

        Returns:
            Dict with training features and labels as numpy arrays.
        """
        logger.info("Preparing ML training data with binary bloom labels")

        try:
            historical = self.aggregate_historical_data()

            if 'error' in historical:
                logger.warning("Using synthetic data for ML training")
                return self._generate_synthetic_ml_data(include_weather)

            time_series = historical['time_series']

            features: List[List[float]] = []
            labels: List[int] = []
            dates: List[str] = []

            ndvi_values = time_series.get('ndvi_values', [])
            ndwi_values = time_series.get('ndwi_values', [])
            soil_moisture_values = time_series.get('soil_moisture_values', [])
            soil_ph_values = time_series.get('soil_ph_values', [])
            soil_clay_values = time_series.get('soil_clay_values', [])

            # Check if soil data is available (not all None)
            has_soil = any(v is not None for v in soil_moisture_values)

            for i, (ndvi, ndwi) in enumerate(zip(ndvi_values, ndwi_values)):
                if ndvi > 0 and ndwi > 0:
                    feature_row = [ndvi, ndwi]

                    if include_weather:
                        rainfall = time_series.get('rainfall_values', [0] * len(ndvi_values))[i]
                        temp = time_series.get('temperature_values', [25] * len(ndvi_values))[i]
                        feature_row.extend([rainfall, temp])

                    if has_soil:
                        sm = soil_moisture_values[i] if i < len(soil_moisture_values) and soil_moisture_values[i] is not None else 0.0
                        ph = soil_ph_values[i] if i < len(soil_ph_values) and soil_ph_values[i] is not None else 6.5
                        clay = soil_clay_values[i] if i < len(soil_clay_values) and soil_clay_values[i] is not None else 0.0
                        feature_row.extend([sm, ph, clay])

                    features.append(feature_row)
                    bloom_label = 1 if (ndwi > NDWI_BLOOM_THRESHOLD and ndvi > NDVI_VEGETATION_THRESHOLD) else 0
                    labels.append(bloom_label)

                    if i < len(time_series.get('dates', [])):
                        dates.append(time_series['dates'][i])
                    else:
                        dates.append(f"Day_{i}")

            n_feat = 2
            if include_weather:
                n_feat += 2
            if has_soil:
                n_feat += 3

            X = np.array(features) if features else np.empty((0, n_feat))
            y = np.array(labels) if labels else np.empty(0)

            feature_names = ['ndvi', 'ndwi']
            if include_weather:
                feature_names.extend(['rainfall_mm', 'temperature_c'])
            if has_soil:
                feature_names.extend(['soil_moisture_pct', 'soil_ph', 'soil_clay_pct'])

            bloom_count = int(np.sum(y == 1)) if len(y) else 0
            no_bloom_count = int(np.sum(y == 0)) if len(y) else 0

            return {
                'features': X,
                'labels': y,
                'dates': dates,
                'feature_names': feature_names,
                'n_samples': len(X),
                'n_features': X.shape[1] if len(X) > 0 else 0,
                'bloom_count': bloom_count,
                'no_bloom_count': no_bloom_count,
                'class_balance': float(bloom_count / len(y)) if len(y) > 0 else 0,
                'thresholds': {
                    'ndwi': NDWI_BLOOM_THRESHOLD,
                    'ndvi': NDVI_VEGETATION_THRESHOLD,
                },
                'include_weather': include_weather,
                'include_soil': has_soil,
                'prepared_at': datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error preparing ML training data: {e}")
            return {'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Time-series generation for visualisations
    # ------------------------------------------------------------------ #

    def generate_time_series_data(self, data_type: str = 'ndvi', months: int = 12) -> Dict:
        """
        Generate time-series data for frontend visualisations.

        Args:
            data_type: 'ndvi' | 'ndwi' | 'rainfall' | 'temperature'
            months: Number of months to include.
        """
        logger.info(f"Generating {data_type} time-series for {months} months")

        try:
            historical = self.aggregate_historical_data(months)

            if 'error' in historical:
                return self._generate_synthetic_time_series(data_type, months)

            time_series = historical['time_series']
            key_map = {
                'ndvi': ('ndvi_values', 'NDVI', 'green'),
                'ndwi': ('ndwi_values', 'NDWI', 'blue'),
                'rainfall': ('rainfall_values', 'Rainfall (mm)', 'lightblue'),
                'temperature': ('temperature_values', 'Temperature (°C)', 'red'),
            }

            if data_type not in key_map:
                return {'error': f'Unknown data type: {data_type}'}

            values_key, ylabel, color = key_map[data_type]
            values = time_series.get(values_key, [])
            dates = time_series.get('dates', [f"Day_{i}" for i in range(len(values))])

            return {
                'data_type': data_type,
                'dates': dates[:len(values)],
                'values': values,
                'ylabel': ylabel,
                'color': color,
                'n_points': len(values),
                'mean_value': float(np.mean(values)) if values else 0,
                'min_value': float(np.min(values)) if values else 0,
                'max_value': float(np.max(values)) if values else 0,
                'period_months': months,
                'generated_at': datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating time-series data: {e}")
            return {'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Bloom event detection
    # ------------------------------------------------------------------ #

    def detect_bloom_events(self, region: str = 'kenya') -> Dict:
        """Enhanced bloom event detection using PostgreSQL county data."""
        logger.info(f"Detecting bloom events for region: {region}")

        try:
            bloom_areas = self.compute_bloom_areas()
            basic_results = self._detect_bloom_events_from_pg(region)

            result = basic_results.copy()
            result.update({
                'bloom_area_km2': bloom_areas.get('bloom_area_km2', 0),
                'avg_bloom_percentage': bloom_areas.get('avg_bloom_percentage', 0),
                'computation_method': 'PostgreSQL gee_county_data',
            })
            return result

        except Exception as e:
            logger.error(f"Error detecting bloom events: {e}")
            return self._get_empty_result(region)

    def _detect_bloom_events_from_pg(self, region: str = 'kenya') -> Dict:
        """Detect bloom events from the latest PostgreSQL county data."""
        try:
            counties = self._get_all_counties_latest()
            if not counties:
                return self._get_empty_result(region)

            # Aggregate NDVI across counties
            ndvi_vals = [c['ndvi'] for c in counties if c.get('ndvi')]
            ndwi_vals = [c['ndwi'] for c in counties if c.get('ndwi')]

            if not ndvi_vals:
                return self._get_empty_result(region)

            ndvi_arr = np.array(ndvi_vals)
            mean_ndvi = float(np.mean(ndvi_arr))

            result: Dict = {
                'data_source': counties[0].get('data_source', 'PostgreSQL'),
                'processed_at': datetime.now().isoformat(),
                'region': region,
                'ndvi_mean': mean_ndvi,
                'ndvi_std': float(np.std(ndvi_arr)),
                'ndvi_min': float(np.min(ndvi_arr)),
                'ndvi_max': float(np.max(ndvi_arr)),
                'health_score': self._calculate_health_score_scalar(mean_ndvi),
            }

            # Determine bloom months from Kenya seasonal patterns + current NDVI
            bloom_months, scores = self._detect_from_pg_data(mean_ndvi, ndwi_vals)
            result['bloom_months'] = bloom_months
            result['bloom_scores'] = scores.tolist()
            result['bloom_dates'] = self._get_bloom_dates(bloom_months)

            logger.info(f"Detected {len(bloom_months)} bloom events from PG data")
            return result

        except Exception as e:
            logger.error(f"Error in PG bloom detection: {e}")
            return self._get_empty_result(region)

    # ------------------------------------------------------------------ #
    #  PostgreSQL helpers
    # ------------------------------------------------------------------ #

    def _get_all_counties_latest(self) -> List[Dict]:
        """Get latest data for all counties from PG (via db_service or direct)."""
        if self.db and hasattr(self.db, 'get_all_counties_latest'):
            return self.db.get_all_counties_latest()

        if not DB_AVAILABLE:
            return []

        try:
            with get_sync_session() as session:  # type: ignore[misc]
                subq = (
                    select(
                        GEECountyData.county,
                        func.max(GEECountyData.observation_date).label("max_date"),
                    )
                    .where(GEECountyData.sub_county.is_(None))  # type: ignore[union-attr]
                    .group_by(GEECountyData.county)
                    .subquery()
                )
                stmt = (
                    select(GEECountyData)
                    .join(
                        subq,
                        and_(
                            GEECountyData.county == subq.c.county,
                            GEECountyData.observation_date == subq.c.max_date,
                        ),
                    )
                    .order_by(GEECountyData.county)
                )
                rows = session.exec(stmt).all()
                return [self._row_to_dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Error getting counties from PG: {e}")
            return []

    @staticmethod
    def _row_to_dict(r) -> Dict:
        """Convert a GEECountyData row to a plain dict."""
        return {
            'county': r.county,
            'sub_county': r.sub_county,
            'region': r.region,
            'observation_date': str(r.observation_date) if r.observation_date else None,
            'ndvi': r.ndvi,
            'ndwi': r.ndwi,
            'evi': r.evi,
            'rainfall_mm': r.rainfall_mm,
            'temperature_mean_c': r.temperature_mean_c,
            'bloom_area_km2': r.bloom_area_km2,
            'bloom_percentage': r.bloom_percentage,
            'bloom_probability': r.bloom_probability,
            'data_source': r.data_source,
            'is_real_data': r.is_real_data,
            'soil_moisture_pct': r.soil_moisture_pct,
            'center_lat': r.center_lat,
            'center_lon': r.center_lon,
        }

    # ------------------------------------------------------------------ #
    #  Detection helpers
    # ------------------------------------------------------------------ #

    def _detect_from_pg_data(self, mean_ndvi: float,
                              ndwi_vals: List[float]) -> Tuple[List[int], np.ndarray]:
        """Detect likely bloom months from aggregated PG data."""
        current_month = datetime.now().month
        scores = np.zeros(12)
        bloom_months: List[int] = []

        mean_ndwi = float(np.mean(ndwi_vals)) if ndwi_vals else 0.0

        if mean_ndvi > 0.5:
            # Kenya long rains: March-May, short rains: Oct-Dec
            if 2 <= current_month <= 5:
                bloom_months = [3, 4]
                scores[3] = 0.8
                scores[4] = 0.7
            elif 9 <= current_month <= 12:
                bloom_months = [10, 11]
                scores[10] = 0.7
                scores[11] = 0.6
            else:
                if current_month < 3:
                    bloom_months = [3, 4]
                    scores[3] = 0.6
                    scores[4] = 0.5
                else:
                    bloom_months = [10, 11]
                    scores[10] = 0.6
                    scores[11] = 0.5

        # Boost if NDWI is high
        if mean_ndwi > NDWI_BLOOM_THRESHOLD:
            for m in bloom_months:
                scores[m] = min(1.0, scores[m] + 0.15)

        return bloom_months, scores

    @staticmethod
    def _calculate_health_score_scalar(mean_ndvi: float) -> float:
        """Calculate vegetation health score (0-100) from a scalar NDVI."""
        if mean_ndvi < 0.2:
            score = mean_ndvi * 100
        elif mean_ndvi < 0.4:
            score = 20 + (mean_ndvi - 0.2) * 150
        elif mean_ndvi < 0.6:
            score = 50 + (mean_ndvi - 0.4) * 125
        else:
            score = 75 + (mean_ndvi - 0.6) * 62.5
        return min(100.0, max(0.0, float(score)))

    # Keep backward-compat alias used by smart_alert_service
    def _calculate_health_score(self, ndvi) -> float:
        if isinstance(ndvi, (int, float)):
            return self._calculate_health_score_scalar(float(ndvi))
        return self._calculate_health_score_scalar(float(np.nanmean(ndvi)))

    @staticmethod
    def _get_bloom_dates(bloom_months: List[int]) -> List[str]:
        """Convert month indices to human-readable date strings."""
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
        ]
        current_year = datetime.now().year
        bloom_dates: List[str] = []
        for idx in bloom_months:
            month_num = idx + 1 if idx < 12 else 1
            year = current_year if month_num >= datetime.now().month else current_year + 1
            bloom_dates.append(f"{month_names[idx]} {year}")
        return bloom_dates

    @staticmethod
    def _get_empty_result(region: str) -> Dict:
        return {
            'data_source': 'None',
            'processed_at': datetime.now().isoformat(),
            'region': region,
            'bloom_months': [],
            'bloom_scores': [],
            'bloom_dates': [],
            'bloom_area_km2': 0,
            'bloom_percentage': 0,
            'error': 'No data available',
        }

    @staticmethod
    def _empty_bloom_area(ndwi_threshold: float, ndvi_threshold: float) -> Dict:
        return {
            'bloom_area_km2': 0.0,
            'total_counties': 0,
            'avg_bloom_percentage': 0.0,
            'ndwi_threshold': ndwi_threshold,
            'ndvi_threshold': ndvi_threshold,
            'timestamp': datetime.now().isoformat(),
            'method': 'No data',
        }

    # ------------------------------------------------------------------ #
    #  Region summary
    # ------------------------------------------------------------------ #

    def get_region_summary(self, region: str = 'kenya') -> Dict:
        bloom_data = self.detect_bloom_events(region)
        return {
            'region': region,
            'data_source': bloom_data.get('data_source'),
            'health_score': bloom_data.get('health_score', 0),
            'num_bloom_events': len(bloom_data.get('bloom_months', [])),
            'next_bloom': bloom_data['bloom_dates'][0] if bloom_data.get('bloom_dates') else 'Unknown',
            'bloom_area_km2': bloom_data.get('bloom_area_km2', 0),
            'avg_bloom_percentage': bloom_data.get('avg_bloom_percentage', 0),
            'updated_at': bloom_data.get('processed_at'),
        }

    # ------------------------------------------------------------------ #
    #  Synthetic fallbacks (demo / no-data mode)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _generate_synthetic_historical_data(months_back: int) -> Dict:
        dates, ndvi, ndwi, rain, temp = [], [], [], [], []
        for i in range(months_back):
            dt = datetime.now() - timedelta(days=30 * i)
            dates.append(dt.strftime('%Y-%m-%d'))
            month = dt.month
            if 2 <= month <= 5 or 9 <= month <= 11:
                ndvi.append(np.random.uniform(0.4, 0.8))
            else:
                ndvi.append(np.random.uniform(0.2, 0.5))
            ndwi.append(np.random.uniform(0.1, 0.6))
            if 2 <= month <= 5:
                rain.append(np.random.uniform(50, 200))
            elif 9 <= month <= 11:
                rain.append(np.random.uniform(30, 120))
            else:
                rain.append(np.random.uniform(0, 20))
            temp.append(np.random.uniform(18, 28))

        dates.reverse(); ndvi.reverse(); ndwi.reverse()
        rain.reverse(); temp.reverse()

        return {
            'time_series': {
                'dates': dates, 'ndvi_values': ndvi, 'ndwi_values': ndwi,
                'rainfall_values': rain, 'temperature_values': temp,
                'data_points': months_back,
            },
            'statistics': {
                'ndvi_mean': float(np.mean(ndvi)),
                'ndvi_std': float(np.std(ndvi)),
                'rainfall_total': float(np.sum(rain)),
                'temperature_avg': float(np.mean(temp)),
            },
            'period_months': months_back,
            'data_source': 'Synthetic demo data',
            'processed_at': datetime.now().isoformat(),
        }

    @staticmethod
    def _generate_synthetic_ml_data(include_weather: bool) -> Dict:
        n = 100
        ndvi = np.random.uniform(0.1, 0.9, n)
        ndwi = np.random.uniform(0.0, 0.7, n)
        features = [ndvi, ndwi]
        names = ['ndvi', 'ndwi']
        if include_weather:
            features.extend([np.random.uniform(0, 150, n), np.random.uniform(15, 30, n)])
            names.extend(['rainfall_mm', 'temperature_c'])
        X = np.array(features).T
        y = ((ndwi > NDWI_BLOOM_THRESHOLD) & (ndvi > NDVI_VEGETATION_THRESHOLD)).astype(int)
        bc = int(np.sum(y == 1))
        return {
            'features': X, 'labels': y,
            'dates': [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(n)],
            'feature_names': names, 'n_samples': n, 'n_features': X.shape[1],
            'bloom_count': bc, 'no_bloom_count': n - bc,
            'class_balance': float(bc / n),
            'thresholds': {'ndwi': NDWI_BLOOM_THRESHOLD, 'ndvi': NDVI_VEGETATION_THRESHOLD},
            'include_weather': include_weather,
            'prepared_at': datetime.now().isoformat(),
            'data_source': 'Synthetic demo data',
        }

    @staticmethod
    def _generate_synthetic_time_series(data_type: str, months: int) -> Dict:
        dates = [(datetime.now() - timedelta(days=30 * i)).strftime('%Y-%m-%d') for i in range(months)]
        dates.reverse()
        cfg = {
            'ndvi': (0.2, 0.8, 'NDVI', 'green'),
            'ndwi': (0.1, 0.6, 'NDWI', 'blue'),
            'rainfall': (0, 150, 'Rainfall (mm)', 'lightblue'),
            'temperature': (18, 28, 'Temperature (°C)', 'red'),
        }
        lo, hi, ylabel, color = cfg.get(data_type, (0, 1, data_type, 'grey'))
        values = [np.random.uniform(lo, hi) for _ in range(months)]
        return {
            'data_type': data_type, 'dates': dates, 'values': values,
            'ylabel': ylabel, 'color': color, 'n_points': months,
            'mean_value': float(np.mean(values)),
            'min_value': float(np.min(values)),
            'max_value': float(np.max(values)),
            'period_months': months,
            'generated_at': datetime.now().isoformat(),
            'data_source': 'Synthetic demo data',
        }


# ------------------------------------------------------------------ #
#  Self-test
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    print("🌸 Bloom Processor Test (PostgreSQL mode)")
    print("=" * 60)

    processor = BloomProcessor()

    print("\n🧮 Bloom area computation...")
    bloom_areas = processor.compute_bloom_areas()
    print(f"  Area: {bloom_areas.get('bloom_area_km2', 0):.2f} km²")
    print(f"  Method: {bloom_areas.get('method', 'N/A')}")

    print("\n📈 Historical data aggregation...")
    hist = processor.aggregate_historical_data(months_back=6)
    if 'error' not in hist:
        print(f"  Data points: {hist['time_series']['data_points']}")
        print(f"  Source: {hist['data_source']}")
        print(f"  NDVI mean: {hist['statistics']['ndvi_mean']:.3f}")
    else:
        print(f"  Error: {hist['error']}")

    print("\n🤖 ML training data...")
    ml = processor.prepare_ml_training_data()
    if 'error' not in ml:
        print(f"  Samples: {ml['n_samples']}, Features: {ml['n_features']}")
        print(f"  Bloom: {ml['bloom_count']}, No-bloom: {ml['no_bloom_count']}")

    print("\n🔍 Bloom detection...")
    results = processor.detect_bloom_events('kenya')
    print(f"  Source: {results.get('data_source')}")
    print(f"  Health: {results.get('health_score', 0):.1f}/100")
    print(f"  Bloom events: {len(results.get('bloom_months', []))}")

    print("\n✅ Bloom Processor test complete!")





