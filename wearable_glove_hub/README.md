# 🧠 NEURO SIGN - Industrial Paralysis Patient Assistance System

> **Developed by:** Rudra Attri Pandey  
> **System Version:** v2.4-IND  
> **Target Applications:** Biomedical Assistive Technology, Stroke & ALS Rehabilitation, Smart Hospital Ward & Home Automation.

---

## 🌟 System Overview

**Neuro Sign** is an industrial-grade, wireless assistive biomedical ecosystem designed specifically for paralyzed, stroke, and motor-neuron disease (ALS) patients. The platform bridges patient micro-movements to immediate physical actions, voice announcements, home automation, and live telemetry monitoring.

The system is composed of three interconnected hardware units:
1. **TX Glove Unit (Arduino Nano):** Wearable hand unit featuring 3x flex sensors, an ADXL345 3-axis digital accelerometer, a 0.96" SSD1306 OLED HUD with an animated radio transmission tower, and 433 MHz RF ASK telemetry.
2. **RX Medical Hub & Base Station (ESP32-S3):** Dual-core smart station featuring 433 MHz superheterodyne reception, 4-channel optocoupler relay automation, a MAX98357A I2S 3W mono voice announcer, a comprehensive vital sensor suite (**DHT11, BMP280, SGP40 VOC AQI, INA219 Power Monitor**), an embedded **TinyML Neuro AI Classifier & Spasm Detector**, and a self-hosted **SoftAP Web Dashboard (`192.168.4.1`)**.
3. **External Visualizer (Arduino UNO Q):** High-speed UART telemetry visualizer and real-time multi-channel waveform plotter for clinical bedside monitors.

---

## 📁 Repository Structure

```
Rudra2/
├── tx_glove_nano/              # Arduino Nano TX Glove Firmware
│   ├── tx_glove_nano.ino       # Main sketch & loop orchestration
│   ├── config.h                # Pinouts, RF parameters, packet struct
│   ├── gesture_sensors.h/.cpp  # 3x Flex + ADXL345 I2C driver & filter
│   ├── oled_display.h/.cpp     # SSD1306 HUD with animated signal tower
│   └── rf_transmitter.h/.cpp   # 433 MHz ASK packet serializer
├── rx_hub_esp32s3/             # ESP32-S3 Medical Hub Firmware
│   ├── rx_hub_esp32s3.ino      # Main FreeRTOS dual-core sketch
│   ├── config.h                # Pinouts, SoftAP settings, static IP
│   ├── rf_receiver.h/.cpp      # 433 MHz ASK decoder & packet loss tracker
│   ├── audio_engine.h/.cpp     # MAX98357A I2S Class-D DAC driver
│   ├── sound_data.h            # Speech and alert sound definitions
│   ├── sensor_manager.h/.cpp   # DHT11, BMP280, SGP40, INA219 driver suite
│   ├── relay_controller.h/.cpp # 4-Channel optocoupler home automation
│   ├── neuro_ai_engine.h/.cpp  # TinyML gesture classifier & tremor detector
│   ├── web_dashboard.h/.cpp    # SoftAP Captive Portal & WebSockets at 192.168.4.1
│   └── uart_streamer.h/.cpp    # High-speed UART telemetry streamer
├── uno_q_monitor/              # Arduino UNO Q Live Plotter Firmware
│   ├── uno_q_monitor.ino       # UART packet parser & serial plotter
│   └── config.h                # Baud rate & channel configurations
├── data_web_ui/                # Standalone Web Dashboard Source Assets
│   ├── index.html              # Cyber-medical glassmorphic layout
│   ├── style.css               # Modern CSS3 dark mode & glowing animations
│   └── app.js                  # WebSocket client & live canvas graph
├── docs/                       # Engineering Documentation
│   ├── WIRING_PINOUT_GUIDE.md  # Detailed hardware connection tables
│   ├── SCHEMATIC_CIRCUIT_DESIGN.md # Circuit schematics & PCB guidelines
│   ├── AI_GESTURE_ALGORITHMS.md    # TinyML mathematical derivation
│   └── SYSTEM_ARCHITECTURE.md  # End-to-end communication protocols
└── README.md                   # Master Documentation
```

