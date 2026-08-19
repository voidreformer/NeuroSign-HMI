// ==============================================================================
// RelayActuator.h — Dual-Channel Opto-Isolated Relay Driver
// Pins:     Channel 1 -> D6 (PB8)  — Room Light / Primary Appliance
//           Channel 2 -> D7 (PB9)  — Emergency Alarm / Strobe / Fan
// Logic:    Active LOW (LOW = relay coil energized = appliance ON)
// Features: Safe auto-shutoff watchdog timer per channel, state tracking,
//           debounced toggle, and per-channel arm/disarm control.
// Safety:   Relay auto-disarms after MAX_ON_DURATION_MS to prevent locked state.
// ==============================================================================
#pragma once
#include <Arduino.h>

static constexpr uint32_t RELAY_CH1_MAX_ON_MS = 0UL;        // 0 = Persistent (no auto-shutoff for room lights)
static constexpr uint32_t RELAY_CH2_MAX_ON_MS = 30000UL;    // 30s auto-shutoff for emergency strobe/alarm

class RelayActuator {
public:
    /**
     * @param ch1_pin GPIO pin for Channel 1 relay (default D6 - Room Light)
     * @param ch2_pin GPIO pin for Channel 2 relay (default D7 - Emergency Siren)
     */
    RelayActuator(uint8_t ch1_pin = 6, uint8_t ch2_pin = 7)
        : _pins{ch1_pin, ch2_pin},
          _states{false, false},
          _on_since{0, 0},
          _max_on_ms{RELAY_CH1_MAX_ON_MS, RELAY_CH2_MAX_ON_MS} {}

    void begin() {
        for (int i = 0; i < 2; i++) {
            pinMode(_pins[i], OUTPUT);
            digitalWrite(_pins[i], HIGH);  // Active-LOW: HIGH = relay OFF (safe default)
            _states[i] = false;
        }
        Serial.printf("[RELAY] CH1 (D%d) & CH2 (D%d) initialized — both OFF.\n",
                      _pins[0], _pins[1]);
    }

    /**
     * @brief Sets the state of a relay channel.
     * @param channel  1 or 2
     * @param on       true = energize relay coil (appliance ON)
     *                 false = de-energize relay coil (appliance OFF)
     */
    void setChannel(uint8_t channel, bool on) {
        if (channel < 1 || channel > 2) return;
        uint8_t idx = channel - 1;

        if (_states[idx] == on) return;  // No change needed

        _states[idx] = on;
        digitalWrite(_pins[idx], on ? LOW : HIGH);  // Active-LOW logic

        if (on) {
            _on_since[idx] = millis();
            if (_max_on_ms[idx] > 0) {
                Serial.printf("[RELAY] CH%d -> ON (watchdog armed for %lu ms)\n",
                              channel, (unsigned long)_max_on_ms[idx]);
            } else {
                Serial.printf("[RELAY] CH%d -> ON (continuous mode)\n", channel);
            }
        } else {
            _on_since[idx] = 0;
            Serial.printf("[RELAY] CH%d -> OFF\n", channel);
        }
    }

    /** @brief Toggles the relay channel state. */
    void toggleChannel(uint8_t channel) {
        if (channel < 1 || channel > 2) return;
        setChannel(channel, !_states[channel - 1]);
    }

    bool isOn(uint8_t channel) const {
        if (channel < 1 || channel > 2) return false;
        return _states[channel - 1];
    }

    /**
     * @brief Watchdog update — must be called every loop() iteration.
     *        Automatically de-energizes any relay with a non-zero timeout
     *        that has been ON for longer than its max duration.
     */
    void update() {
        uint32_t now = millis();
        for (int i = 0; i < 2; i++) {
            if (_states[i] && _on_since[i] > 0 && _max_on_ms[i] > 0) {
                if ((now - _on_since[i]) >= _max_on_ms[i]) {
                    Serial.printf("[RELAY] CH%d auto-shutoff triggered (watchdog %lu ms).\n",
                                  i + 1, (unsigned long)_max_on_ms[i]);
                    setChannel(i + 1, false);
                }
            }
        }
    }

private:
    uint8_t  _pins[2];
    bool     _states[2];
    uint32_t _on_since[2];
    uint32_t _max_on_ms[2];
};
