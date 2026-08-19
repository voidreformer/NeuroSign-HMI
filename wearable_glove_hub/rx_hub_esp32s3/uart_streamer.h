#pragma once
#include "config.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: High-Speed UART Telemetry Streamer (ESP32-S3 to Arduino UNO Q / Monitor)
 * ============================================================================
 */

class UartStreamer {
public:
    UartStreamer();
    bool begin();
    void streamTelemetry(const SystemTelemetry &telemetry);

private:
    uint32_t _lastStreamTime;
    uint32_t _frameCounter;
};
