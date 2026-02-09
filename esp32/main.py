"""
ESP32 Smart Shamba — MicroPython Firmware
=========================================

Reads from sensor array and publishes to MQTT (or REST fallback).
Captures weekly camera images of crop canopy for disease detection.

Hardware:
    - ESP32-CAM (AI-Thinker) or ESP32-WROVER with external camera
    - DHT22: temperature + humidity
    - Capacitive soil moisture sensor (analog)
    - Soil pH analog sensor
    - NPK RS485 Modbus sensor (optional)
    - BMP280/BME280: atmospheric pressure (I2C)
    - LiPo battery with voltage divider

Setup:
    1. Flash MicroPython firmware to ESP32
    2. Upload config.py + main.py via ampy/Thonny/mpremote
    3. Register device via POST /api/iot/devices/register
    4. Update config.py with assigned DEVICE_ID and FARM_ID
    5. Reboot — it auto-connects WiFi → MQTT and starts streaming

MQTT Topics:
    shamba/{farm_id}/{device_id}/telemetry  → JSON sensor readings
    REST fallback: POST /api/iot/ingest     → same JSON
    REST image:    POST /api/iot/image/upload → multipart JPEG
"""

import machine
import time
import json
import gc
import sys

# ── Import config ────────────────────────────────────────────────────
try:
    from config import *
except ImportError:
    print("ERROR: config.py not found. Copy config.py to the device first.")
    sys.exit(1)

# ── WiFi ─────────────────────────────────────────────────────────────
import network

