#pragma once
#include "config.h"
#include "audio_engine.h"
#include "relay_controller.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Embedded TinyML Gesture Classifier & Spasm Anomaly AI Engine
 * ============================================================================
 */

enum GestureClassId {
    GESTURE_NEUTRAL            = 0,
    // Mode 1: Flat on Bed (Patient Needs)
    GESTURE_FLAT_WATER         = 1,   // Flat + Bend Finger 1: "I Need Water"
    GESTURE_FLAT_FOOD          = 2,   // Flat + Bend Finger 2: "I Need Food"
    GESTURE_FLAT_MEDICINE      = 3,   // Flat + Bend Finger 3: "I Need Medicine"
    GESTURE_FLAT_EMERGENCY     = 4,   // Flat + All 3 Bent: "Emergency Alert"

    // Mode 2: Tilt Left 90° (Home Automation Appliance Control)
    GESTURE_LEFT_LIGHT_TOGGLE  = 11,  // Left + Bend Finger 1: Toggle Light 1
    GESTURE_LEFT_FAN_TOGGLE    = 12,  // Left + Bend Finger 2: Toggle Fan
    GESTURE_LEFT_BED_TOGGLE    = 13,  // Left + Bend Finger 3: Toggle Bed Adjust

    // Mode 3: Tilt Right 90° (Clinical & Caregiver Assistance)
    GESTURE_RIGHT_NURSE_CALL   = 21,  // Right + Bend Finger 1: Call Nurse
    GESTURE_RIGHT_PAIN_ALERT   = 22,  // Right + Bend Finger 2: Pain Alert
    GESTURE_RIGHT_ALL_OFF      = 23,  // Right + Bend Finger 3: Turn All Relays OFF / Sleep

    // Tremor Anomaly
    GESTURE_SPASM_ANOMALY      = 99
};

struct GestureCentroid {
    uint8_t id;
    const char* name;
    float flex1;
    float flex2;
    float flex3;
    float pitch;
    float roll;
    float weight;
};

class NeuroAiEngine {
public:
    NeuroAiEngine();
    bool begin(AudioEngine *audio, RelayController *relays);
    void processSample(const NeuroTxPacket &pkt, SystemTelemetry &telemetry);
    void reset();

private:
    AudioEngine     *_audio;
    RelayController *_relays;

    // Temporal smoothing & debounce state
    uint8_t  _candidateGestureId;
    uint32_t _candidateStartTime;
    uint8_t  _confirmedGestureId;
    uint32_t _lastTriggerTime;
    uint32_t _tremorStartTime;

    uint8_t classifyFeatureVector(float f1, float f2, float f3, float pitch, float roll, float &confidence);
    void executeGestureAction(uint8_t gestureId, SystemTelemetry &telemetry);
    const char* getGestureLabel(uint8_t gestureId);
};