---

## ⚡ Hardware Specifications & Bill of Materials

### 1. Transmitter Glove (TX)

| Subsystem / Component | Component Details | Arduino Nano Interface / Pin | Function / Specification |
| :--- | :--- | :--- | :--- |
| **Main Controller (MCU)** | Arduino Nano | Core MCU | ATmega328P, 16 MHz, 5V / 2KB RAM |
| **Flex Sensors (3x)** | 2.2" / 4.5" Flex Sensors | `A0` (Thumb), `A1` (Index), `A2` (Middle) | 10kΩ Divider for Finger Bend Measurement |
| **3-Axis Accelerometer** | ADXL345 Digital Accel (I2C: `0x53`) | `SDA: A4`, `SCL: A5` | ±4g Range Pitch, Roll & Tremor Jitter Detection |
| **OLED Display HUD** | 0.96" SSD1306 OLED (I2C: `0x3C`)| `SDA: A4`, `SCL: A5` | 128x64 HUD with Animated Signal Tower |
| **RF 433 MHz Transmitter** | FS1000A ASK Transmitter | `DATA: D12` | 2000 bps ASK Telemetry with 17.3cm 22AWG Antenna |
| **Power Management** | 3.7V 850mAh LiPo + TP4056 + MT3608 | `5V Rail` / `A3 (Divider)` | 5V Boosted Rail with Battery Level ADC Sensing |

### 2. Base Station Medical Hub (RX)

| Subsystem / Component | Component Details | ESP32-S3 Interface / Pin | Function / Specification |
| :--- | :--- | :--- | :--- |
| **Main Controller (MCU)** | ESP32-S3 DevKitC-1 | Core MCU | Xtensa Dual-Core LX7, 240 MHz, 8MB Flash / 2MB PSRAM |
| **RF 433 MHz Receiver** | Superheterodyne (RX470 / SYN480R) | `GPIO 4` (DATA) | 433.92 MHz ASK Wireless Telemetry Receiver |
| **Audio Voice Engine** | MAX98357A I2S Class-D Mono Amp | `BCLK: 16`, `LRC: 17`, `DIN: 18` | 3W Mono DAC Output to 4Ω/8Ω 3W Speaker |
| **MicroSD Voice Storage** | MicroSD SPI Card Module | `CS: 5`, `MOSI: 6`, `SCK: 7`, `MISO: 21` | MP3 / WAV Pre-recorded Voice Prompt Files |
| **Home Automation** | 4-Channel Optocoupler Relays | `GPIO 10, 11, 12, 13` | Active LOW control for Light, Fan, Bed, Emergency Alarm |
| **Room Temp & Humidity** | DHT11 Sensor | `GPIO 15` (DATA) | Ambient Room Temperature (°C) and Humidity (%) |
| **Air Pressure & Altitude** | BMP280 Sensor (I2C: `0x76`) | `SDA: GPIO 8`, `SCL: GPIO 9` | High-Precision Barometric Pressure (hPa) & Altitude |
| **Indoor Air Quality (AQI)**| SGP40 VOC Sensor (I2C: `0x59`) | `SDA: GPIO 8`, `SCL: GPIO 9` | Sensirion VOC Air Quality Index (1 - 500) |
| **Electrical Power Monitor**| INA219 Power Sensor (I2C: `0x40`) | `SDA: GPIO 8`, `SCL: GPIO 9` | High-Side Supply Bus Voltage (V), Current (mA), Power (mW) |
| **External Monitor Bridge** | Hardware UART Bridge | `TX: GPIO 43`, `RX: GPIO 44` | 115200 Baud Data Stream to Arduino UNO Q / Live Plotter |

### 3. Bedside Live Plotter (Extended)

