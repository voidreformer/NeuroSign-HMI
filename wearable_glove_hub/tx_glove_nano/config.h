#pragma once
#include <Arduino.h>

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Transmitter Glove (TX) Configuration
 * TARGET MCU: Arduino Nano (ATmega328P, 16MHz, 5V / 3.3V)
 * ============================================================================
 */

// --- FIRMWARE IDENTITY ---
#define SYSTEM_NAME            "Neuro Sign"
#define SYSTEM_VERSION         "v2.4-IND"
#define SYSTEM_AUTHOR          "Rudra Attri Pandey"
#define DEVICE_ROLE            "TX_GLOVE_UNIT"
#define PROTOCOL_MAGIC_BYTE    0xAE  // Packet validation preamble

// --- PIN ASSIGNMENTS ---
// 3x Flex Sensors (Analog inputs with voltage divider 10k pull-down/pull-up)
#define PIN_FLEX_1             A0   // Flex Sensor 1: Thumb / Index finger
#define PIN_FLEX_2             A1   // Flex Sensor 2: Middle finger
#define PIN_FLEX_3             A2   // Flex Sensor 3: Ring / Pinky finger

// Battery / Supply Voltage Monitor (Analog divider)
#define PIN_BATTERY_MONITOR    A3   // Voltage divider from V_BAT

// 433 MHz RF Transmitter (FS1000A / RadioHead ASK Data pin)
#define PIN_RF_TX_DATA         12   // Digital Pin D12 for RF transmitter data

// I2C Pins for SSD1306 OLED & ADXL345 Accelerometer (Hardware I2C)
// Pin A4 -> SDA (I2C Data)
// Pin A5 -> SCL (I2C Clock)
#define OLED_I2C_ADDRESS       0x3C // 0.96" SSD1306 OLED I2C Address
#define ADXL345_I2C_ADDRESS    0x53 // ADXL345 Accelerometer (ALT ADDRESS pin grounded)

// Status LED (Optional on-board or external)
#define PIN_STATUS_LED         13   // Built-in LED for heartbeat/transmit pulse

// --- SENSOR CONFIGURATION & THRESHOLDS ---
#define NUM_FLEX_SENSORS       3
#define SENSOR_SAMPLE_WINDOW   8    // Moving average filter window size
#define CALIBRATION_SAMPLES    50   // Number of samples for power-on auto-zeroing

// ADXL345 Register Addresses
#define ADXL_REG_DEVID         0x00
#define ADXL_REG_POWER_CTL     0x2D
#define ADXL_REG_DATA_FORMAT   0x31
#define ADXL_REG_DATAX0        0x32

// --- TRANSMISSION TIMING & PARAMETERS ---
#define RF_BAUD_RATE           2000 // 2000 bps ASK modulation
#define TX_INTERVAL_MS         70   // Transmit telemetry packet every 70ms (~14 Hz)
#define DISPLAY_FPS            20   // OLED Refresh target (20 FPS)

// --- TELEMETRY PACKET STRUCTURE (Packed for RF bandwidth efficiency) ---
#pragma pack(push, 1)
struct NeuroTxPacket {
    uint8_t  preamble;       // 0xAE (Magic start byte)
    uint8_t  sequenceId;     // Incremental packet counter (0-255)
    uint8_t  flex1;          // Flex sensor 1 normalized (0-100%)
    uint8_t  flex2;          // Flex sensor 2 normalized (0-100%)
    uint8_t  flex3;          // Flex sensor 3 normalized (0-100%)
    int8_t   pitch;          // Hand Pitch angle in degrees (-90 to +90)
    int8_t   roll;           // Hand Roll angle in degrees (-90 to +90)
    uint8_t  tremorLevel;    // High-frequency jerk/tremor intensity (0-100)
    uint8_t  batteryPercent; // Battery percentage (0-100%)
    uint8_t  gestureHint;    // Pre-evaluated gesture ID (0 = Idle, 1 = Help, etc.)
    uint8_t  checksum;       // 8-bit XOR/CRC checksum
};
#pragma pack(pop)
