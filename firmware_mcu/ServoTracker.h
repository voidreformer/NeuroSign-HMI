// ==============================================================================
// ServoTracker.h — Dual SG90 Pan/Tilt Camera Servo Controller
// PWM Pins: Pan  -> D9  (TIM1_CH1 / PE9)
//           Tilt -> D10 (TIM1_CH2 / PE11)
// Servo range: SG90 = 500 µs to 2400 µs pulse (0° to 180°)
// Features: Smooth proportional interpolation, angular clamping,
//           speed limiting to prevent camera jolt during tracking.
// ==============================================================================
#pragma once
#include <Arduino.h>
#include <Servo.h>

class ServoTracker {
public:
    /**
     * @param pan_pin  PWM pin for horizontal (yaw) pan servo  (default D9)
     * @param tilt_pin PWM pin for vertical (pitch) tilt servo (default D10)
     */
    ServoTracker(uint8_t pan_pin = 9, uint8_t tilt_pin = 10)
        : _pan_pin(pan_pin), _tilt_pin(tilt_pin) {}

    void begin() {
        _pan_servo.attach(_pan_pin,  500, 2400);
        _tilt_servo.attach(_tilt_pin, 500, 2400);

        _current_pan  = 90;
        _current_tilt = 90;
        _target_pan   = 90;
        _target_tilt  = 90;

        _pan_servo.write(_current_pan);
        _tilt_servo.write(_current_tilt);

        Serial.printf("[SERVO] Pan (D%d) & Tilt (D%d) initialized at 90°.\n",
                      _pan_pin, _tilt_pin);
    }

    /**
     * @brief Sets the commanded absolute target angles.
     *        Motion is smoothed over subsequent update() calls.
     * @param pan_deg  Horizontal angle [0, 180]. 90 = center.
     * @param tilt_deg Vertical angle   [20, 160]. 90 = level.
     */
    void setAbsoluteAngles(int pan_deg, int tilt_deg) {
        _target_pan  = constrain(pan_deg,  0,  180);
        _target_tilt = constrain(tilt_deg, 20, 160);
    }

    /**
     * @brief Increments the current angle by a delta offset.
     *        Useful for proportional error-based camera tracking.
     */
    void nudge(int pan_delta, int tilt_delta) {
        setAbsoluteAngles(
            _target_pan  + pan_delta,
            _target_tilt + tilt_delta
        );
    }

    /**
     * @brief Smooth interpolation step — call every loop iteration.
     *        Applies MAX_STEP_DEG per call to prevent mechanical shock.
     */
    void update() {
        static uint32_t last_update_ms = 0;
        uint32_t now = millis();
        if (now - last_update_ms < SERVO_UPDATE_INTERVAL_MS) return;
        last_update_ms = now;

        bool moved = false;

        // Pan interpolation
        if (abs(_target_pan - _current_pan) > 0) {
            int step = constrain(_target_pan - _current_pan, -MAX_STEP_DEG, MAX_STEP_DEG);
            _current_pan += step;
            _pan_servo.write(_current_pan);
            moved = true;
        }

        // Tilt interpolation
        if (abs(_target_tilt - _current_tilt) > 0) {
            int step = constrain(_target_tilt - _current_tilt, -MAX_STEP_DEG, MAX_STEP_DEG);
            _current_tilt += step;
            _tilt_servo.write(_current_tilt);
            moved = true;
        }

        if (moved) {
            Serial.printf("[SERVO] Pan=%3d° Tilt=%3d°\n", _current_pan, _current_tilt);
        }
    }

    int getCurrentPan()  const { return _current_pan;  }
    int getCurrentTilt() const { return _current_tilt; }

private:
    static constexpr uint8_t  MAX_STEP_DEG            = 3;   // Max degrees per update tick
    static constexpr uint32_t SERVO_UPDATE_INTERVAL_MS = 20;  // 50 Hz servo refresh rate

    uint8_t _pan_pin;
    uint8_t _tilt_pin;
    Servo   _pan_servo;
    Servo   _tilt_servo;
    int     _current_pan  = 90;
    int     _current_tilt = 90;
    int     _target_pan   = 90;
    int     _target_tilt  = 90;
};
