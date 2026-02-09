"""
ESP32 Smart Shamba — Setup & Flashing Guide
=============================================

STEP 1: Install MicroPython on ESP32-CAM
─────────────────────────────────────────
    # Download MicroPython firmware with camera support
    # For ESP32-CAM (AI-Thinker): use firmware from
    # https://github.com/lemariva/micropython-camera-driver/releases

    # Install esptool
    pip install esptool

    # Erase flash (hold BOOT button, press RESET, then release BOOT)
    esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

    # Flash MicroPython
    esptool.py --chip esp32 --port /dev/ttyUSB0 \\
        --baud 460800 write_flash -z 0x1000 micropython_camera_esp32.bin


STEP 2: Install Required Libraries
───────────────────────────────────
    # Install mpremote (Python tool for MicroPython)
    pip install mpremote

    # Install umqtt library on ESP32
    mpremote connect /dev/ttyUSB0 mip install umqtt.simple

    # Upload BMP280 driver (if using pressure sensor)
    mpremote connect /dev/ttyUSB0 mip install bmp280

    # Upload DHT library (usually built into MicroPython)
    # Already included in standard MicroPython firmware


STEP 3: Upload Firmware Files
──────────────────────────────
    # Upload config and main
    mpremote connect /dev/ttyUSB0 cp config.py :config.py
    mpremote connect /dev/ttyUSB0 cp main.py :main.py

    # Verify files
    mpremote connect /dev/ttyUSB0 ls


STEP 4: Register Device on Server
──────────────────────────────────
    # Call the registration endpoint from your computer:
    curl -X POST http://YOUR_SERVER:8000/api/iot/devices/register \\
        -H "Content-Type: application/json" \\
        -d '{
            "device_id": "esp32-001",
            "farm_id": 1,
            "device_type": "esp32-cam",
            "sensors": ["dht22", "soil_moisture", "soil_ph", "npk", "bmp280", "camera"],
            "firmware_version": "1.0.0",
            "notes": "North field — maize plot"
        }'

    # Response:
    # {"success": true, "device_id": "esp32-001", "farm_id": 1, "api_key": "..."}


STEP 5: Update config.py
─────────────────────────
    # Edit config.py with your actual values:
    #   - WIFI_SSID / WIFI_PASSWORD
    #   - MQTT_BROKER (your server LAN IP)
    #   - DEVICE_ID and FARM_ID (from registration response)
    #   - Sensor pin assignments (match your wiring)

    # Re-upload updated config
    mpremote connect /dev/ttyUSB0 cp config.py :config.py


STEP 6: Sensor Calibration
───────────────────────────
    # Soil Moisture:
    #   1. Measure ADC in dry air → set SOIL_MOISTURE_DRY
    #   2. Measure ADC in water  → set SOIL_MOISTURE_WET
    #
    #   mpremote connect /dev/ttyUSB0 exec "
    #   from machine import ADC, Pin
    #   adc = ADC(Pin(34)); adc.atten(ADC.ATTN_11DB); adc.width(ADC.WIDTH_12BIT)
    #   print('ADC raw:', adc.read())
    #   "

    # Soil pH:
    #   1. Dip sensor in pH 7.0 buffer → note voltage → set PH_VOLTAGE_AT_7
    #   2. Dip sensor in pH 4.0 buffer → calculate slope → set PH_VOLTAGE_SLOPE
    #   Slope = (V_at_4 - V_at_7) / (4.0 - 7.0)


STEP 7: Test & Run
───────────────────
    # Reboot the ESP32 (press RESET button)
    # or:
    mpremote connect /dev/ttyUSB0 reset

    # Monitor serial output
    mpremote connect /dev/ttyUSB0 repl

    # You should see:
    #   ============================
    #   🌾 Smart Shamba ESP32 — Starting
    #   Device: esp32-001  |  Farm: 1
    #   ============================
    #   WiFi connected: 192.168.1.50
    #   MQTT connected to 192.168.1.100:1883
    #   [1] Sensors: temp=25.3°C moisture=42.0% pH=6.5 batt=87.0%
    #   MQTT published → shamba/1/esp32-001/telemetry (128 bytes)


WIRING DIAGRAM
══════════════

    ESP32-CAM (AI-Thinker)
    ┌─────────────────────┐
    │  GPIO 4  ─── DHT22 DATA (+ 10kΩ pull-up to 3.3V)
    │  GPIO 34 ─── Soil Moisture (analog out)
    │  GPIO 35 ─── Soil pH (analog out via signal conditioner)
    │  GPIO 33 ─── Battery Voltage Divider (midpoint)
    │  GPIO 21 ─── I2C SDA (BMP280)
    │  GPIO 22 ─── I2C SCL (BMP280)
    │  GPIO 16 ─── RS485 RX (NPK sensor via MAX485)
    │  GPIO 17 ─── RS485 TX (NPK sensor via MAX485)
    │  3.3V    ─── Sensor VCC
    │  GND     ─── Sensor GND
    │  5V      ─── Camera module, RS485 module VCC
    └─────────────────────┘

    NPK Sensor (RS485 Modbus):
        NPK A+ ─── MAX485 A
        NPK B- ─── MAX485 B
        MAX485 DI  ─── ESP32 GPIO 17 (TX)
        MAX485 RO  ─── ESP32 GPIO 16 (RX)
        MAX485 DE+RE ─── ESP32 GPIO 17 (TX, for half-duplex)


TROUBLESHOOTING
═══════════════
    • WiFi won't connect:
        - Check SSID/password in config.py
        - ESP32-CAM GPIO 0 must be HIGH (not grounded) for normal boot

    • MQTT fails:
        - Verify broker is running: mosquitto -v
        - Check firewall allows port 1883
        - Test: mosquitto_pub -h SERVER_IP -t test -m "hello"

    • Camera black image:
        - Ensure PSRAM is enabled in firmware
        - Try camera.quality(15) for lower quality
        - Check ribbon cable connection

    • Soil moisture reads 0 or 100 always:
        - Recalibrate SOIL_MOISTURE_DRY and SOIL_MOISTURE_WET
        - Check ADC pin assignment matches wiring

    • NPK returns None:
        - Verify baud rate is 9600
        - Check MAX485 DE/RE pin connection
        - Ensure NPK sensor has 12-24V power supply
"""
