#pragma once
#include "config.h"
#include "gesture_sensors.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Native 433 MHz RF Pulse Transmitter (Zero External Dependency)
 * ============================================================================
 */

class RfTransmitter {
public:
    RfTransmitter();
    bool begin();
    bool sendTelemetry(const GloveSensorData &sensorData, uint8_t &packetCounter);

private:
    uint8_t calculateChecksum(const NeuroTxPacket &pkt);
    void sendBit(bool bit);
    void sendByte(uint8_t b);
};
