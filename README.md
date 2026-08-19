# NeuroSign-HMI: Edge-Native Multi-Modal Assistive Station
### *Submission for the Arduino Physical AI Challenge India 2026*
**Track**: Robotics & Interactive AI

---

## 🌟 Executive Overview
**NeuroSign-HMI** is a next-generation, edge-native assistive communication and smart-home automation station engineered specifically for the **Arduino UNO Q (4GB)**. 

Designed for individuals with speech, hearing, or motor impairments, the system bridges physical gesture expression with real-world voice synthesis, visual subtitles, appliance control, and emergency cellular alerts—**executing 100% locally on the edge with zero cloud dependencies**.

```
  Deaf/Mute User Signs  ──► [RPi Camera v3 (60 FPS)] ──► [MediaPipe + LSTM] ──► [MAX98357A I2S Amp Speaks Out]
  Hearing Person Speaks ──► [INMP441 I2S Mic]       ──► [Offline STT]       ──► [SmartElex 5" Subtitles]
  Emergency Sign        ──► [Qualcomm MPU]          ──► [STM32U585 MCU]     ──► [SIM800C GSM Offline SOS SMS]
```

---

## 🚀 Key Technical Innovations

1. **True 2-Way Conversational Bridge (Sign $\leftrightarrow$ Speech)**:
   - Translates dynamic hand signs to natural synthetic voice via **MAX98357A I2S Amplifier** & Piper TTS.
   - Translates spoken words to live text subtitles on the **SmartElex 5" Capacitive Touch Display** via **INMP441 I2S Microphone**.
2. **Dual-Brain Heterogeneous Compute**:
   - **Linux MPU (Qualcomm QRB2210 @ 2.0 GHz)**: 60 FPS vision processing, MediaPipe 3D Landmark extraction, and Adreno 702 GPU neural acceleration.
   - **Real-Time MCU (STM32U585 @ 160 MHz, Zephyr RTOS)**: Microsecond deterministic PWM servo tracking, 24 GHz radar auto-wake, optical relay switching, and I2C sensor aggregation.
3. **Autonomous Pan-Tilt Hand Tracking**:
   - Closed-loop proportional feedback drives dual **SG90 Servos** to keep the user's hands centered in the camera frame regardless of seating position.
4. **Smart Presence Auto-Wake**:
   - **HLK-LD2410C 24 GHz Millimeter-Wave Radar** detects human micro-motion, putting the system into low-power sleep when the room is empty and waking the station instantly upon approach.
5. **Offline Emergency Cellular Fallback**:
   - Triggers an instant SMS dispatch via **SIM800C GSM module** directly to caregiver phones during emergency gestures—even during power grid or Wi-Fi internet blackouts.

---

## 📁 Repository Structure

```
NeuroSign_HMI/
├── firmware_mcu/                 # STM32U585 (Zephyr RTOS / Arduino C++)
│   ├── firmware_mcu.ino          # Core setup, 1 kHz loop & RPC listeners
│   ├── RadarDriver.h             # HLK-LD2410C 24GHz UART auto-wake driver
│   ├── ServoTracker.h            # SG90 PWM pan-tilt camera tracker
│   ├── GSM_Emergency.h           # SIM800C AT command emergency SMS driver
│   ├── SensorBus.h               # SGP40 (VOC), INA219 (Power), DHT22, MPU6050
│   ├── MatrixDisplay.h           # 8x13 Blue LED Matrix dynamic glyph renderer
│   └── RelayActuator.h           # Opto-isolated relay & alarm controller
├── app_mpu/                      # Qualcomm QRB2210 (Debian Linux Python 3.11/3.12)
│   ├── main_orchestrator.py      # Master async coordinator daemon
│   ├── vision_pipeline.py        # 60 FPS RPi Camera v3 MIPI-CSI capture
│   ├── landmark_extractor.py     # MediaPipe 3D Landmark extraction
│   ├── gesture_classifier.py     # Quantized 1D-LSTM on Adreno 702 GPU
│   ├── audio_i2s.py              # I2S INMP441 capture & MAX98357A TTS playback
│   ├── display_touch_ui.py       # SmartElex 5" 800x480 Capacitive Touch UI
│   └── ipc_bridge.py             # MessagePack RPC bridge wrapper
├── models/                       # Edge AI Models & 3D Mocap Augmentation Engine
│   ├── gesture_lstm_int8.tflite  # Pre-trained quantized INT8 model artifact
│   ├── labels.json               # Gesture vocabulary mapping
│   ├── gestures_dataset.npz      # 2,100 sample 3D gesture training dataset
│   ├── train_lstm.py             # Model training & INT8 TFLite export
│   ├── synthetic_dataset_generator.py # Parametric 3D trajectory synthesizer
│   ├── mocap_streamer.py         # Real-time webcam to Blender 3D streamer
│   ├── blender_gesture_rig.py    # Blender 21-joint 3D hand armature & receiver
│   └── dataset_collector.py      # Real-time manual gesture data recorder
├── blender_addon/                # Blender MCP Integration
│   └── addon.py                  # Blender MCP add-on for AI-assisted 3D modeling
├── docker/                       # Containerized App Lab Deployment
│   ├── Dockerfile                # Production Debian image
│   └── docker-compose.yml        # IPC socket & device mappings
├── schematics/                   # EDA & Electrical Documentation
│   ├── BOM_NeuroSign.csv         # Bill of Materials with exact part numbers
│   └── WIRING_GUIDE.md           # Pinout, voltage domains & isolation rules
└── README.md                     # Project documentation
```

---

## ⚡ Hardware Pinout & Bill of Materials

Refer to [`schematics/WIRING_GUIDE.md`](./schematics/WIRING_GUIDE.md) and [`schematics/BOM_NeuroSign.csv`](./schematics/BOM_NeuroSign.csv) for full electrical pin tables, 1.8V level shifter wiring, and external power distribution.

---

## 🛠️ Quickstart & Deployment

### 1. Flash Microcontroller Firmware
Open `firmware_mcu/firmware_mcu.ino` in the Arduino IDE (or Arduino App Lab), select **Arduino UNO Q (MCU)**, and flash.

### 2. Launch Linux MPU Container
On the Arduino UNO Q Debian terminal:
```bash
cd NeuroSign_HMI/docker
docker compose up -d --build
```

### 3. Verify Live Execution
The SmartElex 5" screen will initialize displaying the live camera feed, active subtitle bar, and real-time power/air telemetry.
