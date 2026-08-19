# Schematic & Circuit Design: "Neuro Sign"
**Developer:** Rudra Attri Pandey  
**System Architecture:** Wireless Assistive Telemetry & Biomedical Hub

---

## 1. TX Glove Unit Schematic Diagram

```
+-----------------------------------------------------------------------------------+
|                              TX GLOVE (ARDUINO NANO)                              |
|                                                                                   |
|  +-------------------+                                                            |
|  | 3.7V LiPo Battery |----> [ TP4056 + Boost 5V ] ----> VCC (5V) & 3.3V Reg      |
|  +-------------------+                                                            |
|                                                                                   |
|  [ Flex Sensor 1 ] ---+---> A0                                                    |
|                       |                                                           |
|                     [10k]                                                         |
|                       |                                                           |
|                      GND                                                          |
|                                                                                   |
|  [ Flex Sensor 2 ] ---+---> A1                                                    |
|                       |                                                           |
|                     [10k]                                                         |
|                       |                                                           |
|                      GND                                                          |
|                                                                                   |
|  [ Flex Sensor 3 ] ---+---> A2                                                    |
|                       |                                                           |
|                     [10k]                                                         |
|                       |                                                           |
|                      GND                                                          |
|                                                                                   |
|  [ ADXL345 Accel ]                                                                |
|     VCC -> 3.3V, GND -> GND                                                       |
|     SDA -------------------> A4 (SDA) <-----+ (4.7k Pull-up to 3.3V)              |
|     SCL -------------------> A5 (SCL) <-----+ (4.7k Pull-up to 3.3V)              |
|                                                                                   |
|  [ 0.96" OLED SSD1306 ]                                                           |
|     VCC -> 5V/3.3V, GND -> GND                                                    |
|     SDA -------------------> A4 (SDA)                                             |
|     SCL -------------------> A5 (SCL)                                             |
|                                                                                   |
|  [ 433 MHz RF Transmitter (FS1000A) ]                                             |
|     VCC -> 5V, GND -> GND, DATA -> D12, ANT -> 17.3cm 22AWG Wire                  |
+-----------------------------------------------------------------------------------+
```

---

## 2. RX Medical Hub Base Station Schematic Diagram

```
+-----------------------------------------------------------------------------------+
|                          RX MEDICAL HUB (ESP32-S3)                                |
|                                                                                   |
|  [ 5V 3A DC Supply ] ===> [ INA219 VIN+ / VIN- Current Shunt ] ===> 5V Rail       |
|                                                                                   |
|  [ 433 MHz Superheterodyne RX ]                                                   |
|     VCC -> 5V, GND -> GND, DATA -> GPIO 4, ANT -> 17.3cm Wire                     |
|                                                                                   |
|  [ MAX98357A I2S 3W Mono Amp ]                                                    |
|     VDD -> 5V, GND -> GND                                                         |
|     BCLK -----------------> GPIO 16                                               |
|     LRC / WS -------------> GPIO 17                                               |
|     DIN ------------------> GPIO 18                                               |
|     SPK+ / SPK- ----------> 4Ω / 8Ω 3W Speaker                                    |
|                                                                                   |
|  [ 4-Channel Optocoupler Relays ]                                                 |
|     VCC -> 5V, GND -> GND                                                         |
|     IN1 (Light 1) --------> GPIO 10                                               |
|     IN2 (Fan) ------------> GPIO 11                                               |
|     IN3 (Bed Adjust) -----> GPIO 12                                               |
|     IN4 (Emergency Alarm) > GPIO 13                                               |
|                                                                                   |
|  [ Environmental Sensor Bus (I2C: SDA=GPIO 8, SCL=GPIO 9) ]                       |
|     - BMP280  (0x76) -> Temp, Pressure, Altitude                                  |
|     - SGP40   (0x59) -> VOC Air Quality Index                                     |
|     - INA219  (0x40) -> Voltage, Current, Power                                   |
|                                                                                   |
|  [ DHT11 Single-Bus Sensor ]                                                      |
|     DATA -----------------> GPIO 15 (with 4.7k Pull-up to 3.3V)                   |
|                                                                                   |
|  [ High-Speed UART Bridge ]                                                       |
|     GPIO 43 (TX) ---------> Arduino UNO Q RX (Pin 0)                              |
|     GPIO 44 (RX) <--------- Arduino UNO Q TX (Pin 1)                              |
|     GND ------------------> Arduino UNO Q GND                                     |
+-----------------------------------------------------------------------------------+
```

---

## 3. PCB Layout & Signal Integrity Recommendations

1. **I2C Bus Length & Pull-ups:**
   - Keep I2C traces under 10 cm between sensors on the hub PCB.
   - Use dedicated 4.7kΩ pull-up resistors to the 3.3V plane for SDA and SCL.
2. **RF Antenna Ground Plane:**
   - Keep the ground plane clearance around the 433MHz antenna pads at least 5mm to prevent signal detuning.
   - The 17.3cm wire should extend vertically away from battery leads and metal chassis.
3. **I2S Audio Noise Isolation:**
   - Route `BCLK`, `LRC`, and `DIN` with a solid ground return path.
   - Place a 100μF electrolytic capacitor and 0.1μF ceramic capacitor close to the `VDD` pin of the MAX98357A to eliminate pop/click noise during high volume bursts.
4. **Relay Coil Snubber Protection:**
   - The relay module features PC817 optocouplers. Keep the relay coil driving grounds separated from the sensitive ADC/sensor grounds to prevent EMI resets when switching 230V/110V AC inductive loads (such as fan motors).
