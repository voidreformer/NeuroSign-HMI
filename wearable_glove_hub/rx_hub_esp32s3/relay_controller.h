#pragma once
#include "config.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: 4-Channel Relay Controller (Home Automation & Safety Interlocks)
 * ============================================================================
 */

class RelayController {
public:
    RelayController();
    bool begin();
    void setRelay(uint8_t index, bool state);
    void toggleRelay(uint8_t index);
    bool getRelayState(uint8_t index) const;
    void updateTelemetry(SystemTelemetry &telemetry);
    void emergencyAllOff();
    void triggerEmergencyAlarm(bool state);

private:
    bool    _states[4];
    uint8_t _pins[4];
};
