#include "rf_transmitter.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Native 433 MHz RF Pulse Transmitter Implementation
 * ============================================================================
 */

// Timing constants in microseconds (matched with ESP32-S3 RX)
#define PREAMBLE_PULSE_US   400
#define PREAMBLE_COUNT      8
#define SYNC_HIGH_US        1200
#define SYNC_LOW_US         400
#define BIT0_HIGH_US        300
#define BIT0_LOW_US         600
#define BIT1_HIGH_US        600
#define BIT1_LOW_US         300

RfTransmitter::RfTransmitter() {
}

bool RfTransmitter::begin() {
    pinMode(PIN_RF_TX_DATA, OUTPUT);
    digitalWrite(PIN_RF_TX_DATA, LOW);
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);
    return true;
}

uint8_t RfTransmitter::calculateChecksum(const NeuroTxPacket &pkt) {
    const uint8_t* ptr = (const uint8_t*)&pkt;
    uint8_t crc = 0xAA;
    for (size_t i = 0; i < sizeof(NeuroTxPacket) - 1; i++) {
        crc ^= ptr[i];
        crc = (crc << 1) | (crc >> 7);
    }
    return crc;
}

void RfTransmitter::sendBit(bool bit) {
    if (bit) {
        // Bit 1: 600us HIGH, 300us LOW
        digitalWrite(PIN_RF_TX_DATA, HIGH);
        delayMicroseconds(BIT1_HIGH_US);
        digitalWrite(PIN_RF_TX_DATA, LOW);
        delayMicroseconds(BIT1_LOW_US);
    } else {
        // Bit 0: 300us HIGH, 600us LOW
        digitalWrite(PIN_RF_TX_DATA, HIGH);
        delayMicroseconds(BIT0_HIGH_US);
        digitalWrite(PIN_RF_TX_DATA, LOW);
        delayMicroseconds(BIT0_LOW_US);
    }
}

void RfTransmitter::sendByte(uint8_t b) {
    for (int i = 7; i >= 0; i--) {
        sendBit((b >> i) & 0x01);
    }
}

bool RfTransmitter::sendTelemetry(const GloveSensorData &sensorData, uint8_t &packetCounter) {
    NeuroTxPacket pkt;
    pkt.preamble       = PROTOCOL_MAGIC_BYTE;
    pkt.sequenceId     = ++packetCounter;
    pkt.flex1          = sensorData.flexPercent[0];
    pkt.flex2          = sensorData.flexPercent[1];
    pkt.flex3          = sensorData.flexPercent[2];
    pkt.pitch          = sensorData.pitch;
    pkt.roll           = sensorData.roll;
    pkt.tremorLevel    = sensorData.tremorLevel;
    pkt.batteryPercent = sensorData.batteryPercent;
    pkt.gestureHint    = sensorData.rawGestureId;
    pkt.checksum       = calculateChecksum(pkt);

    // Visual LED heartbeat pulse
    digitalWrite(PIN_STATUS_LED, HIGH);

    noInterrupts(); // Protect microsecond pulse timing

    // 1. AGC Training Preamble (wakes up receiver AGC circuit)
    for (int i = 0; i < PREAMBLE_COUNT; i++) {
        digitalWrite(PIN_RF_TX_DATA, HIGH);
        delayMicroseconds(PREAMBLE_PULSE_US);
        digitalWrite(PIN_RF_TX_DATA, LOW);
        delayMicroseconds(PREAMBLE_PULSE_US);
    }

    // 2. Sync Frame Delimiter
    digitalWrite(PIN_RF_TX_DATA, HIGH);
    delayMicroseconds(SYNC_HIGH_US);
    digitalWrite(PIN_RF_TX_DATA, LOW);
    delayMicroseconds(SYNC_LOW_US);

    // 3. Send 11-byte Payload
    const uint8_t* ptr = (const uint8_t*)&pkt;
    for (size_t i = 0; i < sizeof(NeuroTxPacket); i++) {
        sendByte(ptr[i]);
    }

    // Inter-frame gap (LOW line)
    digitalWrite(PIN_RF_TX_DATA, LOW);

    interrupts();

    digitalWrite(PIN_STATUS_LED, LOW);
    return true;
}
