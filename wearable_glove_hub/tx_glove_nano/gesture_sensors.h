#pragma once
#include "config.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Glove Sensor Interface (3x Flex + ADXL345 3-Axis Accelerometer)
 * ============================================================================
 */

struct GloveSensorData {
    uint8_t flexPercent[3];  // 0 - 100% bend for each finger
    int8_t  pitch;           // -90 to +90 degrees tilt
    int8_t  roll;            // -90 to +90 degrees roll
    uint8_t tremorLevel;     // Dynamic high-frequency jitter (0-100)
    uint8_t batteryPercent;  // Estimated battery charge
    uint8_t rawGestureId;    // Fast local rule classification
};

class GestureSensors {
public:
    GestureSensors();
    bool begin();
    void update();
    const GloveSensorData& getData() const { return _data; }
    void recalibrateFlex();

private:
    GloveSensorData _data;

    // Flex sensor calibration minimum and maximum ADC values
    int _flexMin[3];
    int _flexMax[3];

    // Moving average filter history
    int _flexHistory[3][SENSOR_SAMPLE_WINDOW];
    uint8_t _flexHistIndex;

    // Accelerometer smoothing & tremor calculation
    float _accelX, _accelY, _accelZ;
    float _prevAccelX, _prevAccelY, _prevAccelZ;
    float _jerkAccumulator;

    bool initADXL345();
    void readADXL345(float &ax, float &ay, float &az);
    uint8_t readBattery();
    uint8_t evaluateLocalGesture();
};
