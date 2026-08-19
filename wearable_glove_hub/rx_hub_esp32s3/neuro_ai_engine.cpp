#include "neuro_ai_engine.h"
#include <math.h>

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Embedded TinyML Gesture Classifier Implementation
 * ============================================================================
 */

// Prototypes / Centroids for 3-Mode Hierarchical Gestures
// Normalization: Flex 0..100 -> 0..1.0, Pitch/Roll -90..+90 -> -1.0..+1.0
static const GestureCentroid GESTURE_PROFILES[] = {
    { GESTURE_NEUTRAL,            "Neutral / Resting",      0.15f, 0.15f, 0.15f,  0.00f,  0.00f, 1.0f },
    // Mode 1: Flat Bed
    { GESTURE_FLAT_WATER,         "Need Water (F1)",        0.80f, 0.15f, 0.15f,  0.00f,  0.00f, 1.8f },
    { GESTURE_FLAT_FOOD,          "Need Food (F2)",         0.15f, 0.80f, 0.15f,  0.00f,  0.00f, 1.8f },
    { GESTURE_FLAT_MEDICINE,      "Need Medicine (F3)",     0.15f, 0.15f, 0.80f,  0.00f,  0.00f, 1.8f },
    { GESTURE_FLAT_EMERGENCY,     "EMERGENCY HELP (F123)",  0.85f, 0.85f, 0.85f,  0.00f,  0.00f, 2.2f },

    // Mode 2: Tilt Left 90°
    { GESTURE_LEFT_LIGHT_TOGGLE,  "Toggle Light 1 (L+F1)",  0.80f, 0.15f, 0.15f,  0.00f, -0.85f, 1.9f },
    { GESTURE_LEFT_FAN_TOGGLE,    "Toggle Fan (L+F2)",      0.15f, 0.80f, 0.15f,  0.00f, -0.85f, 1.9f },
    { GESTURE_LEFT_BED_TOGGLE,    "Toggle Bed (L+F3)",      0.15f, 0.15f, 0.80f,  0.00f, -0.85f, 1.9f },

    // Mode 3: Tilt Right 90°
    { GESTURE_RIGHT_NURSE_CALL,   "Call Nurse (R+F1)",      0.80f, 0.15f, 0.15f,  0.00f,  0.85f, 1.9f },
    { GESTURE_RIGHT_PAIN_ALERT,   "Pain Alert (R+F2)",      0.15f, 0.80f, 0.15f,  0.00f,  0.85f, 1.9f },
    { GESTURE_RIGHT_ALL_OFF,      "All Off / Sleep (R+F3)", 0.15f, 0.15f, 0.80f,  0.00f,  0.85f, 1.9f }
};

#define NUM_GESTURE_PROFILES (sizeof(GESTURE_PROFILES) / sizeof(GestureCentroid))
#define GESTURE_HOLD_DURATION_MS 350  // Must hold gesture for 350ms to confirm
#define ACTION_COOLDOWN_MS       1200 // Prevent rapid accidental repeats

NeuroAiEngine::NeuroAiEngine() :
    _audio(nullptr),
    _relays(nullptr),
    _candidateGestureId(0),
    _candidateStartTime(0),
    _confirmedGestureId(0),
    _lastTriggerTime(0),
    _tremorStartTime(0)
{
}

bool NeuroAiEngine::begin(AudioEngine *audio, RelayController *relays) {
    _audio = audio;
    _relays = relays;
    reset();
    return true;
}

void NeuroAiEngine::reset() {
    _candidateGestureId = 0;
    _candidateStartTime = 0;
    _confirmedGestureId = 0;
    _lastTriggerTime = 0;
    _tremorStartTime = 0;
}

const char* NeuroAiEngine::getGestureLabel(uint8_t gestureId) {
    for (size_t i = 0; i < NUM_GESTURE_PROFILES; i++) {
        if (GESTURE_PROFILES[i].id == gestureId) {
            return GESTURE_PROFILES[i].name;
        }
    }
    if (gestureId == GESTURE_SPASM_ANOMALY) return "SPASM / TREMOR DETECTED";
    return "Unknown";
}

uint8_t NeuroAiEngine::classifyFeatureVector(float f1, float f2, float f3, float pitch, float roll, float &confidence) {
    // Feature normalization
    float nf1 = constrain(f1 / 100.0f, 0.0f, 1.0f);
    float nf2 = constrain(f2 / 100.0f, 0.0f, 1.0f);
    float nf3 = constrain(f3 / 100.0f, 0.0f, 1.0f);
    float np  = constrain(pitch / 90.0f, -1.0f, 1.0f);
    float nr  = constrain(roll  / 90.0f, -1.0f, 1.0f);

    float minDistance = 999.0f;
    uint8_t bestClass = GESTURE_NEUTRAL;

    for (size_t i = 0; i < NUM_GESTURE_PROFILES; i++) {
        const GestureCentroid &c = GESTURE_PROFILES[i];

        float d_f1 = (nf1 - c.flex1) * 1.3f;
        float d_f2 = (nf2 - c.flex2) * 1.3f;
        float d_f3 = (nf3 - c.flex3) * 1.3f;
        float d_p  = (np  - c.pitch) * 1.0f;
        float d_r  = (nr  - c.roll)  * 1.8f; // Stronger roll weight for mode separation

        float dist = sqrtf(d_f1*d_f1 + d_f2*d_f2 + d_f3*d_f3 + d_p*d_p + d_r*d_r);

        if (dist < minDistance) {
            minDistance = dist;
            bestClass = c.id;
        }
    }

    // Convert distance to probability score (0.0 to 1.0)
    confidence = constrain(1.0f - (minDistance / 2.0f), 0.0f, 1.0f);
    return bestClass;
}

