#include "gesture_sensors.h"
#include <Wire.h>
#include <math.h>

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Glove Sensor Interface Implementation
 * ============================================================================
 */

GestureSensors::GestureSensors() :
    _flexHistIndex(0),
    _accelX(0), _accelY(0), _accelZ(0),
    _prevAccelX(0), _prevAccelY(0), _prevAccelZ(0),
    _jerkAccumulator(0)
{
    // Default fallback calibration values for flex sensors (0-1023 ADC)
    _flexMin[0] = 300; _flexMax[0] = 750;
    _flexMin[1] = 300; _flexMax[1] = 750;
    _flexMin[2] = 300; _flexMax[2] = 750;

    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < SENSOR_SAMPLE_WINDOW; j++) {
            _flexHistory[i][j] = 500;
        }
    }
}

bool GestureSensors::begin() {
    pinMode(PIN_FLEX_1, INPUT);
    pinMode(PIN_FLEX_2, INPUT);
    pinMode(PIN_FLEX_3, INPUT);
    pinMode(PIN_BATTERY_MONITOR, INPUT);

    Wire.begin();
    Wire.setClock(400000); // 400kHz Fast Mode I2C

    bool adxlOk = initADXL345();
    recalibrateFlex();
    return adxlOk;
}

bool GestureSensors::initADXL345() {
    Wire.beginTransmission(ADXL345_I2C_ADDRESS);
    Wire.write(ADXL_REG_DEVID);
    if (Wire.endTransmission() != 0) return false;

    Wire.requestFrom(ADXL345_I2C_ADDRESS, 1);
    if (Wire.available()) {
        uint8_t devId = Wire.read();
        if (devId != 0xE5) {
            // Unexpected Device ID but will attempt initialization
        }
    }

    // Set Measurement mode (D3 = 1 in POWER_CTL register 0x2D)
    Wire.beginTransmission(ADXL345_I2C_ADDRESS);
    Wire.write(ADXL_REG_POWER_CTL);
    Wire.write(0x08);
    Wire.endTransmission();

    // Set Data Format (+/- 4g range, full resolution)
    Wire.beginTransmission(ADXL345_I2C_ADDRESS);
    Wire.write(ADXL_REG_DATA_FORMAT);
    Wire.write(0x01); // +/- 4g
    Wire.endTransmission();

    return true;
}

void GestureSensors::readADXL345(float &ax, float &ay, float &az) {
    Wire.beginTransmission(ADXL345_I2C_ADDRESS);
    Wire.write(ADXL_REG_DATAX0);
    Wire.endTransmission(false);

    Wire.requestFrom((uint8_t)ADXL345_I2C_ADDRESS, (uint8_t)6);
    if (Wire.available() >= 6) {
        int16_t rawX = Wire.read() | (Wire.read() << 8);
        int16_t rawY = Wire.read() | (Wire.read() << 8);
        int16_t rawZ = Wire.read() | (Wire.read() << 8);

        // Convert to Gs (Scale factor ~ 0.0078 g/LSB in 4g mode)
        ax = (float)rawX * 0.0078125f;
        ay = (float)rawY * 0.0078125f;
        az = (float)rawZ * 0.0078125f;
    }
}

void GestureSensors::recalibrateFlex() {
    // Quick baseline recording for flat hand (resting position)
    long sum[3] = {0, 0, 0};
    for (int s = 0; s < CALIBRATION_SAMPLES; s++) {
        sum[0] += analogRead(PIN_FLEX_1);
        sum[1] += analogRead(PIN_FLEX_2);
        sum[2] += analogRead(PIN_FLEX_3);
        delay(3);
    }
    for (int i = 0; i < 3; i++) {
        _flexMin[i] = sum[i] / CALIBRATION_SAMPLES;
        _flexMax[i] = _flexMin[i] + 350; // Expected dynamic range with standard 10k divider
    }
}

uint8_t GestureSensors::readBattery() {
    // Voltage divider calculation assuming 10k/10k divider to A3 from 1S LiPo (3.3V-4.2V)
    int raw = analogRead(PIN_BATTERY_MONITOR);
    float vSense = (raw * 5.0f) / 1023.0f;
    float vBat = vSense * 2.0f; // Scale divider (2x)

    if (vBat >= 4.2f) return 100;
    if (vBat <= 3.2f) return 0;
    return (uint8_t)(((vBat - 3.2f) / (4.2f - 3.2f)) * 100.0f);
}

