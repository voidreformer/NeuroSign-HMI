#include "relay_controller.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: 4-Channel Relay Controller Implementation
 * ============================================================================
 */

RelayController::RelayController() {
    _pins[0] = PIN_RELAY_1;
    _pins[1] = PIN_RELAY_2;
    _pins[2] = PIN_RELAY_3;
    _pins[3] = PIN_RELAY_4;

    for (int i = 0; i < 4; i++) {
        _states[i] = false;
    }
}

bool RelayController::begin() {
    for (int i = 0; i < 4; i++) {
        pinMode(_pins[i], OUTPUT);
        // Turn OFF relays on boot (Active LOW: write HIGH to turn off)
        digitalWrite(_pins[i], (RELAY_ACTIVE_LEVEL == LOW) ? HIGH : LOW);
        _states[i] = false;
    }
    return true;
}

void RelayController::setRelay(uint8_t index, bool state) {
    if (index >= 4) return;
    _states[index] = state;

    uint8_t writeVal;
    if (RELAY_ACTIVE_LEVEL == LOW) {
        writeVal = state ? LOW : HIGH;
    } else {
        writeVal = state ? HIGH : LOW;
    }
    digitalWrite(_pins[index], writeVal);
}

void RelayController::toggleRelay(uint8_t index) {
    if (index >= 4) return;
    setRelay(index, !_states[index]);
}

bool RelayController::getRelayState(uint8_t index) const {
    if (index >= 4) return false;
    return _states[index];
}

void RelayController::updateTelemetry(SystemTelemetry &telemetry) {
    for (int i = 0; i < 4; i++) {
        telemetry.relayState[i] = _states[i];
    }
}

void RelayController::emergencyAllOff() {
    for (int i = 0; i < 3; i++) {
        setRelay(i, false);
    }
    // Turn ON Emergency Alarm (Relay 4)
    setRelay(3, true);
}

void RelayController::triggerEmergencyAlarm(bool state) {
    setRelay(3, state);
}
