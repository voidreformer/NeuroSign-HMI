# Neuro Sign - Complete Engineering Log & Conversation History

**System:** Neuro Sign - Paralysis Patient Assistance Biomedical Platform  
**Developer:** Rudra Attri Pandey  
**Conversation ID:** `263f93c3-5131-4645-b453-6ea5dae37963`  
**Date:** August 2026  

---

## 📑 Executive Summary of Built Systems

1. **Transmitter Glove (TX Module) - Arduino Nano**:
   - **Sensors:** 3x Flex Sensors (`A0, A1, A2`) + ADXL345 3-Axis Digital Accelerometer (`A4-SDA, A5-SCL`).
   - **Display:** 0.96" SSD1306 OLED HUD (`0x3C`) with dynamic **animated radio transmission tower**, battery percentage, and gesture action banners.
   - **RF Communication:** 433 MHz ASK Native Pulse Modulator (`D12`) with preamble sync, checksum, and sequence counters.
   - **Power:** 3.7V LiPo with battery ADC divider monitoring (`A3`).

2. **Receiver Medical Hub (RX Base Station) - ESP32-S3**:
   - **RF Receiver:** Native microsecond GPIO interrupt pulse demodulator on `GPIO 4` (Zero external library / Zero AVR dependencies).
   - **Audio Voice Engine:** MAX98357A I2S 3W Mono Class-D Amplifier (`BCLK:16, LRC:17, DIN:18`).
   - **MicroSD Card Audio Engine:** MicroSD SPI (`CS:5, MOSI:6, SCK:7, MISO:21`) streaming pre-recorded `.wav` / `.mp3` voice prompts with automatic algorithmic synthesizer fallback.
   - **Home Automation:** 4-Channel optocoupler isolated relays (`GPIO 10, 11, 12, 13`) for Light 1, Fan, Bed Position, and Emergency Buzzer.
   - **Sensor Diagnostic Suite:**
     - **DHT11:** Room Temperature & Humidity (`GPIO 15`).
     - **BMP280:** High-precision Barometric Air Pressure & Altitude (I2C: `GPIO 8`/`GPIO 9`, address `0x76`).
     - **SGP40:** Sensirion Indoor Air Quality & VOC Index (I2C: `GPIO 8`/`GPIO 9`, address `0x59`).
     - **INA219:** High-Side Voltage, Current & Power Monitor (I2C: `GPIO 8`/`GPIO 9`, address `0x40`).
   - **TinyML Neuro AI Classifier:** 3-mode hierarchical gesture recognition & continuous tremor/spasm anomaly detection.
   - **SoftAP & Web Dashboard:** Self-hosted WiFi Access Point (`NeuroSign_Hub`) at static IP `192.168.4.1` with a glassmorphic cyber-medical HUD and live WebSockets.
   - **UART Streamer:** Continuous 115200 baud telemetry bridge to external monitors (`GPIO 43/44`).

3. **Bedside Visualizer - Arduino UNO Q**:
   - High-speed UART receiver that parses the JSON telemetry stream and outputs live multi-variable waveform oscilloscope plots to the Arduino IDE Serial Plotter / Processing visualizers.

---

## 🖐️ Hierarchical 3-Mode Gesture Control Mapping

```
                                [ Patient Hand Position ]
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
 [ MODE 1: FLAT BED ]            [ MODE 2: TILT LEFT 90° ]         [ MODE 3: TILT RIGHT 90° ]
  (Roll: -40° to +40°)             (Roll < -40°, Palm Left)          (Roll > +40°, Palm Right)
         |                                  |                                  |
  • Finger 1: "Need Water"          • Finger 1: Toggle Light 1         • Finger 1: Call Nurse
  • Finger 2: "Need Food"           • Finger 2: Toggle Fan             • Finger 2: Pain Alert
  • Finger 3: "Need Medicine"       • Finger 3: Toggle Bed             • Finger 3: All Relays OFF
  • All 3: Emergency Alarm          (Appliance Control)                (Caregiver Assistance)
```

---

## 📁 MicroSD Card Audio Files Reference

| File on SD Card | Trigger Condition | Voice Audio Message |
| :--- | :--- | :--- |
| `/water.wav` | Mode 1 (Flat) + Bend Finger 1 | *"I need water, please bring me a glass of water."* |
| `/food.wav` | Mode 1 (Flat) + Bend Finger 2 | *"I need food, I am feeling hungry."* |
| `/medicine.wav` | Mode 1 (Flat) + Bend Finger 3 | *"I need my medicine / assistance."* |
| `/emergency.wav`| Mode 1 (Flat) + All 3 Fingers | *"Emergency help needed immediately at Bedside 1!"* |
| `/light.wav` | Mode 2 (Left) + Bend Finger 1 | *"Room light switched."* |
| `/fan.wav` | Mode 2 (Left) + Bend Finger 2 | *"Room fan switched."* |
| `/bed.wav` | Mode 2 (Left) + Bend Finger 3 | *"Adjusting hospital bed position."* |
| `/nurse.wav` | Mode 3 (Right) + Bend Finger 1| *"Calling nurse to bedside."* |
| `/pain.wav` | Mode 3 (Right) + Bend Finger 2| *"Patient is experiencing pain, please assist."* |
| `/all_off.wav` | Mode 3 (Right) + Bend Finger 3| *"All appliances switched off. Sleep mode."* |
| `/startup.wav` | Base Station Power On | *"Neuro Sign medical hub online and calibrated."* |

---

## 🛠️ Hardware Pinouts Summary

### TX Glove (Arduino Nano)
- Flex Sensors: `A0` (F1), `A1` (F2), `A2` (F3)
- Battery Monitor: `A3`
- I2C Bus (SSD1306 OLED + ADXL345): `A4` (SDA), `A5` (SCL)
- RF 433 MHz Transmitter: `D12` (DATA)

### RX Base Hub (ESP32-S3)
- RF 433 MHz Receiver: `GPIO 4` (DATA)
- Relays (4-Channel): `GPIO 10` (Light), `GPIO 11` (Fan), `GPIO 12` (Bed), `GPIO 13` (Alarm)
- I2S Audio Amp (MAX98357A): `GPIO 16` (BCLK), `GPIO 17` (LRC), `GPIO 18` (DIN)
- MicroSD SPI: `GPIO 5` (CS), `GPIO 6` (MOSI), `GPIO 7` (SCK), `GPIO 21` (MISO)
- DHT11 Sensor: `GPIO 15`
- I2C Sensors (BMP280, SGP40, INA219): `GPIO 8` (SDA), `GPIO 9` (SCL)
- UART Stream to UNO Q: `GPIO 43` (TX), `GPIO 44` (RX)
