# Hardware Wiring & Pinout Guide: "Neuro Sign"
**Developer:** Rudra Attri Pandey  
**System Version:** v2.4-IND

---

## 1. Transmitter Glove (TX Module) - Arduino Nano

| Component | Component Pin | Arduino Nano Pin | Notes / Recommended Values |
| :--- | :--- | :--- | :--- |
| **Flex Sensor 1 (Thumb)** | Pin 1 (VCC) / Pin 2 (Sig) | **A0** | Voltage divider with 10kΩ resistor to GND |
| **Flex Sensor 2 (Index)** | Pin 1 (VCC) / Pin 2 (Sig) | **A1** | Voltage divider with 10kΩ resistor to GND |
| **Flex Sensor 3 (Middle)**| Pin 1 (VCC) / Pin 2 (Sig) | **A2** | Voltage divider with 10kΩ resistor to GND |
| **Battery Voltage Divider**| Center Tap | **A3** | 10kΩ / 10kΩ divider from LiPo battery (+) |
| **ADXL345 Accelerometer**| VCC | **3.3V** | Operating voltage: 3.3V |
| | GND | **GND** | Ground |
| | SDA | **A4 (SDA)** | Shared I2C Data bus (4.7kΩ pull-up to 3.3V) |
| | SCL | **A5 (SCL)** | Shared I2C Clock bus (4.7kΩ pull-up to 3.3V) |
| | SDO / ALT_ADDR | **GND** | Sets I2C address to `0x53` |
| | CS | **3.3V** | Selects I2C Mode |
| **0.96" SSD1306 OLED** | VCC | **5V / 3.3V** | Standard I2C OLED display |
| | GND | **GND** | Ground |
| | SDA | **A4 (SDA)** | Shared I2C Data bus |
| | SCL | **A5 (SCL)** | Shared I2C Clock bus |
| **433 MHz RF Transmitter**| VCC | **5V** | FS1000A / RadioHead Transmitter |
| | GND | **GND** | Ground |
| | DATA | **D12** | RF ASK Data line |
| | ANT | **17.3 cm Wire** | 1/4 wavelength antenna (22 AWG copper wire) |

---

## 2. Receiver & Medical Hub (RX Module) - ESP32-S3

| Component | Component Pin | ESP32-S3 Pin | Notes / Recommended Values |
| :--- | :--- | :--- | :--- |
| **433 MHz RF Receiver** | VCC | **5V** | Superheterodyne Receiver (RX470 / SYN480R) |
| | GND | **GND** | Ground |
| | DATA | **GPIO 4** | RF ASK Receiver Data Line |
| | ANT | **17.3 cm Wire**| 1/4 wavelength antenna for optimal range |
| **4-Channel Relay Module**| VCC | **5V** | External 5V rail (isolated relay supply) |
| | GND | **GND** | Common Ground |
| | IN1 (Light 1) | **GPIO 10** | Optocoupler Active LOW |
| | IN2 (Fan) | **GPIO 11** | Optocoupler Active LOW |
| | IN3 (Bed Adjust) | **GPIO 12** | Optocoupler Active LOW |
| | IN4 (Emergency Alarm)| **GPIO 13** | Optocoupler Active LOW |
| **MAX98357A I2S Amplifier**| VDD | **5V** | 3W Class-D Mono DAC/Amp |
| | GND | **GND** | Ground |
| | BCLK | **GPIO 16** | I2S Bit Clock |
| | LRC / WS | **GPIO 17** | I2S Left/Right Word Select Clock |
| | DIN | **GPIO 18** | I2S Serial Audio Data |
| | GAIN | **GND / 100kΩ** | GND = 9dB, Open = 12dB, 100k to GND = 15dB |
| | SD_MODE | **Open / VDD** | Left channel / Stereo downmix |
| **MicroSD Card Module** | VCC | **3.3V / 5V** | FAT32 Formatted Voice MP3/WAV storage |
| | GND | **GND** | Ground |
| | CS | **GPIO 5** | SPI Chip Select |
| | MOSI | **GPIO 6** | SPI Master Out Slave In |
| | SCK | **GPIO 7** | SPI Serial Clock |
| | MISO | **GPIO 21** | SPI Master In Slave Out |
| **DHT11 Temp & Humidity** | VCC | **3.3V / 5V** | Ambient sensor |
| | DATA | **GPIO 15** | 4.7kΩ pull-up resistor to VCC |
| | GND | **GND** | Ground |
| **BMP280 Barometer** | VCC | **3.3V** | Pressure & Altitude |
| | GND | **GND** | Ground |
| | SDA | **GPIO 8** | Shared I2C Data bus |
| | SCL | **GPIO 9** | Shared I2C Clock bus |
| | SDO | **GND** | Sets I2C Address to `0x76` |
| **SGP40 VOC / AQI Sensor**| VCC | **3.3V** | Indoor Air Quality |
| | GND | **GND** | Ground |
| | SDA | **GPIO 8** | Shared I2C Data bus (`0x59`) |
| | SCL | **GPIO 9** | Shared I2C Clock bus |
| **INA219 Power Monitor** | VCC | **3.3V** | High-side Voltage/Current Sensor |
| | GND | **GND** | Ground |
| | SDA | **GPIO 8** | Shared I2C Data bus (`0x40`) |
| | SCL | **GPIO 9** | Shared I2C Clock bus |
| | VIN+ | **5V Supply In** | Power bus positive before load |
| | VIN- | **5V Hub Rail** | Power bus after shunt resistor |
| **UART to Arduino UNO Q**| TX | **GPIO 43** | Connects to Arduino UNO Q RX (Pin 0) |
| | RX | **GPIO 44** | Connects to Arduino UNO Q TX (Pin 1) |

---

## 3. Power Distribution & Safety Interlocks

1. **Glove Power (TX):**
   - 3.7V 850mAh LiPo battery with TP4056 USB-C charging board and MT3608 boost converter (boosting to 5.0V for Nano and 433MHz RF transmitter) or direct 3.3V step-down regulator for the ADXL345.
2. **Hub Power (RX):**
   - Regulated 5.0V 3.0A DC power supply connected through the INA219 current shunt.
   - Separate 5V branch for the 4-channel relay coil power to prevent voltage dips when switching inductors.
   - Flyback diodes and optocouplers on the relay board provide galvanic isolation between the mains AC loads and the ESP32-S3.
