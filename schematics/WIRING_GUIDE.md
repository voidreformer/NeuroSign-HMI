# NeuroSign-HMI Max: Complete Hardware Wiring & Electrical Pinout Guide

This document defines the exact hardware connections, power distribution, and logic-level isolation rules for the **NeuroSign-HMI Max** assistive workstation on the **Arduino UNO Q (4GB)**.

---

## ⚡ Critical Power & Voltage Isolation Architecture

> [!CAUTION]
> **Voltage Domains & Level Shifting**:
> - **Qualcomm Dragonwing MPU (JMEDIA & JMISC headers)**: Native **1.8V Logic**. Direct connection to 3.3V or 5V logic lines will permanently destroy the Qualcomm silicon.
> - **STM32U585 MCU & Qwiic Bus (JDIGITAL & JANALOG headers)**: Native **3.3V Logic** (5V tolerant on select pins).
> - **GSM Module (SIM800C)**: Requires **3.7V - 4.4V (peak 2.0A bursts)**. DO NOT power from Arduino 5V/3.3V pin. Must be powered via an external **LM2596 DC-DC Buck Converter** connected to the primary 12V/7.4V battery pack.

```
                  ┌──────────────────────────────────────────────────┐
                  │          Primary Power Supply (12V DC / LiPo)    │
                  └─────────┬──────────────────────┬─────────────────┘
                            │                      │
                   ┌────────▼─────────┐   ┌────────▼────────┐
                   │ LM2596 Buck (5V) │   │ LM2596 Buck(4V) │
                   └────────┬─────────┘   └────────┬────────┘
                            │                      │
             ┌──────────────┴──────────┐           │ (Peak 2A)
             │                         │           ▼
     ┌───────▼────────┐      ┌─────────▼────────┐ ┌───────────────────┐
     │ Arduino UNO Q  │      │ 5V Relays, Servos│ │ SIM800C GSM       │
     │ (5V_SYS / VIN) │      │ (SG90, L298N)    │ │ Cellular Module   │
     └────────────────┘      └──────────────────┘ └───────────────────┘
```

---

## 📌 Detailed Pinout Connection Chart

### 1. Vision & Display Subsystem (60-Pin JMEDIA Header - 1.8V Domain)

| Module | Module Pin | Arduino UNO Q Header | Signal Name | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Raspberry Pi Camera v3** | MIPI-CSI Ribbon | JMEDIA CSI-0 (4-Lane) | `MIPI_CSI0_D[0..3]` | 60 FPS 1080p Gesture Tracking |
| | 3.3V / 1.8V Power | JMEDIA Power Pins | `1V8_CAM`, `3V3_SYS` | Dedicated camera power rail |
| | I2C Control | JMEDIA I2C-CSI | `CSI0_SDA`, `CSI0_SCL` | Autofocus & sensor config |
| **SmartElex 5" TFT Touch** | MIPI-DSI / Ribbon | JMEDIA DSI-0 (4-Lane) | `MIPI_DSI0_D[0..3]` | 800x480 Display Stream |
| (Capacitive Touch) | I2C Touch (SDA) | JMEDIA I2C-DSI | `DSI_TOUCH_SDA` | 1.8V I2C Touch Controller |
| | I2C Touch (SCL) | JMEDIA I2C-DSI | `DSI_TOUCH_SCL` | 1.8V I2C Touch Controller |
| | Touch Interrupt | JMEDIA GPIO | `GPIO_TOUCH_INT` | Low-active interrupt |

---

### 2. High-Fidelity I2S Audio Subsystem (60-Pin JMISC Header - 1.8V / Level-Shifted)

*Using TI TXU0104 Level Translator to bridge 1.8V MPU I2S bus to 3.3V Audio Breakouts:*

| Module | Module Pin | TXU0104 Shifter | Arduino UNO Q (JMISC) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **INMP441 (I2S Mic)** | `SD` (Serial Data Out)| `A1 (3.3V)` $\rightarrow$ `B1 (1.8V)` | `I2S_SDI` (Pin 14) | Digital Audio In (Speech) |
| | `SCK` (Serial Clock) | `B2 (1.8V)` $\rightarrow$ `A2 (3.3V)` | `I2S_SCK` (Pin 16) | Bit Clock (16/32-bit audio) |
| | `WS` (Word Select)   | `B3 (1.8V)` $\rightarrow$ `A3 (3.3V)` | `I2S_WS` (Pin 18)  | Left/Right Channel Select |
| | `L/R`                | GND (3.3V Rail)                       | GND                 | Left Channel Selected |
| | `VDD` / `GND`        | 3.3V Rail / Common GND                | `3V3_SYS` / `GND`   | Digital Mic Power |
| **MAX98357A (I2S Amp)** | `DIN` (Data In)     | `B4 (1.8V)` $\rightarrow$ `A4 (3.3V)` | `I2S_SDO` (Pin 20) | Digital Audio Out (TTS) |
| | `BCLK` (Bit Clock)   | Tied to `I2S_SCK` (3.3V side)         | `I2S_SCK` (Pin 16) | Shared I2S Clock |
| | `LRC` (Left/Right)   | Tied to `I2S_WS` (3.3V side)          | `I2S_WS` (Pin 18)  | Shared Frame Sync |
| | `GAIN`               | GND (100kΩ pull-down)                 | GND                 | Set gain to +9dB |
| | `Vin` / `GND`        | 5V Isolated / Common GND              | `5V_SYS` / `GND`    | Drives 3W 4Ω Speaker |