void NeuroAiEngine::executeGestureAction(uint8_t gestureId, SystemTelemetry &telemetry) {
    uint32_t now = millis();
    snprintf(telemetry.lastAlertMessage, sizeof(telemetry.lastAlertMessage), "%s", getGestureLabel(gestureId));
    telemetry.lastAlertTimestamp = now;

    switch (gestureId) {
        // --- MODE 1: FLAT BED (PATIENT REQUESTS) ---
        case GESTURE_FLAT_WATER:
            if (_audio) _audio->playAlert(SOUND_WATER_REQUEST);
            break;

        case GESTURE_FLAT_FOOD:
            if (_audio) _audio->playAlert(SOUND_FOOD_REQUEST);
            break;

        case GESTURE_FLAT_MEDICINE:
            if (_audio) _audio->playAlert(SOUND_MEDICINE_REQUEST);
            break;

        case GESTURE_FLAT_EMERGENCY:
            if (_relays) _relays->triggerEmergencyAlarm(true);
            if (_audio)  _audio->playAlert(SOUND_EMERGENCY_ALARM);
            telemetry.spasmAlertActive = true;
            break;

        // --- MODE 2: TILT LEFT 90° (APPLIANCE CONTROL) ---
        case GESTURE_LEFT_LIGHT_TOGGLE:
            if (_relays) _relays->toggleRelay(0); // Relay 1 (Light 1)
            if (_audio)  _audio->playAlert(SOUND_LIGHT_TOGGLE);
            break;

        case GESTURE_LEFT_FAN_TOGGLE:
            if (_relays) _relays->toggleRelay(1); // Relay 2 (Fan)
            if (_audio)  _audio->playAlert(SOUND_FAN_TOGGLE);
            break;

        case GESTURE_LEFT_BED_TOGGLE:
            if (_relays) _relays->toggleRelay(2); // Relay 3 (Bed Position)
            if (_audio)  _audio->playAlert(SOUND_BED_ADJUST);
            break;

        // --- MODE 3: TILT RIGHT 90° (CAREGIVER CONTROLS) ---
        case GESTURE_RIGHT_NURSE_CALL:
            if (_audio) _audio->playAlert(SOUND_CALL_NURSE);
            break;

        case GESTURE_RIGHT_PAIN_ALERT:
            if (_audio) _audio->playAlert(SOUND_PAIN_ALERT);
            break;

        case GESTURE_RIGHT_ALL_OFF:
            if (_relays) {
                _relays->setRelay(0, false);
                _relays->setRelay(1, false);
                _relays->setRelay(2, false);
            }
            if (_audio) _audio->playAlert(SOUND_ALL_OFF);
            break;

        // --- ANOMALY: TREMOR / SPASM ---
        case GESTURE_SPASM_ANOMALY:
            if (_relays) _relays->triggerEmergencyAlarm(true);
            if (_audio)  _audio->playAlert(SOUND_TREMOR_WARNING);
            telemetry.spasmAlertActive = true;
            break;

        default:
            break;
    }
}

void NeuroAiEngine::processSample(const NeuroTxPacket &pkt, SystemTelemetry &telemetry) {
    uint32_t now = millis();

    // 1. Spasm & High Tremor Anomaly Detection
    if (pkt.tremorLevel > 70) {
        if (_tremorStartTime == 0) {
            _tremorStartTime = now;
        } else if (now - _tremorStartTime > 800) { // Sustained spasm > 800ms
            if (now - _lastTriggerTime > ACTION_COOLDOWN_MS) {
                _lastTriggerTime = now;
                telemetry.gestureId = GESTURE_SPASM_ANOMALY;
                telemetry.gestureConfidence = 0.98f;
                strncpy(telemetry.gestureName, getGestureLabel(GESTURE_SPASM_ANOMALY), sizeof(telemetry.gestureName));
                executeGestureAction(GESTURE_SPASM_ANOMALY, telemetry);
            }
            return;
        }
    } else {
        _tremorStartTime = 0;
    }

    // 2. Classify gesture using TinyML Feature Vector
    float confidence = 0.0f;
    uint8_t classifiedId = classifyFeatureVector(
        (float)pkt.flex1,
        (float)pkt.flex2,
        (float)pkt.flex3,
        (float)pkt.pitch,
        (float)pkt.roll,
        confidence
    );

    // 3. Temporal Stability Window & Hysteresis
    if (classifiedId != _candidateGestureId) {
        _candidateGestureId = classifiedId;
        _candidateStartTime = now;
    } else {
        // Sustained candidate
        if (now - _candidateStartTime >= GESTURE_HOLD_DURATION_MS) {
            if (_confirmedGestureId != _candidateGestureId) {
                _confirmedGestureId = _candidateGestureId;

                // Update Telemetry Display
                telemetry.gestureId = _confirmedGestureId;
                telemetry.gestureConfidence = confidence;
                strncpy(telemetry.gestureName, getGestureLabel(_confirmedGestureId), sizeof(telemetry.gestureName));

                // If non-neutral and cooldown expired, fire action
                if (_confirmedGestureId != GESTURE_NEUTRAL && (now - _lastTriggerTime > ACTION_COOLDOWN_MS)) {
                    _lastTriggerTime = now;
                    executeGestureAction(_confirmedGestureId, telemetry);
                }
            }
        }
    }
}