void GestureSensors::update() {
    // 1. Read and filter flex sensors
    int rawFlex[3] = {
        analogRead(PIN_FLEX_1),
        analogRead(PIN_FLEX_2),
        analogRead(PIN_FLEX_3)
    };

    for (int i = 0; i < 3; i++) {
        _flexHistory[i][_flexHistIndex] = rawFlex[i];

        // Running average
        long avg = 0;
        for (int j = 0; j < SENSOR_SAMPLE_WINDOW; j++) {
            avg += _flexHistory[i][j];
        }
        avg /= SENSOR_SAMPLE_WINDOW;

        // Auto-adapt bounds dynamically if patient stretches further
        if (avg < _flexMin[i]) _flexMin[i] = avg;
        if (avg > _flexMax[i]) _flexMax[i] = avg;

        // Map to 0 - 100%
        int percent = map(avg, _flexMin[i], _flexMax[i], 0, 100);
        _data.flexPercent[i] = (uint8_t)constrain(percent, 0, 100);
    }

    _flexHistIndex = (_flexHistIndex + 1) % SENSOR_SAMPLE_WINDOW;

    // 2. Read ADXL345 Accelerometer & calculate Pitch / Roll / Tremor
    readADXL345(_accelX, _accelY, _accelZ);

    // Calculate Pitch and Roll in degrees
    // Pitch: Rotation around Y-axis
    // Roll: Rotation around X-axis
    float pitchRad = atan2(-_accelX, sqrt(_accelY * _accelY + _accelZ * _accelZ));
    float rollRad  = atan2(_accelY, _accelZ);

    int pitchDeg = (int)(pitchRad * 180.0f / 3.14159265f);
    int rollDeg  = (int)(rollRad * 180.0f / 3.14159265f);

    _data.pitch = (int8_t)constrain(pitchDeg, -90, 90);
    _data.roll  = (int8_t)constrain(rollDeg, -90, 90);

    // 3. Tremor / Jerk Detection (High frequency variance)
    float deltaX = _accelX - _prevAccelX;
    float deltaY = _accelY - _prevAccelY;
    float deltaZ = _accelZ - _prevAccelZ;
    float jerkMagnitude = sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ) * 100.0f;

    _prevAccelX = _accelX;
    _prevAccelY = _accelY;
    _prevAccelZ = _accelZ;

    // Exponential smoothing of tremor level
    _jerkAccumulator = (_jerkAccumulator * 0.7f) + (jerkMagnitude * 0.3f);
    _data.tremorLevel = (uint8_t)constrain((int)_jerkAccumulator, 0, 100);

    // 4. Battery and local quick gesture recognition
    _data.batteryPercent = readBattery();
    _data.rawGestureId = evaluateLocalGesture();
}

uint8_t GestureSensors::evaluateLocalGesture() {
    uint8_t f1 = _data.flexPercent[0];
    uint8_t f2 = _data.flexPercent[1];
    uint8_t f3 = _data.flexPercent[2];
    int8_t roll  = _data.roll;

    // 0. Spasm / Tremor Override
    if (_data.tremorLevel > 65) {
        return 99; // Spasm / Emergency Tremor
    }

    // Emergency Fist (All 3 fingers bent > 65% in any position)
    if (f1 > 65 && f2 > 65 && f3 > 65) {
        return 4; // Emergency Help
    }

    // Individual Finger Bend Flags (Active > 48%, Inactive < 38%)
    bool b1 = (f1 > 48);
    bool b2 = (f2 > 48);
    bool b3 = (f3 > 48);

    // MODE 2: TILT LEFT 90° (Roll < -40°) -> Appliance Control
    if (roll < -40) {
        if (b1 && !b2 && !b3) return 11; // Left + Finger 1: Toggle Light 1
        if (b2 && !b1 && !b3) return 12; // Left + Finger 2: Toggle Fan
        if (b3 && !b1 && !b2) return 13; // Left + Finger 3: Toggle Bed Position
        return 0;
    }

    // MODE 3: TILT RIGHT 90° (Roll > +40°) -> Clinical & Caregiver Controls
    if (roll > 40) {
        if (b1 && !b2 && !b3) return 21; // Right + Finger 1: Call Nurse
        if (b2 && !b1 && !b3) return 22; // Right + Finger 2: Pain Alert
        if (b3 && !b1 && !b2) return 23; // Right + Finger 3: All Appliances OFF / Sleep
        return 0;
    }

    // MODE 1: FLAT / PARALLEL ON BED (-40° <= Roll <= +40°) -> Patient Requests
    if (b1 && !b2 && !b3) return 1; // Flat + Finger 1: "I Need Water"
    if (b2 && !b1 && !b3) return 2; // Flat + Finger 2: "I Need Food"
    if (b3 && !b1 && !b2) return 3; // Flat + Finger 3: "I Need Medicine"

    return 0; // Neutral / Resting
}