---

### 3. Sensor Bus & Radar Subsystem (STM32U585 MCU - 3.3V Domain)

| Module | Module Pin | Arduino UNO Q Interface | Pin / Port | Functionality |
| :--- | :--- | :--- | :--- | :--- |
| **HLK-LD2410C (24GHz Radar)**| `TX` | MCU JDIGITAL Header | `RX2` (Pin D0 / PA3) | 24 GHz Presence Stream |
| | `RX` | MCU JDIGITAL Header | `TX2` (Pin D1 / PA2) | Radar Config & Sensitivity |
| | `OUT` | MCU JDIGITAL Header | `D2` (Pin PB4) | Instant Presence Interrupt |
| | `VCC` (5V) / `GND` | Power Rail / GND | `5V_SYS` / `GND` | Radar Power Supply |
| **SGP40 (Air Quality)** | `SDA` / `SCL` | Dedicated Qwiic I2C | `I2C1_SDA` / `I2C1_SCL` | VOC Gas Index Tracking |
| **INA219 (Power Monitor)** | `SDA` / `SCL` | Dedicated Qwiic I2C | `I2C1_SDA` / `I2C1_SCL` | System Current & Watts |
| **MPU-6050 (6-Axis IMU)** | `SDA` / `SCL` | Dedicated Qwiic I2C | `I2C1_SDA` / `I2C1_SCL` | Vibration & Motion |
| | `INT` | MCU JDIGITAL Header | `D3` (Pin PB5) | Motion Wake Interrupt |
| **DHT22 (Temp & Humidity)** | `DATA` | MCU JDIGITAL Header | `D4` (Pin PB6) | Ambient Temp Tracking |

---

### 4. Actuators, Servos & GSM Cellular Subsystem (MCU Control)

| Module | Module Pin | Arduino UNO Q Header | Pin / Port | Operational Logic |
| :--- | :--- | :--- | :--- | :--- |
| **SG90 Pan Servo** | `PWM Signal` | MCU JDIGITAL | `D9` (TIM1_CH1 / PE9) | Horizontal Camera Tracking |
| | `5V` / `GND` | External 5V Buck / GND | `5V_EXT` / `GND` | Prevents brownouts |
| **SG90 Tilt Servo** | `PWM Signal` | MCU JDIGITAL | `D10` (TIM1_CH2 / PE11)| Vertical Camera Tracking |
| | `5V` / `GND` | External 5V Buck / GND | `5V_EXT` / `GND` | Prevents brownouts |
| **Relay Channel 1 (Light)**| `IN1` | MCU JDIGITAL | `D6` (PB8) | Active LOW Optocoupler |
| **Relay Channel 2 (Alarm)**| `IN2` | MCU JDIGITAL | `D7` (PB9) | Active LOW Optocoupler |
| **SIM800C GSM Module** | `RXD` | MCU JDIGITAL (UART3) | `TX3` (Pin D8 / PD8) | Emergency SMS Commands |
| | `TXD` | MCU JDIGITAL (UART3) | `RX3` (Pin D11 / PD9)| GSM Status & Network Info |
| | `VBAT` (4.0V) | Dedicated Buck Converter| `4V_BUCK` (2A Peak) | GSM Cellular Power |
| | `GND` | Common Ground | `GND` | Common Ground Reference |

---

## 🛠️ Grounding & Noise Suppression Rules

1. **Star Ground Topology**: Connect Arduino Ground, 5V Buck Ground, 4V GSM Buck Ground, and Audio Amplifier Ground to a central star ground bus.
2. **Audio Decoupling**: Place a $100\mu\text{F}$ electrolytic capacitor in parallel with a $0.1\mu\text{F}$ ceramic capacitor across the MAX98357A power pins to eliminate digital switching hum.
3. **Servo Filtering**: Place a $470\mu\text{F}$ electrolytic capacitor across the SG90 5V servo rail to absorb inductive kickback when motors reverse direction.
