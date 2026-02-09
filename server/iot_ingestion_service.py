"""
IoT Data Ingestion Service for Smart Shamba Platform
Handles MQTT subscriptions and REST API ingestion from ESP32 sensors.

Transport options:
    1. MQTT (via EMQX broker) — real-time streaming
    2. REST POST /api/iot/ingest — batch or single reading
    3. REST POST /api/iot/ingest/batch — high-throughput batch

ESP32 publishes JSON to MQTT topics:
    shamba/{farm_id}/{device_id}/telemetry

Example payload:
    {
        "device_id": "esp32-001",
        "farm_id": 1,
        "temperature_c": 26.5,
        "humidity_pct": 72.3,
        "soil_moisture_pct": 45.2,
        "soil_ph": 6.8,
        "battery_pct": 87.0,
        "rssi_dbm": -65
    }
"""

import os
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Optional MQTT client
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt not installed — MQTT ingestion disabled. "
                    "Install: pip install paho-mqtt")

# Raw DB access for TimescaleDB-specific SQL
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from database.postgres_service import PostgresService


class IoTIngestionService:
    """
    IoT data ingestion from ESP32 devices via MQTT or REST.
    Writes to the sensor_readings table via PostgresService.
    """

    def __init__(self, db_service: Optional[PostgresService] = None):
        self.db = db_service or PostgresService()

        # MQTT config
        self.mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.mqtt_username = os.getenv("MQTT_USERNAME", "")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "")
        self.mqtt_topic = os.getenv("MQTT_TOPIC", "shamba/#")

        self.mqtt_client: Optional[mqtt.Client] = None  # type: ignore
        self._running = False

        # Anomaly thresholds
        self.thresholds = {
            "temperature_c": {"min": -5, "max": 55},
            "humidity_pct": {"min": 0, "max": 100},
            "soil_moisture_pct": {"min": 0, "max": 100},
            "soil_ph": {"min": 3.0, "max": 10.0},
            "battery_pct": {"min": 0, "max": 100},
        }

    # ------------------------------------------------------------------ #
    # REST ingestion (single reading)
    # ------------------------------------------------------------------ #

    def ingest_reading(self, payload: Dict) -> Dict:
        """
        Ingest a single sensor reading from REST POST.

        Required fields: farm_id, device_id
        Optional fields: temperature_c, humidity_pct, soil_moisture_pct,
                         soil_ph, light_lux, rainfall_mm, battery_pct, etc.
        """
        farm_id = payload.get("farm_id")
        device_id = payload.get("device_id")

        if not farm_id or not device_id:
            return {"success": False, "error": "farm_id and device_id are required"}

        # Validate ranges
        anomalies = self._check_anomalies(payload)

        # Save to database
        ok = self.db.save_sensor_reading(payload)

        result = {
            "success": ok,
            "device_id": device_id,
            "farm_id": farm_id,
            "ts": datetime.utcnow().isoformat(),
        }
        if anomalies:
            result["anomalies"] = anomalies

        return result

    # ------------------------------------------------------------------ #
    # REST ingestion (batch)
    # ------------------------------------------------------------------ #

    def ingest_batch(self, readings: List[Dict]) -> Dict:
        """
        Ingest a batch of sensor readings.
        Returns count of successfully inserted readings.
        """
        if not readings:
            return {"success": False, "error": "Empty batch", "inserted": 0}

        # Validate each reading has required fields
        valid = [r for r in readings if r.get("farm_id") and r.get("device_id")]
        inserted = self.db.save_sensor_readings_batch(valid)

        return {
            "success": inserted > 0,
            "total": len(readings),
            "valid": len(valid),
            "inserted": inserted,
        }

    # ------------------------------------------------------------------ #
    # Anomaly detection
    # ------------------------------------------------------------------ #

    def _check_anomalies(self, reading: Dict) -> List[Dict]:
        """Check sensor values against thresholds."""
        anomalies = []
        for field, limits in self.thresholds.items():
            value = reading.get(field)
            if value is not None:
                if value < limits["min"] or value > limits["max"]:
                    anomalies.append({
                        "field": field,
                        "value": value,
                        "min": limits["min"],
                        "max": limits["max"],
                        "severity": "warning" if abs(value) < limits["max"] * 1.5 else "critical",
                    })
        # Battery low alert
        battery = reading.get("battery_pct")
        if battery is not None and battery < 15:
            anomalies.append({
                "field": "battery_pct",
                "value": battery,
                "severity": "warning",
                "message": f"Battery low: {battery}%",
            })
        return anomalies

    # ------------------------------------------------------------------ #
    # Get recent readings for a farm
    # ------------------------------------------------------------------ #

    def get_farm_readings(self, farm_id: int, hours: int = 24,
                          device_id: Optional[str] = None) -> List[Dict]:
        """Get recent sensor data for a specific farm."""
        return self.db.get_sensor_readings(farm_id, hours=hours, device_id=device_id)

    # ------------------------------------------------------------------ #
    # TimescaleDB time_bucket aggregations
    # ------------------------------------------------------------------ #

    def _get_raw_conn(self):
        """Get a raw psycopg2 connection for TimescaleDB SQL."""
        if not PSYCOPG2_AVAILABLE:
            return None
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        db = os.getenv("DB_NAME", "smart-shamba")
        user = os.getenv("DB_USER", "geoffreyyogo")
        pw = os.getenv("DB_PASSWORD", "och13ng")
        return psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pw)  # type: ignore[possibly-undefined]

    def get_hourly_averages(
        self, farm_id: int, hours: int = 48, device_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get hourly averages using TimescaleDB time_bucket.
        Returns aggregated temperature, humidity, soil_moisture per hour.
        """
        conn = self._get_raw_conn()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            sql = """
                SELECT
                    time_bucket('1 hour', ts) AS bucket,
                    device_id,
                    AVG(temperature_c)      AS avg_temp,
                    AVG(humidity_pct)        AS avg_humidity,
                    AVG(soil_moisture_pct)   AS avg_soil_moisture,
                    AVG(soil_ph)             AS avg_ph,
                    MIN(temperature_c)       AS min_temp,
                    MAX(temperature_c)       AS max_temp,
                    COUNT(*)                 AS reading_count
                FROM sensor_readings
                WHERE farm_id = %s AND ts >= NOW() - INTERVAL '%s hours'
            """
            params: list = [farm_id, hours]
            if device_id:
                sql += " AND device_id = %s"
                params.append(device_id)
            sql += " GROUP BY bucket, device_id ORDER BY bucket DESC"
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]  # type: ignore[union-attr]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            # Serialize datetimes
            for r in rows:
                if r.get("bucket"):
                    r["bucket"] = r["bucket"].isoformat()
                for k in ("avg_temp", "avg_humidity", "avg_soil_moisture", "avg_ph", "min_temp", "max_temp"):
                    if r.get(k) is not None:
                        r[k] = round(float(r[k]), 2)
            return rows
        except Exception as e:
            logger.error(f"Error getting hourly averages: {e}")
            return []
        finally:
            conn.close()

    def get_daily_summary(
        self, farm_id: int, days: int = 30, device_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Daily summary using time_bucket('1 day').
        """
        conn = self._get_raw_conn()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            sql = """
                SELECT
                    time_bucket('1 day', ts) AS day,
                    device_id,
                    AVG(temperature_c)       AS avg_temp,
                    MIN(temperature_c)       AS min_temp,
                    MAX(temperature_c)       AS max_temp,
                    AVG(humidity_pct)        AS avg_humidity,
                    AVG(soil_moisture_pct)   AS avg_soil_moisture,
                    AVG(soil_ph)             AS avg_ph,
                    SUM(rainfall_mm)         AS total_rainfall,
                    MIN(battery_pct)         AS min_battery,
                    COUNT(*)                 AS reading_count
                FROM sensor_readings
                WHERE farm_id = %s AND ts >= NOW() - INTERVAL '%s days'
            """
            params: list = [farm_id, days]
            if device_id:
                sql += " AND device_id = %s"
                params.append(device_id)
            sql += " GROUP BY day, device_id ORDER BY day DESC"
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]  # type: ignore[union-attr]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            for r in rows:
                if r.get("day"):
                    r["day"] = r["day"].isoformat()
                for k in list(r.keys()):
                    if r[k] is not None and isinstance(r[k], (float,)):
                        r[k] = round(r[k], 2)
            return rows
        except Exception as e:
            logger.error(f"Error getting daily summary: {e}")
            return []
        finally:
            conn.close()

    def get_latest_per_device(self, farm_id: int) -> List[Dict]:
        """Get the most recent reading per device using TimescaleDB last()."""
        conn = self._get_raw_conn()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT ON (device_id)
                    device_id,
                    ts,
                    temperature_c, humidity_pct, soil_moisture_pct,
                    soil_ph, battery_pct, rssi_dbm
                FROM sensor_readings
                WHERE farm_id = %s
                ORDER BY device_id, ts DESC
            """, (farm_id,))
            cols = [d[0] for d in cur.description]  # type: ignore[union-attr]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            for r in rows:
                if r.get("ts"):
                    r["ts"] = r["ts"].isoformat()
            return rows
        except Exception as e:
            logger.error(f"Error getting latest readings: {e}")
            return []
        finally:
            conn.close()

    def setup_continuous_aggregates(self):
        """
        Create TimescaleDB continuous aggregates for common queries.
        Call once at application startup.
        """
        conn = self._get_raw_conn()
        if not conn:
            logger.warning("Cannot setup continuous aggregates — no psycopg2")
            return
        try:
            cur = conn.cursor()

            # Hourly aggregate
            cur.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_hourly
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 hour', ts) AS bucket,
                    farm_id,
                    device_id,
                    AVG(temperature_c)      AS avg_temp,
                    AVG(humidity_pct)        AS avg_humidity,
                    AVG(soil_moisture_pct)   AS avg_soil_moisture,
                    AVG(soil_ph)             AS avg_ph,
                    SUM(rainfall_mm)         AS total_rainfall,
                    MIN(battery_pct)         AS min_battery,
                    COUNT(*)                 AS reading_count
                FROM sensor_readings
                GROUP BY bucket, farm_id, device_id
                WITH NO DATA;
            """)

            # Daily aggregate
            cur.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_daily
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 day', ts) AS bucket,
                    farm_id,
                    device_id,
                    AVG(temperature_c)      AS avg_temp,
                    MIN(temperature_c)      AS min_temp,
                    MAX(temperature_c)      AS max_temp,
                    AVG(humidity_pct)        AS avg_humidity,
                    AVG(soil_moisture_pct)   AS avg_soil_moisture,
                    SUM(rainfall_mm)         AS total_rainfall,
                    MIN(battery_pct)         AS min_battery,
                    COUNT(*)                 AS reading_count
                FROM sensor_readings
                GROUP BY bucket, farm_id, device_id
                WITH NO DATA;
            """)

            # Add refresh policies — refresh every 30 min for hourly, 1 hour for daily
            cur.execute("""
                SELECT add_continuous_aggregate_policy('sensor_hourly',
                    start_offset => INTERVAL '3 hours',
                    end_offset   => INTERVAL '1 hour',
                    schedule_interval => INTERVAL '30 minutes',
                    if_not_exists => true);
            """)
            cur.execute("""
                SELECT add_continuous_aggregate_policy('sensor_daily',
                    start_offset => INTERVAL '3 days',
                    end_offset   => INTERVAL '1 day',
                    schedule_interval => INTERVAL '1 hour',
                    if_not_exists => true);
            """)

            conn.commit()
            logger.info("✓ TimescaleDB continuous aggregates configured")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error setting up continuous aggregates: {e}")
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # MQTT subscriber
    # ------------------------------------------------------------------ #

    def start_mqtt(self):
        """Start MQTT subscriber in a background thread."""
        if not MQTT_AVAILABLE:
            logger.warning("Cannot start MQTT — paho-mqtt not installed")
            return False

        if self._running:
            logger.info("MQTT already running")
            return True

        try:
            self.mqtt_client = mqtt.Client(  # type: ignore[possibly-undefined]
                client_id="shamba-iot-ingestor",
                protocol=mqtt.MQTTv311,  # type: ignore[possibly-undefined]
            )
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_message = self._on_message
            self.mqtt_client.on_disconnect = self._on_disconnect

            if self.mqtt_username:
                self.mqtt_client.username_pw_set(
                    self.mqtt_username, self.mqtt_password
                )

            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            self._running = True
            self.mqtt_client.loop_start()
            logger.info(
                f"✓ MQTT subscriber started: {self.mqtt_broker}:{self.mqtt_port} "
                f"topic={self.mqtt_topic}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to start MQTT: {e}")
            self._running = False
            return False

    def stop_mqtt(self):
        """Stop MQTT subscriber."""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self._running = False
            logger.info("MQTT subscriber stopped")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"✓ MQTT connected, subscribing to {self.mqtt_topic}")
            client.subscribe(self.mqtt_topic)
        else:
            logger.error(f"MQTT connection failed: rc={rc}")

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT message."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))

            # Extract farm_id and device_id from topic if not in payload
            # Topic format: shamba/{farm_id}/{device_id}/telemetry
            parts = msg.topic.split("/")
            if len(parts) >= 3:
                payload.setdefault("farm_id", int(parts[1]))
                payload.setdefault("device_id", parts[2])

            result = self.ingest_reading(payload)
            if result.get("anomalies"):
                logger.warning(
                    f"IoT anomaly from {payload.get('device_id')}: "
                    f"{result['anomalies']}"
                )
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from MQTT: {msg.topic}")
        except Exception as e:
            logger.error(f"MQTT message processing error: {e}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"MQTT disconnected unexpectedly: rc={rc}")
            self._running = False


# Quick test
if __name__ == "__main__":
    print("🌾 Smart Shamba — IoT Ingestion Service Test")
    print("=" * 60)

    svc = IoTIngestionService()

    # Test single reading
    result = svc.ingest_reading({
        "farm_id": 1,
        "device_id": "esp32-test-001",
        "temperature_c": 25.5,
        "humidity_pct": 68.0,
        "soil_moisture_pct": 42.0,
        "soil_ph": 6.5,
        "battery_pct": 92.0,
        "rssi_dbm": -55,
    })
    print(f"Single ingest: {result}")

    # Test batch
    batch_result = svc.ingest_batch([
        {"farm_id": 1, "device_id": "esp32-test-001", "temperature_c": 26.0, "humidity_pct": 70.0},
        {"farm_id": 1, "device_id": "esp32-test-002", "soil_moisture_pct": 38.0, "soil_ph": 7.0},
    ])
    print(f"Batch ingest: {batch_result}")

    # Test anomaly
    anomaly = svc.ingest_reading({
        "farm_id": 1,
        "device_id": "esp32-test-001",
        "temperature_c": 60.0,  # Too high!
        "battery_pct": 5.0,      # Low battery!
    })
    print(f"Anomaly test: {anomaly}")

    print("\n✓ IoT ingestion service test completed!")
