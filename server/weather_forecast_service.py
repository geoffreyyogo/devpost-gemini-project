"""
Weather Forecast Service for Smart Shamba
Uses the Google Weather API (Maps Platform) to provide sub-county-level
weather forecasts for agricultural planning and bloom prediction.

Prerequisites:
  1. Enable "Weather API" in Google Cloud Console for your project
  2. Create a Maps Platform API key (or reuse an existing one)
  3. Set env var: GOOGLE_WEATHER_API_KEY=<your-key>

Endpoints used:
  - GET /v1/forecast/days:lookup   → 10-day daily forecast
  - GET /v1/forecast/hours:lookup  → 240-hour hourly forecast
  - GET /v1/currentConditions:lookup → current weather
"""

import os
import logging
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Google Weather API base URL
WEATHER_BASE = "https://weather.googleapis.com/v1"


class WeatherForecastService:
    """Fetches and caches weather forecasts for Kenya sub-counties."""

    def __init__(self, api_key: str = None, db_service=None):
        """
        Args:
            api_key: Google Maps Platform API key with Weather API enabled.
                     Falls back to GOOGLE_WEATHER_API_KEY env var.
            db_service: Optional PostgresService to persist forecasts.
        """
        self.api_key = api_key or os.getenv("GOOGLE_WEATHER_API_KEY", "")
        self.db = db_service
        self._cache: Dict[str, Dict] = {}  # key: "lat,lon" -> forecast
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=6)  # Refresh forecasts every 6 hours

        if not self.api_key:
            logger.warning(
                "⚠ GOOGLE_WEATHER_API_KEY not set — weather forecasts will be unavailable. "
                "Enable the Weather API in Google Cloud Console and create a Maps Platform API key."
            )

        # Lazy import of sub-county coordinates
        try:
            from kenya_sub_counties import KENYA_SUB_COUNTIES
            self._sub_counties = KENYA_SUB_COUNTIES
        except ImportError:
            self._sub_counties = {}
            logger.warning("kenya_sub_counties not available — sub-county lookup disabled")

        logger.info(
            f"✓ Weather Forecast Service initialized "
            f"(API key={'set' if self.api_key else 'NOT set'})"
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def get_daily_forecast(
        self, lat: float, lon: float, days: int = 10
    ) -> Dict:
        """
        Get up to 10-day daily forecast for a location.

        Returns:
            Dict with daily forecasts including max/min temp, precipitation,
            humidity, wind speed, UV index, cloud cover.
        """
        if not self.api_key:
            return {"error": "Weather API key not configured"}

        cache_key = f"daily:{lat:.4f},{lon:.4f}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        url = f"{WEATHER_BASE}/forecast/days:lookup"
        params = {
            "key": self.api_key,
            "location.latitude": lat,
            "location.longitude": lon,
            "days": min(days, 10),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            forecast = self._parse_daily_forecast(data, lat, lon)
            self._set_cached(cache_key, forecast)
            return forecast

        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API HTTP error: {e.response.status_code} — {e.response.text[:300]}")
            return {"error": f"Weather API error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Weather forecast fetch failed: {e}")
            return {"error": str(e)}

    async def get_hourly_forecast(
        self, lat: float, lon: float, hours: int = 48
    ) -> Dict:
        """Get hourly forecast (up to 240 hours)."""
        if not self.api_key:
            return {"error": "Weather API key not configured"}

        cache_key = f"hourly:{lat:.4f},{lon:.4f}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        url = f"{WEATHER_BASE}/forecast/hours:lookup"
        params = {
            "key": self.api_key,
            "location.latitude": lat,
            "location.longitude": lon,
            "hours": min(hours, 240),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            forecast = self._parse_hourly_forecast(data, lat, lon)
            self._set_cached(cache_key, forecast)
            return forecast

        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API HTTP error: {e.response.status_code}")
            return {"error": f"Weather API error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Hourly forecast fetch failed: {e}")
            return {"error": str(e)}

    async def get_current_conditions(self, lat: float, lon: float) -> Dict:
        """Get current weather conditions for a location."""
        if not self.api_key:
            return {"error": "Weather API key not configured"}

        cache_key = f"current:{lat:.4f},{lon:.4f}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        url = f"{WEATHER_BASE}/currentConditions:lookup"
        params = {
            "key": self.api_key,
            "location.latitude": lat,
            "location.longitude": lon,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            conditions = self._parse_current_conditions(data, lat, lon)
            self._set_cached(cache_key, conditions)
            return conditions

        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API HTTP error: {e.response.status_code}")
            return {"error": f"Weather API error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Current conditions fetch failed: {e}")
            return {"error": str(e)}

    async def get_sub_county_forecast(
        self, county_id: str, sub_county_id: str
    ) -> Dict:
        """
        Get weather forecast for a specific sub-county by ID.
        Looks up coordinates from kenya_sub_counties.
        """
        county_data = self._sub_counties.get(county_id, {})
        sub_counties = county_data.get("sub_counties", {})
        sub_county = sub_counties.get(sub_county_id)

        if not sub_county:
            return {
                "error": f"Sub-county '{sub_county_id}' not found in '{county_id}'"
            }

        coords = sub_county.get("coordinates", {})
        lat = coords.get("lat")
        lon = coords.get("lon")

        if not lat or not lon:
            return {"error": f"No coordinates for sub-county '{sub_county_id}'"}

        forecast = await self.get_daily_forecast(lat, lon)
        forecast["county"] = county_data.get("county_name", county_id)
        forecast["sub_county"] = sub_county.get("name", sub_county_id)
        return forecast

    async def get_county_forecast(self, county_id: str) -> Dict:
        """
        Get weather forecast for all sub-counties in a county.
        Returns aggregated forecast + per-sub-county breakdown.
        """
        county_data = self._sub_counties.get(county_id, {})
        sub_counties = county_data.get("sub_counties", {})

        if not sub_counties:
            # Fallback: try kenya_counties_config for county center
            try:
                from kenya_counties_config import KENYA_COUNTIES
                county_info = KENYA_COUNTIES.get(county_id, {})
                coords = county_info.get("coordinates", {})
                if coords:
                    forecast = await self.get_daily_forecast(
                        coords["lat"], coords["lon"]
                    )
                    forecast["county"] = county_info.get("name", county_id)
                    return forecast
            except ImportError:
                pass
            return {"error": f"County '{county_id}' not found"}

        # Fetch for first 5 sub-counties to avoid rate limits
        results = {}
        tasks = []
        sub_ids = list(sub_counties.keys())[:5]

        for sc_id in sub_ids:
            sc = sub_counties[sc_id]
            coords = sc.get("coordinates", {})
            lat, lon = coords.get("lat"), coords.get("lon")
            if lat and lon:
                tasks.append((sc_id, sc.get("name", sc_id), lat, lon))

        # Fetch concurrently (with small stagger to avoid hitting limits)
        forecasts = []
        for sc_id, sc_name, lat, lon in tasks:
            fc = await self.get_daily_forecast(lat, lon)
            fc["sub_county"] = sc_name
            results[sc_id] = fc
            forecasts.append(fc)
            await asyncio.sleep(0.1)  # Small stagger

        # Aggregate: average of all sub-county forecasts
        aggregated = self._aggregate_forecasts(forecasts)
        aggregated["county"] = county_data.get("county_name", county_id)
        aggregated["sub_county_forecasts"] = results
        aggregated["sub_counties_sampled"] = len(results)
        aggregated["total_sub_counties"] = len(sub_counties)

        return aggregated

    async def get_agricultural_insights(
        self, lat: float, lon: float, crop: str = None
    ) -> Dict:
        """
        Generate agriculture-specific weather insights for a location.
        Combines daily forecast with farming advice.
        """
        forecast = await self.get_daily_forecast(lat, lon)
        if "error" in forecast:
            return forecast

        days = forecast.get("daily_forecasts", [])
        if not days:
            return {**forecast, "insights": []}

        insights = []

        # Analyse rainfall patterns
        total_rain_mm = sum(d.get("precipitation_mm", 0) for d in days)
        rainy_days = sum(1 for d in days if d.get("precipitation_probability", 0) > 50)

        if total_rain_mm > 100:
            insights.append({
                "type": "heavy_rain",
                "severity": "warning",
                "message": f"Heavy rainfall expected: {total_rain_mm:.0f}mm over {len(days)} days. "
                           "Consider drainage measures and delay fertiliser application.",
            })
        elif total_rain_mm > 30:
            insights.append({
                "type": "moderate_rain",
                "severity": "info",
                "message": f"Moderate rainfall expected: {total_rain_mm:.1f}mm over {len(days)} days. "
                           "Good conditions for crop growth; apply fertiliser before or between rains.",
            })
        elif total_rain_mm < 10 and len(days) >= 5:
            insights.append({
                "type": "dry_spell",
                "severity": "warning",
                "message": "Dry spell expected with <10mm rain over next 10 days. "
                           "Consider irrigation and mulching to conserve soil moisture.",
            })
        elif total_rain_mm < 20:
            insights.append({
                "type": "light_rain",
                "severity": "info",
                "message": f"Light rainfall expected: {total_rain_mm:.1f}mm over {len(days)} days. "
                           "Supplement with irrigation if soil moisture drops below optimal levels.",
            })

        # High temperature warnings
        max_temps = [d.get("max_temp_c", 0) for d in days]
        if max_temps and max(max_temps) > 35:
            insights.append({
                "type": "heat_stress",
                "severity": "alert",
                "message": f"High temperatures expected (up to {max(max_temps):.0f}°C). "
                           "Provide shade for sensitive crops and increase watering frequency.",
            })

        # Optimal planting windows
        if 10 < total_rain_mm < 80:
            good_planting_days = [
                d["date"] for d in days
                if 15 < d.get("max_temp_c", 0) < 32
                and d.get("precipitation_probability", 0) > 25
            ]
            if good_planting_days:
                insights.append({
                    "type": "planting_window",
                    "severity": "info",
                    "message": f"Good planting conditions expected on: {', '.join(good_planting_days[:3])}",
                })

        # Bloom risk assessment
        if total_rain_mm > 50 and any(d.get("humidity_pct", 0) > 80 for d in days):
            insights.append({
                "type": "bloom_risk",
                "severity": "warning",
                "message": "High moisture + humidity conditions favour algal bloom development. "
                           "Monitor water bodies and apply preventive measures.",
            })

        # Spray window (dry periods with low wind)
        spray_days = [
            d["date"] for d in days
            if d.get("precipitation_probability", 0) < 25
            and d.get("wind_speed_kmh", 0) < 20
        ]
        if spray_days:
            insights.append({
                "type": "spray_window",
                "severity": "info",
                "message": f"Optimal spray/fertiliser application days: {', '.join(spray_days[:3])}",
            })

        # High humidity warning (fungal disease risk)
        humid_days = [d["date"] for d in days if d.get("humidity_pct", 0) > 80]
        if len(humid_days) >= 3:
            insights.append({
                "type": "fungal_risk",
                "severity": "warning",
                "message": f"High humidity ({len(humid_days)} days above 80%) increases risk of "
                           "fungal diseases (blight, rust). Consider preventive fungicide application.",
            })

        return {
            **forecast,
            "insights": insights,
            "agriculture_summary": {
                "total_rain_10d_mm": total_rain_mm,
                "rainy_days": rainy_days,
                "max_temperature_c": max(max_temps) if max_temps else None,
                "min_temperature_c": min(d.get("min_temp_c", 0) for d in days) if days else None,
                "crop": crop,
            },
        }

    # ------------------------------------------------------------------ #
    # Parsing helpers
    # ------------------------------------------------------------------ #

    def _parse_daily_forecast(self, raw: Dict, lat: float, lon: float) -> Dict:
        """Parse Google Weather API daily forecast response."""
        days = []
        for day_data in raw.get("forecastDays", []):
            interval = day_data.get("interval", {})
            day_fc = day_data.get("daytimeForecast", {})
            night_fc = day_data.get("nighttimeForecast", {})

            # Temperature (at day level)
            max_temp = day_data.get("maxTemperature", {})
            min_temp = day_data.get("minTemperature", {})

            # Precipitation (inside daytime/nighttime forecasts)
            day_precip = day_fc.get("precipitation", {})
            night_precip = night_fc.get("precipitation", {})
            precip_prob = max(
                day_precip.get("probability", {}).get("percent", 0),
                night_precip.get("probability", {}).get("percent", 0),
            )
            precip_mm = (
                self._to_mm(day_precip.get("qpf", {}))
                + self._to_mm(night_precip.get("qpf", {}))
            )

            # Humidity — max of daytime and nighttime
            humidity = max(
                day_fc.get("relativeHumidity", 0),
                night_fc.get("relativeHumidity", 0),
            )

            # Wind (daytime forecast)
            wind = day_fc.get("wind", {})
            wind_speed = wind.get("speed", {})

            # UV and cloud cover (daytime forecast)
            uv_index = day_fc.get("uvIndex", 0)
            cloud_cover = day_fc.get("cloudCover", 0)

            # Weather condition (daytime forecast)
            wc = day_fc.get("weatherCondition", {})
            condition = wc.get("type", "UNKNOWN")
            desc_obj = wc.get("description", {})
            description = desc_obj.get("text", "") if isinstance(desc_obj, dict) else str(desc_obj)

            days.append({
                "date": interval.get("startTime", "")[:10],
                "max_temp_c": self._to_celsius(max_temp),
                "min_temp_c": self._to_celsius(min_temp),
                "precipitation_probability": precip_prob,
                "precipitation_mm": precip_mm,
                "humidity_pct": humidity,
                "wind_speed_kmh": self._to_kmh(wind_speed),
                "wind_direction": wind.get("direction", {}).get("cardinal", ""),
                "uv_index": uv_index,
                "cloud_cover_pct": cloud_cover,
                "condition": condition,
                "description": description,
            })

        return {
            "latitude": lat,
            "longitude": lon,
            "daily_forecasts": days,
            "forecast_days": len(days),
            "fetched_at": datetime.now().isoformat(),
            "source": "Google Weather API",
        }

    def _parse_hourly_forecast(self, raw: Dict, lat: float, lon: float) -> Dict:
        """Parse Google Weather API hourly forecast response."""
        hours = []
        for hour_data in raw.get("forecastHours", []):
            interval = hour_data.get("interval", {})
            temp = hour_data.get("temperature", {})
            precip = hour_data.get("precipitation", {})
            wind = hour_data.get("wind", {})

            hours.append({
                "datetime": interval.get("startTime", ""),
                "temp_c": self._to_celsius(temp),
                "precipitation_mm": self._to_mm(precip.get("qpf", {})),
                "precipitation_probability": precip.get("probability", {}).get("percent", 0),
                "humidity_pct": hour_data.get("relativeHumidity", 0),
                "wind_speed_kmh": self._to_kmh(wind.get("speed", {})),
                "cloud_cover_pct": hour_data.get("cloudCover", 0),
                "condition": hour_data.get("weatherCondition", {}).get("type", "UNKNOWN"),
            })

        return {
            "latitude": lat,
            "longitude": lon,
            "hourly_forecasts": hours,
            "forecast_hours": len(hours),
            "fetched_at": datetime.now().isoformat(),
            "source": "Google Weather API",
        }

    def _parse_current_conditions(self, raw: Dict, lat: float, lon: float) -> Dict:
        """Parse Google Weather API current conditions response."""
        temp = raw.get("temperature", {})
        feels = raw.get("feelsLikeTemperature", {})
        wind = raw.get("wind", {})
        precip = raw.get("precipitation", {})
        wc = raw.get("weatherCondition", {})
        desc_obj = wc.get("description", {})
        description = desc_obj.get("text", "") if isinstance(desc_obj, dict) else str(desc_obj)

        return {
            "latitude": lat,
            "longitude": lon,
            "temperature_c": self._to_celsius(temp),
            "feels_like_c": self._to_celsius(feels),
            "humidity_pct": raw.get("relativeHumidity", 0),
            "wind_speed_kmh": self._to_kmh(wind.get("speed", {})),
            "wind_direction": wind.get("direction", {}).get("cardinal", ""),
            "precipitation_mm": self._to_mm(precip.get("qpf", {})),
            "cloud_cover_pct": raw.get("cloudCover", 0),
            "uv_index": raw.get("uvIndex", 0),
            "condition": wc.get("type", "UNKNOWN"),
            "description": description,
            "fetched_at": datetime.now().isoformat(),
            "source": "Google Weather API",
        }

    def _aggregate_forecasts(self, forecasts: List[Dict]) -> Dict:
        """Average multiple sub-county forecasts into a county-level summary."""
        all_days: Dict[str, List[Dict]] = {}
        for fc in forecasts:
            for day in fc.get("daily_forecasts", []):
                date = day.get("date", "")
                if date:
                    all_days.setdefault(date, []).append(day)

        aggregated_days = []
        for date in sorted(all_days.keys()):
            day_list = all_days[date]
            n = len(day_list)
            aggregated_days.append({
                "date": date,
                "max_temp_c": sum(d.get("max_temp_c", 0) for d in day_list) / n,
                "min_temp_c": sum(d.get("min_temp_c", 0) for d in day_list) / n,
                "precipitation_probability": sum(d.get("precipitation_probability", 0) for d in day_list) / n,
                "precipitation_mm": sum(d.get("precipitation_mm", 0) for d in day_list) / n,
                "humidity_pct": sum(d.get("humidity_pct", 0) for d in day_list) / n,
                "wind_speed_kmh": sum(d.get("wind_speed_kmh", 0) for d in day_list) / n,
            })

        return {
            "daily_forecasts": aggregated_days,
            "forecast_days": len(aggregated_days),
            "fetched_at": datetime.now().isoformat(),
            "source": "Google Weather API (aggregated)",
        }

    # ------------------------------------------------------------------ #
    # Unit conversion helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _to_celsius(temp_obj: Dict) -> float:
        """Extract Celsius from a Temperature object. If Fahrenheit, convert."""
        if not temp_obj:
            return 0.0
        # Google Weather API returns celsius by default
        c = temp_obj.get("celsius") or temp_obj.get("degrees")
        if c is not None:
            return float(c)
        f = temp_obj.get("fahrenheit")
        if f is not None:
            return (float(f) - 32) * 5 / 9
        return 0.0

    @staticmethod
    def _to_mm(qpf_obj: Dict) -> float:
        """Extract millimetres from a QPF object."""
        if not qpf_obj:
            return 0.0
        mm = qpf_obj.get("millimeters") or qpf_obj.get("quantity")
        return float(mm) if mm else 0.0

    @staticmethod
    def _to_kmh(speed_obj: Dict) -> float:
        """Extract km/h from a Speed object."""
        if not speed_obj:
            return 0.0
        kmh = speed_obj.get("kilometersPerHour") or speed_obj.get("value")
        return float(kmh) if kmh else 0.0

    # ------------------------------------------------------------------ #
    # Cache management
    # ------------------------------------------------------------------ #

    def _get_cached(self, key: str) -> Optional[Dict]:
        """Return cached result if still fresh."""
        if key in self._cache:
            if datetime.now() - self._cache_time[key] < self._cache_ttl:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._cache_time[key]
        return None

    def _set_cached(self, key: str, data: Dict):
        """Store result in cache."""
        self._cache[key] = data
        self._cache_time[key] = datetime.now()

    def clear_cache(self):
        """Clear all cached forecasts."""
        self._cache.clear()
        self._cache_time.clear()
        logger.info("Weather forecast cache cleared")