| Subsystem / Component | Component Details | Interface / Pin | Function / Specification |
| :--- | :--- | :--- | :--- |
| **Live Visualizer MCU** | Arduino UNO Q (4GB) / UNO R4 | `RX: Pin 0`, `TX: Pin 1` | High-Speed UART Multi-Channel Waveform Plotter |
| **Serial Wave Stream** | Arduino IDE Serial Plotter / Processing | USB Serial @ 115200 Baud | Real-time Multi-Variable Oscilloscope Graphing |

---

## 🖐️ AI Gesture Dictionary & Hierarchical Control Matrix

| Mode / Hand Orientation | Gesture ID | Intention Name | Trigger Gesture | System Action Triggered |
| :--- | :--- | :--- | :--- | :--- |
| **Mode 1: Flat on Bed** <br>*(Roll ≈ 0°, -40° to +40°)* | **1** | **Need Water** | **Bend Finger 1 (Thumb/Index)** | 🔊 Voice Prompt: *"I Need Water"* |
| | **2** | **Need Food** | **Bend Finger 2 (Middle)** | 🔊 Voice Prompt: *"I Need Food"* |
| | **3** | **Need Medicine** | **Bend Finger 3 (Ring/Pinky)** | 🔊 Voice Prompt: *"I Need Medicine"* |
| | **4** | **EMERGENCY CALL** | **All 3 Fingers Bent (>65%)** | 🚨 **Fires Alarm Siren + Relay 4** |
| **Mode 2: Tilt 90° LEFT** <br>*(Roll < -40°, Palm Left)* | **11** | **Toggle Light 1** | **Bend Finger 1 (Thumb/Index)** | 💡 **Toggles Relay 1 (Light 1 ON/OFF)** |
| | **12** | **Toggle Room Fan**| **Bend Finger 2 (Middle)** | 🌀 **Toggles Relay 2 (Fan ON/OFF)** |
| | **13** | **Toggle Bed Position**| **Bend Finger 3 (Ring/Pinky)**| 🛏️ **Toggles Relay 3 (Bed Adjust ON/OFF)** |
| **Mode 3: Tilt 90° RIGHT** <br>*(Roll > +40°, Palm Right)*| **21** | **Call Nurse** | **Bend Finger 1 (Thumb/Index)** | 👩‍⚕️ **Nurse Station Call Alert Chime** |
| | **22** | **Pain Alert** | **Bend Finger 2 (Middle)** | ⚠️ **Patient Pain Warning Alert** |
| | **23** | **All Appliances OFF**| **Bend Finger 3 (Ring/Pinky)**| 🌙 **Switches OFF Relays 1, 2, 3 (Sleep)**|
| **Any Position** | **99** | **Spasm / Tremor Alert**| **Sustained Tremor (>70%)** | 🚨 **Emergency Alarm + Caregiver Alert** |

---

## 🛠️ Required Arduino IDE Libraries

Install the following libraries via the **Arduino IDE Library Manager** (`Ctrl+Shift+I`):
1. `Adafruit SSD1306` & `Adafruit GFX Library` (for OLED display on TX Glove)
2. `ArduinoJson` by Benoit Blanchot (Version 6.x or 7.x)
3. `WebSockets` by Markus Sattler (for ESP32 WebSockets telemetry server)
4. `WiFi`, `WebServer`, `DNSServer`, `Wire` (Built directly into ESP32 & Arduino cores)

*(Note: The 433 MHz RF ASK Demodulator/Modulator is natively implemented with high-speed microsecond interrupts, eliminating any AVR-specific `RadioHead`/`util/atomic.h` dependencies for 100% native ESP32-S3 compilation).*

---

## 📁 MicroSD Card Audio Setup (.WAV / .MP3 Voice Files)

Format your MicroSD card as **FAT32** and copy your voice audio recordings directly into the root directory:

