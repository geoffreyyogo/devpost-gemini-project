"""
ESP32 Smart Shamba — Configuration
Flash this alongside main.py to your ESP32-CAM board.

Edit the values below to match your deployment:
    - WiFi credentials
    - MQTT broker (your server IP)
    - Farm/device IDs (assigned during registration)
    - Sensor pins
"""

# ── WiFi ─────────────────────────────────────────────────────────────
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# ── Device Identity ──────────────────────────────────────────────────
# Set these after registering the device via POST /api/iot/devices/register
DEVICE_ID = "esp32-001"
FARM_ID = 1

# ── MQTT Broker ──────────────────────────────────────────────────────
MQTT_BROKER = "192.168.1.100"       # Your server's LAN IP
MQTT_PORT = 1883
MQTT_USER = ""                       # Leave blank if no auth
MQTT_PASS = ""
MQTT_TOPIC_TELEMETRY = "shamba/{farm_id}/{device_id}/telemetry"
MQTT_TOPIC_IMAGE     = "shamba/{farm_id}/{device_id}/image"

# ── REST Fallback (if MQTT is unreachable) ───────────────────────────
REST_API_URL = "http://192.168.1.100:8000"
REST_INGEST  = "/api/iot/ingest"
REST_IMAGE   = "/api/iot/image/upload"

# ── Sensor Pins (adjust for your wiring) ─────────────────────────────
# Soil moisture — capacitive analog sensor (ADC)
PIN_SOIL_MOISTURE = 34              # ADC1_CH6

# Soil pH — analog sensor through signal conditioner
PIN_SOIL_PH = 35                    # ADC1_CH7

# DHT22 — temperature + humidity (digital)
PIN_DHT22 = 4                       # GPIO4

# Soil NPK — RS485 Modbus (UART)
PIN_NPK_TX = 17                     # UART2 TX
PIN_NPK_RX = 16                     # UART2 RX

# BMP280 / BME280 — atmospheric pressure + temp (I2C)
PIN_I2C_SDA = 21
PIN_I2C_SCL = 22

# Battery voltage divider (ADC)
PIN_BATTERY = 33                    # ADC1_CH5

# ── Camera (ESP32-CAM AI-Thinker) ───────────────────────────────────
CAMERA_ENABLED = True               # Set False if no camera module
# Only used if CAMERA_ENABLED — image dimensions
IMAGE_WIDTH  = 640
IMAGE_HEIGHT = 480
IMAGE_QUALITY = 12                  # JPEG quality 0-63 (lower = better)

# ── Timing ───────────────────────────────────────────────────────────
TELEMETRY_INTERVAL_SEC = 300        # Send sensor data every 5 minutes
IMAGE_INTERVAL_SEC = 604800         # Capture + send image every 7 days (weekly)
DEEP_SLEEP_ENABLED = False          # Use deep sleep between readings (saves battery)
DEEP_SLEEP_SEC = 300                # Deep sleep duration

# ── Calibration ──────────────────────────────────────────────────────
# Soil moisture sensor: raw ADC → percentage
# Measure sensor in air (dry) and water (wet) to calibrate
SOIL_MOISTURE_DRY = 3500            # ADC reading in dry air
SOIL_MOISTURE_WET = 1200            # ADC reading in water

# Soil pH sensor: raw voltage → pH
# Use pH 4.0 and pH 7.0 buffer solutions to calibrate
PH_VOLTAGE_AT_7 = 2.5              # Voltage at pH 7.0
PH_VOLTAGE_SLOPE = -0.18           # Volts per pH unit

# Battery voltage divider ratio (R1/R2+R1 if using divider for 4.2V LiPo)
BATTERY_VDIV_RATIO = 2.0           # e.g., 100k/100k divider = 2.0
BATTERY_MAX_V = 4.2
BATTERY_MIN_V = 3.0
