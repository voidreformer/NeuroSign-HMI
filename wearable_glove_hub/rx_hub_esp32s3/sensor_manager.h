#pragma once
#include "config.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Multi-Sensor Diagnostics Manager (DHT11, BMP280, SGP40, INA219)
 * ============================================================================
 */

class SensorManager {
public:
    SensorManager();
    bool begin();
    void update(SystemTelemetry &telemetry);

private:
    bool _bmp280Detected;
    bool _sgp40Detected;
    bool _ina219Detected;
    bool _dht11Detected;

    uint32_t _lastPollTime;
    float    _seaLevelPressureHpa;

    // SGP40 VOC Index Algorithm internal state
    int32_t  _sgp40VocBaseline;
    float    _sgp40VocFilter;

    bool initBMP280();
    bool initSGP40();
    bool initINA219();
    bool initDHT11();

    void readDHT11(float &tempC, float &humidity);
    void readBMP280(float &tempC, float &pressureHpa, float &altitudeM);
    void readSGP40(float tempC, float humidity, int32_t &vocIndex);
    void readINA219(float &busVoltageV, float &currentMA, float &powerMW);
};
