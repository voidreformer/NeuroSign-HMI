#pragma once
#include <Arduino.h>

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Arduino UNO Q Live Monitor & Plotter Configuration
 * TARGET HARDWARE: Arduino UNO Q / Arduino UNO R4 / Processing Visualizer
 * ============================================================================
 */

#define SYSTEM_NAME         "Neuro Sign Monitor"
#define SYSTEM_AUTHOR       "Rudra Attri Pandey"
#define MONITOR_BAUD_RATE   115200

// Optional Status LED for incoming packet sync
#define PIN_SYNC_LED        13

// Serial Plotter Channel Flags (Enable/Disable streams)
#define PLOT_FLEX_CHANNELS  1
#define PLOT_TILT_CHANNELS  1
#define PLOT_TREMOR_CHANNEL 1
#define PLOT_POWER_CHANNELS 1
