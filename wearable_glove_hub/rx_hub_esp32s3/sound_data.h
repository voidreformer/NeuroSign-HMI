#pragma once
#include <Arduino.h>

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Audio Waveforms & Alert Sounds for MAX98357A I2S Amplifier
 * ============================================================================
 */

enum SoundAlertId {
    SOUND_NONE = 0,
    SOUND_STARTUP,
    SOUND_CALIBRATED,
    SOUND_WATER_REQUEST,       // "I Need Water"
    SOUND_FOOD_REQUEST,        // "I Need Food"
    SOUND_MEDICINE_REQUEST,    // "I Need Medicine"
    SOUND_EMERGENCY_ALARM,     // "Emergency Alarm"
    SOUND_LIGHT_TOGGLE,        // Light 1 Click Tone
    SOUND_FAN_TOGGLE,          // Fan Hum Tone
    SOUND_BED_ADJUST,          // Bed Motor Chime
    SOUND_CALL_NURSE,          // Nurse Call Chime
    SOUND_PAIN_ALERT,          // Pain Warning Chime
    SOUND_ALL_OFF,             // Power Down Sleep Chime
    SOUND_TREMOR_WARNING       // Tremor / Spasm Warning
};

// Standard sample rate for embedded alert engine
#define AUDIO_SAMPLE_RATE 16000