def connect_wifi(ssid, password, timeout=15):
    """Connect to WiFi. Returns True on success."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print(f"WiFi already connected: {wlan.ifconfig()[0]}")
        return True
    print(f"Connecting to WiFi '{ssid}'...")
    wlan.connect(ssid, password)
    start = time.time()
    while not wlan.isconnected():
        if time.time() - start > timeout:
            print("WiFi connection timed out!")
            return False
        time.sleep(0.5)
    ip = wlan.ifconfig()[0]
    print(f"WiFi connected: {ip}")
    return True


# ── Sensors ──────────────────────────────────────────────────────────

class SensorArray:
    """Read all connected sensors and return a dict payload."""

    def __init__(self):
        # ADC for soil moisture
        self.adc_moisture = machine.ADC(machine.Pin(PIN_SOIL_MOISTURE))
        self.adc_moisture.atten(machine.ADC.ATTN_11DB)   # 0–3.3V range
        self.adc_moisture.width(machine.ADC.WIDTH_12BIT)  # 0–4095

        # ADC for soil pH
        self.adc_ph = machine.ADC(machine.Pin(PIN_SOIL_PH))
        self.adc_ph.atten(machine.ADC.ATTN_11DB)
        self.adc_ph.width(machine.ADC.WIDTH_12BIT)

        # ADC for battery
        self.adc_battery = machine.ADC(machine.Pin(PIN_BATTERY))
        self.adc_battery.atten(machine.ADC.ATTN_11DB)
        self.adc_battery.width(machine.ADC.WIDTH_12BIT)

        # DHT22 (temperature + humidity)
        try:
            import dht
            self.dht = dht.DHT22(machine.Pin(PIN_DHT22))
            self._dht_ok = True
        except Exception:
            self._dht_ok = False
            print("DHT22 not available")

        # BMP280 (pressure) via I2C
        self._bmp = None
        try:
            self.i2c = machine.I2C(0, sda=machine.Pin(PIN_I2C_SDA),
                                      scl=machine.Pin(PIN_I2C_SCL), freq=400000)
            # Try to detect BMP280 on I2C bus
            devices = self.i2c.scan()
            if 0x76 in devices or 0x77 in devices:
                self._init_bmp280()
        except Exception as e:
            print(f"I2C/BMP280 not available: {e}")

        # NPK Modbus via UART (optional)
        self._npk_uart = None
        try:
            self._npk_uart = machine.UART(2, baudrate=9600,
                                           tx=machine.Pin(PIN_NPK_TX),
                                           rx=machine.Pin(PIN_NPK_RX))
            print("NPK UART initialized")
        except Exception:
            print("NPK sensor UART not available")

    def _init_bmp280(self):
        """Minimal BMP280 init (I2C address 0x76 or 0x77)."""
        # Try common BMP280 MicroPython driver
        try:
            from bmp280 import BMP280
            self._bmp = BMP280(self.i2c)
            print("BMP280 initialized")
        except ImportError:
            # Fallback: manual register read
            self._bmp = None
            print("bmp280 module not installed — pressure disabled. "
                  "Upload bmp280.py driver to /lib/")

    def read_all(self):
        """
        Read all sensors. Returns dict matching server SensorReadingPayload.
        Skips unavailable sensors gracefully.
        """
        payload = {
            "device_id": DEVICE_ID,
            "farm_id": FARM_ID,
        }

        # ── DHT22: temperature + humidity ────────────────────────────
        if self._dht_ok:
            try:
                self.dht.measure()
                time.sleep_ms(100)
                payload["temperature_c"] = round(self.dht.temperature(), 1)
                payload["humidity_pct"]  = round(self.dht.humidity(), 1)
            except Exception as e:
                print(f"DHT22 read error: {e}")

        # ── Soil moisture (capacitive analog) ────────────────────────
        try:
            raw = self._avg_adc(self.adc_moisture, samples=10)
            # Map ADC range to 0-100%
            moisture = self._map_range(raw, SOIL_MOISTURE_DRY, SOIL_MOISTURE_WET, 0, 100)
            payload["soil_moisture_pct"] = round(max(0, min(100, moisture)), 1)
        except Exception as e:
            print(f"Soil moisture read error: {e}")

        # ── Soil pH (analog) ─────────────────────────────────────────
        try:
            raw = self._avg_adc(self.adc_ph, samples=10)
            voltage = (raw / 4095.0) * 3.3
            ph = 7.0 + (voltage - PH_VOLTAGE_AT_7) / PH_VOLTAGE_SLOPE
            payload["soil_ph"] = round(max(0, min(14, ph)), 2)
        except Exception as e:
            print(f"Soil pH read error: {e}")

        # ── BMP280: atmospheric pressure ─────────────────────────────
        if self._bmp:
            try:
                payload["pressure_hpa"] = round(self._bmp.pressure / 100, 1)
                # Can also get temperature as cross-check
                bmp_temp = round(self._bmp.temperature, 1)
                if "temperature_c" not in payload:
                    payload["temperature_c"] = bmp_temp
            except Exception as e:
                print(f"BMP280 read error: {e}")

        # ── NPK (RS485 Modbus) ───────────────────────────────────────
        if self._npk_uart:
            try:
                npk = self._read_npk()
                if npk:
                    payload["soil_nitrogen"]   = npk.get("N")
                    payload["soil_phosphorus"] = npk.get("P")
                    payload["soil_potassium"]  = npk.get("K")
            except Exception as e:
                print(f"NPK read error: {e}")

        # ── Battery voltage ──────────────────────────────────────────
        try:
            raw = self._avg_adc(self.adc_battery, samples=5)
            voltage = (raw / 4095.0) * 3.3 * BATTERY_VDIV_RATIO
            pct = ((voltage - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V)) * 100
            payload["battery_pct"] = round(max(0, min(100, pct)), 1)
        except Exception as e:
            print(f"Battery read error: {e}")

        # ── WiFi RSSI ────────────────────────────────────────────────
        try:
            wlan = network.WLAN(network.STA_IF)
            if wlan.isconnected():
                rssi = wlan.status("rssi")
                payload["rssi_dbm"] = rssi
        except Exception:
            pass

        return payload

    def _avg_adc(self, adc, samples=10):
        """Take multiple ADC samples and return average (reduces noise)."""
        total = 0
        for _ in range(samples):
            total += adc.read()
            time.sleep_ms(5)
        return total // samples

    @staticmethod
    def _map_range(x, in_min, in_max, out_min, out_max):
        """Map a value from one range to another."""
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def _read_npk(self):
        """
        Read NPK from RS485 Modbus sensor.
        Standard query: address 0x01, function 0x03, register 0x001E, count 3
        Returns {N, P, K} in mg/kg or None.
        """
        if not self._npk_uart:
            return None
        # Modbus RTU frame: addr, func, reg_hi, reg_lo, count_hi, count_lo, crc_lo, crc_hi
        queries = {
            "N": bytes([0x01, 0x03, 0x00, 0x1E, 0x00, 0x01, 0xE4, 0x0C]),
            "P": bytes([0x01, 0x03, 0x00, 0x1F, 0x00, 0x01, 0xB5, 0xCC]),
            "K": bytes([0x01, 0x03, 0x00, 0x20, 0x00, 0x01, 0x85, 0xC0]),
        }
        result = {}
        for nutrient, cmd in queries.items():
            self._npk_uart.write(cmd)
            time.sleep_ms(200)
            resp = self._npk_uart.read(7)
            if resp and len(resp) >= 5:
                # Response: addr, func, byte_count, data_hi, data_lo, crc_lo, crc_hi
                value = (resp[3] << 8) | resp[4]
                result[nutrient] = value
        return result if result else None


# ── Camera ───────────────────────────────────────────────────────────

def capture_image():
    """
    Capture a JPEG image from ESP32-CAM.
    Returns bytes or None if camera not available.
    """
    if not CAMERA_ENABLED:
        return None
    try:
        import camera
        camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM,
                    xclk_freq=camera.XCLK_20MHz)
        camera.framesize(camera.FRAME_VGA)      # 640x480
        camera.quality(IMAGE_QUALITY)
        # Discard first frame (often overexposed)
        _ = camera.capture()
        time.sleep_ms(200)
        img = camera.capture()
        camera.deinit()
        return img
    except ImportError:
        print("camera module not available — not an ESP32-CAM board?")
        return None
    except Exception as e:
        print(f"Camera capture error: {e}")
        try:
            camera.deinit()
        except Exception:
            pass
        return None


# ── MQTT Publisher ───────────────────────────────────────────────────

class MQTTPublisher:
    """Publish telemetry and images via MQTT."""

    def __init__(self):
        self.client = None
        self._connected = False

    def connect(self):
        """Connect to MQTT broker."""
        try:
            from umqtt.simple import MQTTClient
            client_id = f"esp32-{DEVICE_ID}"
            self.client = MQTTClient(client_id, MQTT_BROKER, port=MQTT_PORT,
                                      user=MQTT_USER or None,
                                      password=MQTT_PASS or None,
                                      keepalive=120)
            self.client.connect()
            self._connected = True
            print(f"MQTT connected to {MQTT_BROKER}:{MQTT_PORT}")
            return True
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            self._connected = False
            return False

    def publish_telemetry(self, payload):
        """Publish sensor data as JSON to telemetry topic."""
        if not self._connected:
            if not self.connect():
                return False
        try:
            topic = MQTT_TOPIC_TELEMETRY.format(
                farm_id=FARM_ID, device_id=DEVICE_ID
            )
            msg = json.dumps(payload)
            self.client.publish(topic, msg)
            print(f"MQTT published → {topic} ({len(msg)} bytes)")
            return True
        except Exception as e:
            print(f"MQTT publish error: {e}")
            self._connected = False
            return False

    def disconnect(self):
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass
            self._connected = False


# ── REST Fallback ────────────────────────────────────────────────────

def rest_send_telemetry(payload):
    """Send telemetry via HTTP POST (fallback if MQTT unavailable)."""
    try:
        import urequests
        url = f"{REST_API_URL}{REST_INGEST}"
        headers = {"Content-Type": "application/json"}
        resp = urequests.post(url, json=payload, headers=headers)
        ok = resp.status_code == 200
        resp.close()
        if ok:
            print(f"REST telemetry sent ({url})")
        else:
            print(f"REST telemetry failed: HTTP {resp.status_code}")
        return ok
    except Exception as e:
        print(f"REST send error: {e}")
        return False


def rest_send_image(image_bytes):
    """
    Upload JPEG image via HTTP POST multipart/form-data.
    The server assigns a unique URL identifier.
    """
    if not image_bytes:
        return False
    try:
        import urequests
        url = f"{REST_API_URL}{REST_IMAGE}"

        # Build multipart body manually (MicroPython doesn't have requests-toolbelt)
        boundary = "----SmartShambaESP32"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="capture.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + image_bytes + (
            f"\r\n--{boundary}\r\n"
            f'Content-Disposition: form-data; name="farm_id"\r\n\r\n'
            f"{FARM_ID}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="device_id"\r\n\r\n'
            f"{DEVICE_ID}\r\n"
            f"--{boundary}--\r\n"
        ).encode("utf-8")

        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        resp = urequests.post(url, data=body, headers=headers)
        ok = resp.status_code == 200
        if ok:
            result = resp.json()
            print(f"Image uploaded: {result.get('image_url', 'OK')}")
        else:
            print(f"Image upload failed: HTTP {resp.status_code}")
        resp.close()
        return ok
    except Exception as e:
        print(f"Image upload error: {e}")
        return False


# ── Deep Sleep ───────────────────────────────────────────────────────

def enter_deep_sleep(seconds):
    """Enter deep sleep to conserve battery."""
    print(f"Entering deep sleep for {seconds}s...")
    machine.deepsleep(seconds * 1000)


# ── Main Loop ────────────────────────────────────────────────────────

def main():
    """Main firmware loop: read sensors → publish → sleep → repeat."""
    print()
    print("=" * 50)
    print("  🌾 Smart Shamba ESP32 — Starting")
    print(f"  Device: {DEVICE_ID}  |  Farm: {FARM_ID}")
    print("=" * 50)

    # Connect WiFi
    if not connect_wifi(WIFI_SSID, WIFI_PASSWORD):
        print("WiFi failed — entering deep sleep to retry...")
        if DEEP_SLEEP_ENABLED:
            enter_deep_sleep(60)
        return

    # Initialize sensors
    sensors = SensorArray()

    # Initialize MQTT
    mqtt_pub = MQTTPublisher()
    mqtt_ok = mqtt_pub.connect()

    # Track image interval (weekly)
    last_image_time = 0

    print(f"\nSensor loop: every {TELEMETRY_INTERVAL_SEC}s")
    print(f"Image capture: every {IMAGE_INTERVAL_SEC}s")
    print("-" * 50)

    cycle = 0
    while True:
        cycle += 1
        gc.collect()
        now = time.time()

        # ── Read sensors ─────────────────────────────────────────────
        try:
            payload = sensors.read_all()
            print(f"\n[{cycle}] Sensors: temp={payload.get('temperature_c')}°C "
                  f"moisture={payload.get('soil_moisture_pct')}% "
                  f"pH={payload.get('soil_ph')} "
                  f"batt={payload.get('battery_pct')}%")
        except Exception as e:
            print(f"Sensor read error: {e}")
            payload = {"device_id": DEVICE_ID, "farm_id": FARM_ID}

        # ── Publish telemetry ────────────────────────────────────────
        if mqtt_ok:
            if not mqtt_pub.publish_telemetry(payload):
                # MQTT failed — try REST fallback
                rest_send_telemetry(payload)
        else:
            rest_send_telemetry(payload)

        # ── Weekly image capture ─────────────────────────────────────
        if CAMERA_ENABLED and (now - last_image_time) >= IMAGE_INTERVAL_SEC:
            print("📷 Capturing crop image...")
            img = capture_image()
            if img:
                print(f"  Image captured: {len(img)} bytes")
                if not rest_send_image(img):
                    print("  Image upload failed — will retry next cycle")
                else:
                    last_image_time = now
                del img
                gc.collect()

        # ── Sleep or deep sleep ──────────────────────────────────────
        if DEEP_SLEEP_ENABLED:
            mqtt_pub.disconnect()
            enter_deep_sleep(TELEMETRY_INTERVAL_SEC)
            # After deep sleep, board resets and main() runs again
            break
        else:
            time.sleep(TELEMETRY_INTERVAL_SEC)


# Run on boot
if __name__ == "__main__":
    main()
else:
    # Also run when imported as boot.py
    main()
