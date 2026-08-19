#pragma once
#include <Arduino.h>

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Receiver Hub (RX) Configuration
 * TARGET MCU: ESP32-S3 (Dual-Core Xtensa LX7, 240MHz, 8MB Flash / 2MB PSRAM)
 * ============================================================================
 */

// --- FIRMWARE IDENTITY ---
#define SYSTEM_NAME             "Neuro Sign"
#define SYSTEM_VERSION          "v2.4-IND"
#define SYSTEM_AUTHOR           "Rudra Attri Pandey"
#define DEVICE_ROLE             "RX_BASE_STATION_HUB"
#define PROTOCOL_MAGIC_BYTE     0xAE

// --- PIN ASSIGNMENTS (ESP32-S3) ---

// 433 MHz RF Receiver Data Pin
#define PIN_RF_RX_DATA          4    // GPIO 4 for 433MHz Superheterodyne RX

// 4-Channel Optocoupler Relay Module
#define PIN_RELAY_1             10   // Relay 1: Room Light 1
#define PIN_RELAY_2             11   // Relay 2: Room Fan
#define PIN_RELAY_3             12   // Relay 3: Bed Position / Aux Actuator
#define PIN_RELAY_4             13   // Relay 4: Emergency Alarm / Buzzer
#define RELAY_ACTIVE_LEVEL      LOW  // Active LOW for standard optocoupler boards

// I2S Digital Audio Output (MAX98357A 3W Class-D Mono Amp)
#define PIN_I2S_BCLK            16   // I2S Bit Clock (BCLK)
#define PIN_I2S_LRC             17   // I2S Left/Right Clock (WS / Frame Sync)
#define PIN_I2S_DIN             18   // I2S Serial Data Out (DIN)

// MicroSD Card Module (SPI Interface) for Pre-Recorded Voice Prompts (.WAV / .MP3)
#define PIN_SD_CS               5    // MicroSD SPI Chip Select (CS)
#define PIN_SD_MOSI             6    // MicroSD SPI MOSI
#define PIN_SD_SCK              7    // MicroSD SPI SCK (Clock)
#define PIN_SD_MISO             21   // MicroSD SPI MISO

// DHT11 Temperature & Humidity Sensor
#define PIN_DHT11               15   // GPIO 15 for DHT11 Single-Bus data

// I2C Bus for Environmental & Electrical Diagnostic Sensors
// (BMP280, SGP40, INA219)
#define PIN_I2C_SDA             8    // ESP32-S3 I2C SDA
#define PIN_I2C_SCL             9    // ESP32-S3 I2C SCL
#define I2C_BUS_FREQ_HZ         400000

// I2C Sensor Addresses
#define ADDR_BMP280_1           0x76 // BMP280 Primary Address (SDO -> GND)
#define ADDR_BMP280_2           0x77 // BMP280 Alternate Address (SDO -> VCC)
#define ADDR_SGP40              0x59 // Sensirion SGP40 VOC Sensor
#define ADDR_INA219             0x40 // INA219 Power Monitor

// Hardware UART Bridge for Arduino UNO Q / Live Monitor
#define PIN_UART_UNO_TX         43   // ESP32-S3 TX -> Arduino UNO Q RX
#define PIN_UART_UNO_RX         44   // ESP32-S3 RX <- Arduino UNO Q TX
#define UART_STREAM_BAUD        115200

// Built-in / Status NeoPixel LED
#define PIN_STATUS_RGB          48   // Onboard RGB LED on ESP32-S3 dev boards

// --- WIFI SOFTAP & NETWORK CONFIGURATION ---
#define WIFI_AP_SSID            "NeuroSign_Hub"
#define WIFI_AP_PASS            "neurosign2026"
#define STATIC_IP_ADDR          192, 168, 4, 1
#define STATIC_IP_GATEWAY       192, 168, 4, 1
#define STATIC_IP_SUBNET        255, 255, 255, 0
#define WEB_SERVER_PORT         80
#define WEBSOCKET_PORT          81

// --- TIMING CONSTANTS ---
#define SENSOR_POLL_INTERVAL_MS 1000 // Poll DHT11, BMP280, SGP40, INA219 every 1 sec
#define WS_BROADCAST_RATE_MS    50   // Broadcast WebSocket telemetry every 50ms (20 Hz)
#define UART_STREAM_RATE_MS     50   // Stream UART packets to Arduino UNO Q at 20 Hz
#define RF_RX_TIMEOUT_MS        1500 // Mark RF link disconnected if no packet in 1.5s

// --- TELEMETRY PACKET STRUCTURE (Matched with TX Nano) ---
#pragma pack(push, 1)
struct NeuroTxPacket {
    uint8_t  preamble;
    uint8_t  sequenceId;
    uint8_t  flex1;
    uint8_t  flex2;
    uint8_t  flex3;
    int8_t   pitch;
    int8_t   roll;
    uint8_t  tremorLevel;
    uint8_t  batteryPercent;
    uint8_t  gestureHint;
    uint8_t  checksum;
};
#pragma pack(pop)

// --- SYSTEM TELEMETRY STATE STRUCT ---
struct SystemTelemetry {
    // TX Glove telemetry
    bool     rfConnected;
    uint8_t  rfSignalQuality;   // 0 - 100%
    uint32_t packetsReceived;
    uint32_t packetsDropped;
    uint8_t  flex[3];
    int8_t   pitch;
    int8_t   roll;
    uint8_t  tremor;
    uint8_t  battery;
    uint8_t  gestureId;
    char     gestureName[32];
    float    gestureConfidence;

    // Environmental readings
    float    temperatureC;
    float    humidityPercent;
    float    pressureHpa;
    float    altitudeMeters;
    int32_t  vocIndex;          // SGP40 VOC Index (1 - 500)

    // Electrical Power readings (INA219)
    float    busVoltageV;
    float    currentMA;
    float    powerMW;

    // Relay States (True = ON, False = OFF)
    bool     relayState[4];

    // System metrics
    uint32_t uptimeSeconds;
    uint32_t freeHeapBytes;
    bool     spasmAlertActive;
    char     lastAlertMessage[64];
    uint32_t lastAlertTimestamp;
};
