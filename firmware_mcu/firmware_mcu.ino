// ==============================================================================
// NeuroSign-HMI Max: STM32U585 Microcontroller Firmware (Zephyr RTOS / Arduino Core)
// Handles: HLK-LD2410C Radar, SG90 Pan-Tilt, SIM800C GSM, Sensor Bus,
//          8x13 LED Matrix, Opto-Relays, and MessagePack IPC Bridge
// ==============================================================================

#include <Arduino.h>
#include <Modulino.h>
#include <Arduino_LED_Matrix.h>
#include "arduino_bridge.h"

#include "RadarDriver.h"
#include "ServoTracker.h"
#include "GSM_Emergency.h"
#include "SensorBus.h"
#include "MatrixDisplay.h"
#include "RelayActuator.h"

// ---------------------------------------------------------------------------
// Global Subsystem Instances
// ---------------------------------------------------------------------------
RadarDriver       radar(Serial2);          // HLK-LD2410C on UART2 (D0/D1)
ServoTracker      servos(9, 10);           // SG90 Pan (D9/TIM1_CH1) & Tilt (D10/TIM1_CH2)
GSMEmergency      gsm(Serial3);            // SIM800C on UART3 (D8/D11)
SensorBus         sensors;                 // SGP40, INA219, MPU-6050, DHT22 on I2C / D4
MatrixDisplay     matrix;                  // 8x13 Blue LED Matrix via built-in lib
RelayActuator     relays(6, 7);            // Relay Ch1 (D6 = Lights), Ch2 (D7 = Alarm)

// ---------------------------------------------------------------------------
// IPC Provider Callbacks — Called by Qualcomm MPU over Unix Domain Socket RPC
// ---------------------------------------------------------------------------

/**
 * @brief Commanded by MPU to actuate a relay channel.
 *        relay_id: 1 = Room Light, 2 = Emergency Alarm/Strobe
 *        state:    1 = ON,         0 = OFF
 */
void on_mcu_set_relay(int relay_id, int state) {
    bool on = (state != 0);
    if (relay_id == 1) {
        relays.setChannel(1, on);
        matrix.showGlyph(on ? GLYPH_RELAY_ON : GLYPH_IDLE);
        Serial.printf("[RELAY] Channel 1 (Light) -> %s\n", on ? "ON" : "OFF");
    } else if (relay_id == 2) {
        relays.setChannel(2, on);
        matrix.showGlyph(on ? GLYPH_EMERGENCY : GLYPH_IDLE);
        Serial.printf("[RELAY] Channel 2 (Alarm) -> %s\n", on ? "ON" : "OFF");
    }
}

/**
 * @brief Commanded by MPU to pan and tilt the SG90 camera servos.
 *        pan_angle:  0-180 degrees (horizontal sweep)
 *        tilt_angle: 0-180 degrees (vertical elevation)
 */
void on_mcu_set_pan_tilt(int pan_angle, int tilt_angle) {
    servos.setAbsoluteAngles(pan_angle, tilt_angle);
}

/**
 * @brief Commanded by MPU to dispatch an offline SMS via SIM800C.
 *        phone: E.164-formatted phone string (e.g. "+919876543210")
 *        msg:   Plain text body (max 160 chars)
 */
void on_mcu_send_sms(const char* phone, const char* msg) {
    Serial.printf("[GSM] Dispatching SOS SMS to %s\n", phone);
    matrix.showGlyph(GLYPH_EMERGENCY);
    gsm.sendSMS(phone, msg);
}

/**
 * @brief Commanded by MPU to change the 8x13 LED Matrix iconography.
 *        glyph_id: 0=IDLE, 1=GESTURE_OK, 2=EMERGENCY_SOS, 3=SPEAKING, 4=LISTENING
 */
void on_mcu_set_glyph(int glyph_id) {
    matrix.showGlyph(static_cast<GlyphType>(glyph_id));
}

// ---------------------------------------------------------------------------
// Radar Presence Reporting — Pushes to MPU as async notification
// ---------------------------------------------------------------------------
void report_radar_telemetry() {
    static uint32_t last_report_ms = 0;
    if (millis() - last_report_ms < 250) return;  // Report at 4 Hz max
    last_report_ms = millis();

    bool present        = radar.isPresent();
    uint16_t dist_cm    = radar.getDistanceCm();
    uint8_t energy      = radar.getEnergy();

    Bridge.notify("radar_telemetry_event", (int)present, (int)dist_cm, (int)energy);
}

// ---------------------------------------------------------------------------
// Sensor Telemetry Reporting — Aggregated & sent to MPU
// ---------------------------------------------------------------------------
void report_sensor_telemetry() {
    static uint32_t last_report_ms = 0;
    if (millis() - last_report_ms < 2000) return;  // Report at 0.5 Hz
    last_report_ms = millis();

    SensorData data = sensors.read();
    Bridge.notify("sensor_bus_event",
        (int)data.voc_index,
        data.bus_volts,
        data.current_ma,
        data.temp_c,
        data.humidity
    );
}

// ---------------------------------------------------------------------------
// Arduino Setup
// ---------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    Serial.println("==============================================");
    Serial.println(" NeuroSign-HMI Max — STM32U585 Firmware v1.0");
    Serial.println("==============================================");

    // Initialize IPC Bridge to Qualcomm MPU
    Bridge.begin();

    // Register inbound RPC service endpoints
    Bridge.provide("mcu_set_relay",    on_mcu_set_relay);
    Bridge.provide("mcu_set_pan_tilt", on_mcu_set_pan_tilt);
    Bridge.provide("mcu_send_sms",     on_mcu_send_sms);
    Bridge.provide("mcu_set_glyph",    on_mcu_set_glyph);

    // Initialize hardware subsystems
    radar.begin(115200);
    servos.begin();
    servos.setAbsoluteAngles(90, 90);  // Center position

    gsm.begin(9600);
    sensors.begin();
    matrix.begin();
    relays.begin();

    // Boot-complete visual acknowledgement
    matrix.showGlyph(GLYPH_GESTURE_OK);
    delay(800);
    matrix.showGlyph(GLYPH_IDLE);

    Serial.println("[INIT] All subsystems ready. Bridge IPC active.");
}

// ---------------------------------------------------------------------------
// Arduino Main Loop — 1 kHz deterministic execution (Zephyr RTOS scheduled)
// ---------------------------------------------------------------------------
void loop() {
    // 1. Poll HLK-LD2410C Radar UART stream
    radar.update();

    // 2. Update servo position (smooth interpolation step)
    servos.update();

    // 3. Process Bridge RPC inbound queue
    Bridge.update();

    // 4. Push telemetry to MPU at scheduled intervals
    report_radar_telemetry();
    report_sensor_telemetry();

    // 5. Enforce relay auto-shutoff timers
    relays.update();

    delayMicroseconds(800);  // ~1 kHz tick (800 µs + overhead ≈ 1 ms)
}
