# System Architecture & Protocol Reference: "Neuro Sign"
**Developer:** Rudra Attri Pandey  
**Device:** Neuro Sign Paralysis Patient Assistance Platform

---

## 1. System Communication Pipeline

```
+------------------------------------------------------------------------------------+
|  1. TX GLOVE (Wearable Glove)                                                      |
|     - 3x Flex Sensors + ADXL345 sampled at 100 Hz                                  |
|     - Local moving average filtering & auto-calibration                            |
|     - 0.96" SSD1306 OLED HUD with animated Radio Tower telemetry                   |
|     - 433 MHz RF ASK Packet transmitted at 14 Hz                                    |
+------------------------------------------------------------------------------------+
                                      |
                                      | 433 MHz RF ASK Telemetry Packet (11 bytes)
                                      v
+------------------------------------------------------------------------------------+
|  2. RX BASE STATION HUB (ESP32-S3)                                                 |
|     - Core 0: 433 MHz Packet RX + Link Quality + I2S Audio DMA Engine               |
|     - Core 1: Sensor Manager (DHT11, BMP280, SGP40, INA219)                       |
|               Neuro AI Classifier (Centroid Distance + Spasm Detector)             |
|               Optocoupler 4-Channel Relays (Light, Fan, Bed, Alarm)                |
|               MAX98357A I2S 3W Mono Voice Announcer                                |
|               SoftAP Captive Portal + WebSockets at 192.168.4.1                    |
|               UART Streamer (115200 baud)                                          |
+------------------------------------------------------------------------------------+
                 |                                                |
                 | WebSockets JSON (20 Hz)                        | UART Stream (20 Hz)
                 v                                                v
+------------------------------------+           +-----------------------------------+
|  3. CAREGIVER WEB DASHBOARD        |           |  4. ARDUINO UNO Q / PC PLOTTER    |
|     - Mobile / Tablet / PC Browser |           |     - Real-Time Multi-Channel     |
|     - Glassmorphic Cyber-Medical HUD|          |       Waveform Oscilloscope Plot  |
|     - Live Visual Gauges & Controls|           |     - Bedside External Monitor    |
+------------------------------------+           +-----------------------------------+
```

---

## 2. RF Telemetry Binary Packet Structure

The binary packet transmitted over 433 MHz ASK is structured as an 11-byte compact binary struct:

| Byte Offset | Field Name | Data Type | Range / Units | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0` | `preamble` | `uint8_t` | `0xAE` | Magic byte for frame synchronization |
| `1` | `sequenceId` | `uint8_t` | `0 - 255` | Incremental packet counter (for packet loss tracking) |
| `2` | `flex1` | `uint8_t` | `0 - 100 %` | Thumb flex sensor normalized percentage |
| `3` | `flex2` | `uint8_t` | `0 - 100 %` | Index finger flex sensor normalized percentage |
| `4` | `flex3` | `uint8_t` | `0 - 100 %` | Middle finger flex sensor normalized percentage |
| `5` | `pitch` | `int8_t` | `-90 to +90°`| Hand pitch tilt angle |
| `6` | `roll` | `int8_t` | `-90 to +90°`| Hand roll tilt angle |
| `7` | `tremorLevel` | `uint8_t`| `0 - 100 %` | High-frequency acceleration variance |
| `8` | `batteryPercent` | `uint8_t`| `0 - 100 %` | Glove LiPo battery charge |
| `9` | `gestureHint` | `uint8_t` | `0 - 99` | Fast local rule gesture classification |
| `10` | `checksum` | `uint8_t` | `0 - 255` | 8-bit left-rotated XOR checksum |

---

## 3. WebSockets JSON Protocol (Port 81)

Broadcasted from the ESP32-S3 to connected browsers every 50ms:

```json
{
  "rfConnected": true,
  "rfSignalQuality": 95,
  "packetsReceived": 1420,
  "packetsDropped": 12,
  "flex": [15, 82, 85],
  "pitch": 4,
  "roll": -2,
  "tremor": 9,
  "battery": 88,
  "gestureId": 2,
  "gestureName": "Need Water",
  "gestureConfidence": 0.97,
  "temperatureC": 25.4,
  "humidityPercent": 54.0,
  "pressureHpa": 1013.2,
  "vocIndex": 95,
  "busVoltageV": 5.04,
  "currentMA": 148.2,
  "powerMW": 746.9,
  "relayState": [false, false, false, false],
  "spasmAlertActive": false
}
```

### Inbound WebSocket Client Commands:
1. **Toggle Relay:**
   ```json
   { "action": "toggle_relay", "index": 0 }
   ```
2. **Play Voice Announcement:**
   ```json
   { "action": "play_sound", "id": 3 }
   ```
3. **Reset / Silence Emergency Alarm:**
   ```json
   { "action": "reset_alarm" }
   ```
