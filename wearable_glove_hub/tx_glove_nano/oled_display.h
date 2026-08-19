#pragma once
#include "config.h"
#include "gesture_sensors.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: OLED Display & Signal Tower Animation (SSD1306 128x64 I2C)
 * ============================================================================
 */

class OledDisplay {
public:
    OledDisplay();
    bool begin();
    void update(const GloveSensorData &sensorData, uint8_t packetSeq, bool txBurst);
    void showSplashScreen();
    void showCalibrationScreen(uint8_t step);

private:
    uint8_t _animationFrame;
    unsigned long _lastAnimTime;

    void drawTowerAnimation(int x, int y, uint8_t frame, bool isTransmitting);
    void drawBattery(int x, int y, uint8_t percent);
    void drawFlexBars(int x, int y, const uint8_t flex[3]);
    const char* getGestureName(uint8_t gestureId);
};
