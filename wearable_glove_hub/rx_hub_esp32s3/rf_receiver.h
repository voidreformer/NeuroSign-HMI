#pragma once
#include "config.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Native ESP32-S3 433 MHz RF ASK Demodulator (Zero AVR Dependencies)
 * ============================================================================
 */

class RfReceiver {
public:
    RfReceiver();
    bool begin();
    bool pollPacket(NeuroTxPacket &outPacket);
    void updateLinkStats(SystemTelemetry &telemetry);

private:
    uint8_t  _lastSequenceId;
    uint32_t _lastPacketReceivedTime;
    uint32_t _totalReceivedCount;
    uint32_t _totalDroppedCount;
    uint8_t  _linkQuality;

    uint8_t calculateChecksum(const NeuroTxPacket &pkt);
};