| Filename on SD Card | Triggered By | Voice Announcement Description |
| :--- | :--- | :--- |
| `/water.wav` | Flat Bed + Bend Finger 1 | *"I need water, please bring me water."* |
| `/food.wav` | Flat Bed + Bend Finger 2 | *"I need food, I am feeling hungry."* |
| `/medicine.wav` | Flat Bed + Bend Finger 3 | *"I need my medicine / assistance."* |
| `/emergency.wav`| Flat Bed + All 3 Fingers | *"Emergency help needed immediately!"* |
| `/light.wav` | Left 90° + Bend Finger 1 | *"Room light switched."* |
| `/fan.wav` | Left 90° + Bend Finger 2 | *"Room fan switched."* |
| `/bed.wav` | Left 90° + Bend Finger 3 | *"Adjusting hospital bed position."* |
| `/nurse.wav` | Right 90° + Bend Finger 1| *"Calling duty nurse to bedside."* |
| `/pain.wav` | Right 90° + Bend Finger 2| *"Patient is experiencing pain, please assist."* |
| `/all_off.wav` | Right 90° + Bend Finger 3| *"All appliances switched off. Sleep mode."* |
| `/startup.wav` | Hub Power On / Boot | *"Neuro Sign medical hub online and calibrated."* |

*(Note: If the MicroSD card is not inserted or a specific file is missing, the ESP32-S3 automatically and gracefully falls back to the built-in algorithmic speech synthesizer chime so patient alerts are never lost!).*

---

## 🚀 Quick Start & Operating Guide

### Step 1: Flashing the Transmitter Glove (TX)
1. Open [tx_glove_nano.ino](file:///c:/Users/Purulia_3D/OneDrive/AppData/Desktop/project1/Rudra2/tx_glove_nano/tx_glove_nano.ino) in Arduino IDE.
2. Select Board: **Arduino Nano**, Processor: **ATmega328P (Old Bootloader / New Bootloader)**.
3. Upload the sketch.
4. On power-up, keep your hand flat and resting for 2 seconds while the auto-calibration bar fills.
5. The OLED will show the animated transmission tower and live sensor values.

### Step 2: Flashing the Receiver Hub (RX)
1. Open [rx_hub_esp32s3.ino](file:///c:/Users/Purulia_3D/OneDrive/AppData/Desktop/project1/Rudra2/rx_hub_esp32s3/rx_hub_esp32s3.ino) in Arduino IDE.
2. Select Board: **ESP32S3 Dev Module** (Flash Size: 8MB, PSRAM: OPI PSRAM, USB CDC On Boot: Enabled).
3. Upload the sketch.
4. The ESP32-S3 will initialize all sensors, relays, audio amp, and start the WiFi Access Point.

### Step 3: Connecting to the Web Dashboard
1. On your smartphone, tablet, or laptop, connect to the WiFi network:
   - **SSID:** `NeuroSign_Hub`
   - **Password:** `neurosign2026`
2. Open any web browser and navigate to:
   - **Static IP:** `http://192.168.4.1/`
3. The glassmorphic HUD will instantly load with live real-time flex telemetry, orientation tilt, environmental vitals, relay controls, audio buttons, and patient event audit logs.

### Step 4: Connecting the Arduino UNO Q Live Plotter (Extended)
1. Connect ESP32-S3 `GPIO 43` (TX) to Arduino UNO Q `Pin 0` (RX) and join common GND.
2. Open [uno_q_monitor.ino](file:///c:/Users/Purulia_3D/OneDrive/AppData/Desktop/project1/Rudra2/uno_q_monitor/uno_q_monitor.ino) and upload it to the Arduino UNO Q.
3. Open **Tools -> Serial Plotter** (`Ctrl+Shift+L`) at **115200 baud** to see real-time multi-variable biomedical sensor waveforms!

---

## 📜 Credits & License

**Developed by:** Rudra Attri Pandey  
**Project:** Neuro Sign - Paralysis Patient Assistance Biomedical Platform  
**License:** Open Academic & Biomedical Innovation License (2026)
