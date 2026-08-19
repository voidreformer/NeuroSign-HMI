/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Main Transmitter Sketch (TX Glove)
 * TARGET HARDWARE: Arduino Nano (ATmega328P)
 * 
 * SENSORS & HARDWARE:
 *  - 3x Flex Sensors on A0, A1, A2
 *  - ADXL345 3-Axis Digital Accelerometer on I2C (A4-SDA, A5-SCL)
 *  - 0.96" SSD1306 OLED (128x64) on I2C (A4-SDA, A5-SCL)
 *  - 433 MHz RF Transmitter (FS1000A) on Digital Pin D12
 *  - Battery Monitor on A3
 * ============================================================================
 */

#include "config.h"
#include "gesture_sensors.h"
#include "oled_display.h"
#include "rf_transmitter.h"

// System Singletons
GestureSensors sensors;
OledDisplay    display;
RfTransmitter  transmitter;

// Runtime state variables
uint8_t       g_packetSequence = 0;
unsigned long g_lastTxTime     = 0;
unsigned long g_lastOledTime   = 0;
bool          g_lastTxBurst    = false;

void setup() {
    Serial.begin(115200);
    Serial.println(F("\n=========================================="));
    Serial.println(F("  NEURO SIGN - PARALYSIS ASSIST (TX)     "));
    Serial.println(F("  Developed by: Rudra Attri Pandey        "));
    Serial.println(F("  Firmware: " SYSTEM_VERSION "               "));
    Serial.println(F("==========================================\n"));

    // 1. Initialize OLED Display & show splash screen
    if (!display.begin()) {
        Serial.println(F("[ERROR] SSD1306 OLED initialization failed! Check I2C wiring (A4/A5)."));
    } else {
        Serial.println(F("[OK] SSD1306 OLED Initialized (0x3C)."));
    }

    // 2. Perform Sensor Auto-Calibration with visual progress bar
    Serial.println(F("[INFO] Starting Flex & ADXL345 calibration..."));
    for (uint8_t step = 0; step <= 100; step += 20) {
        display.showCalibrationScreen(step);
        delay(60);
    }

    if (!sensors.begin()) {
        Serial.println(F("[WARN] ADXL345 Accelerometer not responding at 0x53. Using fallback tilt."));
    } else {
        Serial.println(F("[OK] ADXL345 3-Axis Accelerometer Initialized."));
    }

    // 3. Initialize 433 MHz RF Transmitter
    if (!transmitter.begin()) {
        Serial.println(F("[ERROR] 433 MHz RF Transmitter initialization failed!"));
    } else {
        Serial.println(F("[OK] 433 MHz RF Transmitter Ready on D12 (2000 bps)."));
    }

    Serial.println(F("[SYSTEM] TX Glove System Ready. Commencing transmission loop.\n"));
}

void loop() {
    unsigned long currentMillis = millis();

    // 1. High-frequency sensor sample update (~100 Hz)
    sensors.update();
    const GloveSensorData &data = sensors.getData();

    // 2. RF Telemetry Transmission Burst (~14 Hz / 70ms interval)
    if (currentMillis - g_lastTxTime >= TX_INTERVAL_MS) {
        g_lastTxTime = currentMillis;
        g_lastTxBurst = transmitter.sendTelemetry(data, g_packetSequence);

        // Optional debug serial output
        #if 1
        Serial.print(F("[TX #"));
        Serial.print(g_packetSequence);
        Serial.print(F("] F1:"));
        Serial.print(data.flexPercent[0]);
        Serial.print(F("% F2:"));
        Serial.print(data.flexPercent[1]);
        Serial.print(F("% F3:"));
        Serial.print(data.flexPercent[2]);
        Serial.print(F("% | P:"));
        Serial.print(data.pitch);
        Serial.print(F(" R:"));
        Serial.print(data.roll);
        Serial.print(F(" | Tremor:"));
        Serial.print(data.tremorLevel);
        Serial.print(F(" | G:"));
        Serial.println(data.rawGestureId);
        #endif
    }

    // 3. OLED HUD & Animated Signal Tower update (20 FPS / 50ms interval)
    if (currentMillis - g_lastOledTime >= (1000 / DISPLAY_FPS)) {
        g_lastOledTime = currentMillis;
        display.update(data, g_packetSequence, g_lastTxBurst);
    }
}
