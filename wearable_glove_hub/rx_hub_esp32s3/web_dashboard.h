#pragma once
#include "config.h"
#include "audio_engine.h"
#include "relay_controller.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Embedded Web Server & Real-Time WebSockets Telemetry Hub (192.168.4.1)
 * ============================================================================
 */

class WebDashboard {
public:
    WebDashboard();
    bool begin(AudioEngine *audio, RelayController *relays);
    void update(const SystemTelemetry &telemetry);
    void handleClient();

private:
    AudioEngine     *_audio;
    RelayController *_relays;
    uint32_t         _lastWsBroadcast;

    void setupSoftAP();
    void setupHttpRoutes();
    void broadcastTelemetry(const SystemTelemetry &telemetry);
};
