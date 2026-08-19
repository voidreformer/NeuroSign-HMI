/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Main Receiver Hub & Base Station (RX)
 * TARGET HARDWARE: ESP32-S3 (Dual-Core Xtensa LX7, 240MHz)
 * 
 * SUBSYSTEMS & HARDWARE:
 *  - 433 MHz Superheterodyne RF Receiver on GPIO 4
 *  - MAX98357A I2S Mono 3W Class-D Amp (BCLK:16, LRC:17, DIN:18)
 *  - 4-Channel Optocoupler Relay Module on GPIO 10, 11, 12, 13
 *  - DHT11 Temperature & Humidity on GPIO 15
 *  - BMP280 Barometric Pressure & Altitude on I2C (SDA:8, SCL:9)
 *  - Sensirion SGP40 Indoor Air Quality (VOC Index) on I2C
 *  - INA219 Voltage, Current & Power Consumption Monitor on I2C
 *  - TinyML Neuro AI Gesture Classifier & Spasm Tremor Anomaly Detector
 *  - SoftAP WiFi Captive Portal + Real-Time WebSockets HUD (192.168.4.1)
 *  - High-Speed UART Bridge to Arduino UNO Q / Live Monitor (GPIO 43/44)
 * ============================================================================
 */

#include "config.h"
#include "rf_receiver.h"
#include "audio_engine.h"
#include "sensor_manager.h"
#include "relay_controller.h"
#include "neuro_ai_engine.h"
#include "web_dashboard.h"
#include "uart_streamer.h"

// System Singletons
RfReceiver      rfReceiver;
AudioEngine     audioEngine;
SensorManager   sensorManager;
RelayController relayController;
NeuroAiEngine   neuroAi;
WebDashboard    webDashboard;
UartStreamer    uartStreamer;

// Shared Telemetry State
SystemTelemetry g_telemetry;
portMUX_TYPE    g_telemetryMutex = portMUX_INITIALIZER_UNLOCKED;

// FreeRTOS Task Handles for Dual-Core Scheduling
TaskHandle_t TaskCore0Handle = NULL;

// Core 0 Task: High-Frequency RF Packet Polling & Audio I2S DMA Updates
void TaskCore0_RF_Audio(void *pvParameters) {
    NeuroTxPacket rxPkt;

    while (true) {
        // 1. Poll 433 MHz RF Receiver
        if (rfReceiver.pollPacket(rxPkt)) {
            taskENTER_CRITICAL(&g_telemetryMutex);
            g_telemetry.flex[0]  = rxPkt.flex1;
            g_telemetry.flex[1]  = rxPkt.flex2;
            g_telemetry.flex[2]  = rxPkt.flex3;
            g_telemetry.pitch    = rxPkt.pitch;
            g_telemetry.roll     = rxPkt.roll;
            g_telemetry.tremor   = rxPkt.tremorLevel;
            g_telemetry.battery  = rxPkt.batteryPercent;
            taskEXIT_CRITICAL(&g_telemetryMutex);

            // Pass sample into Neuro AI classifier
            neuroAi.processSample(rxPkt, g_telemetry);
        }

        // Update RF connection health & quality metrics
        rfReceiver.updateLinkStats(g_telemetry);

        // 2. Audio Engine Synthesis Step
        audioEngine.update();

        // 1ms yield to FreeRTOS scheduler
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println(F("\n========================================================"));
    Serial.println(F("           NEURO SIGN - PARALYSIS ASSIST HUB           "));
    Serial.println(F("         Developed by: Rudra Attri Pandey               "));
    Serial.println(F("         Firmware Version: " SYSTEM_VERSION "         "));
    Serial.println(F("         Hardware: ESP32-S3 Dual-Core Xtensa LX7        "));
    Serial.println(F("========================================================\n"));

    // 1. Initialize Relays (Failsafe boot state: all off)
    relayController.begin();
    Serial.println(F("[OK] 4-Channel Optocoupler Relays Initialized (GPIO 10,11,12,13)."));

    // 2. Initialize MAX98357A I2S Audio Engine
    if (audioEngine.begin()) {
        Serial.println(F("[OK] MAX98357A I2S Audio Engine Ready (BCLK:16, LRC:17, DIN:18)."));
    }

    // 3. Initialize Multi-Sensor Diagnostic Hub (DHT11, BMP280, SGP40, INA219)
    sensorManager.begin();
    Serial.println(F("[OK] Sensor Hub Active (DHT11, BMP280, SGP40, INA219 on I2C 8/9)."));

    // 4. Initialize 433 MHz RF Superheterodyne Receiver
    if (rfReceiver.begin()) {
        Serial.println(F("[OK] 433 MHz RF Superheterodyne Receiver Ready on GPIO 4."));
    }

    // 5. Initialize Neuro AI TinyML Classifier
    neuroAi.begin(&audioEngine, &relayController);
    Serial.println(F("[OK] TinyML Neuro AI Engine Loaded (Centroids & Spasm Detector)."));

    // 6. Initialize SoftAP WiFi & Web Dashboard (192.168.4.1)
    webDashboard.begin(&audioEngine, &relayController);
    Serial.println(F("[OK] WiFi SoftAP 'NeuroSign_Hub' Started. Static IP: 192.168.4.1"));

    // 7. Initialize High-Speed UART Bridge for Arduino UNO Q
    uartStreamer.begin();
    Serial.println(F("[OK] High-Speed UART Telemetry Bridge Ready (GPIO 43/44, 115200 baud)."));

    // Initialize Default Telemetry Structure
    memset(&g_telemetry, 0, sizeof(SystemTelemetry));
    strncpy(g_telemetry.gestureName, "NEUTRAL / RESTING", sizeof(g_telemetry.gestureName));
    g_telemetry.gestureConfidence = 0.95f;
    g_telemetry.busVoltageV = 5.0f;

    // 8. Launch Core 0 Dedicated Task for RF & Audio
    xTaskCreatePinnedToCore(
        TaskCore0_RF_Audio,
        "Task_RF_Audio",
        8192,
        NULL,
        2, // High priority
        &TaskCore0Handle,
        0  // Pinned to Core 0
    );

    Serial.println(F("\n[SYSTEM] Neuro Sign Hub Online. Connect WiFi to 'NeuroSign_Hub' and browse to http://192.168.4.1\n"));
}

void loop() {
    // Loop runs on Core 1: Sensors, Web Server, WebSockets, UART Stream
    
    // 1. Poll Environmental & Electrical Sensors
    sensorManager.update(g_telemetry);

    // 2. Sync Relay States to Telemetry
    relayController.updateTelemetry(g_telemetry);

    // 3. Update Web Dashboard & WebSockets Broadcast (192.168.4.1)
    webDashboard.update(g_telemetry);

    // 4. Stream Telemetry over UART to Arduino UNO Q / Live Monitor
    uartStreamer.streamTelemetry(g_telemetry);

    delay(10); // Core 1 cooperative yield
}
