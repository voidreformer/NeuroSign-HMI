// ==============================================================================
// SensorBus.h — Unified I2C Sensor Aggregator
// Sensors:  SGP40 (Air Quality VOC), INA219 (Current/Voltage/Power),
//           MPU-6050 (6-Axis Gyro+Accel), DHT22 (Temperature & Humidity)
// Buses:    SGP40, INA219, MPU-6050 -> Qwiic I2C1 (3.3V)
//           DHT22                   -> Digital pin D4 (PB6) single-bus
// ==============================================================================
#pragma once
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_SGP40.h>
#include <Adafruit_INA219.h>
#include <Adafruit_MPU6050.h>
#include <DHT.h>

static constexpr uint8_t DHT22_DATA_PIN = 4;   // D4 = PB6

struct SensorData {
    int     voc_index   = 100;   // SGP40 VOC Index (1=clean, 500=very polluted)
    float   bus_volts   = 0.0f;  // INA219 bus voltage (V)
    float   current_ma  = 0.0f;  // INA219 shunt current (mA)
    float   power_mw    = 0.0f;  // INA219 calculated power (mW)
    float   temp_c      = 25.0f; // DHT22 temperature (°C)
    float   humidity    = 50.0f; // DHT22 relative humidity (%)
    float   accel_x     = 0.0f;  // MPU-6050 X-axis acceleration (m/s²)
    float   accel_y     = 0.0f;  // MPU-6050 Y-axis acceleration (m/s²)
    float   accel_z     = 9.81f; // MPU-6050 Z-axis acceleration (m/s²)
    bool    motion      = false; // MPU-6050 motion detected flag
};

class SensorBus {
public:
    SensorBus() : _dht(DHT22_DATA_PIN, DHT22) {}

    bool begin() {
        Wire.begin();

        bool ok = true;

        if (!_sgp40.begin()) {
            Serial.println("[SENSOR] WARNING: SGP40 not found on I2C.");
            ok = false;
        } else {
            Serial.println("[SENSOR] SGP40 air quality sensor OK.");
        }

        if (!_ina219.begin()) {
            Serial.println("[SENSOR] WARNING: INA219 not found on I2C.");
            ok = false;
        } else {
            Serial.println("[SENSOR] INA219 power monitor OK.");
        }

        if (!_mpu6050.begin()) {
            Serial.println("[SENSOR] WARNING: MPU-6050 not found on I2C.");
            ok = false;
        } else {
            _mpu6050.setAccelerometerRange(MPU6050_RANGE_4_G);
            _mpu6050.setGyroRange(MPU6050_RANGE_250_DEG);
            Serial.println("[SENSOR] MPU-6050 IMU OK.");
        }

        _dht.begin();
        Serial.println("[SENSOR] DHT22 temperature/humidity sensor OK.");
        Serial.printf("[SENSOR] SensorBus init complete (all_ok=%s).\n", ok ? "YES" : "PARTIAL");
        return ok;
    }

    /**
     * @brief Reads all sensors and returns a populated SensorData struct.
     *        Safe to call every 2000ms to respect DHT22 minimum sampling interval.
     */
    SensorData read() {
        SensorData data;

        // 1. SGP40 — VOC Index (requires humidity/temp compensation)
        data.temp_c     = _dht.readTemperature();
        data.humidity   = _dht.readHumidity();
        if (!isnan(data.temp_c) && !isnan(data.humidity)) {
            data.voc_index = _sgp40.measureVocIndex(data.humidity, data.temp_c);
        } else {
            data.temp_c   = _last.temp_c;
            data.humidity = _last.humidity;
            data.voc_index = _sgp40.measureVocIndex();
        }

        // 2. INA219 — Power monitoring
        data.bus_volts  = _ina219.getBusVoltage_V();
        data.current_ma = _ina219.getCurrent_mA();
        data.power_mw   = _ina219.getPower_mW();

        // 3. MPU-6050 — Acceleration & motion
        sensors_event_t accel_ev, gyro_ev, temp_ev;
        _mpu6050.getEvent(&accel_ev, &gyro_ev, &temp_ev);
        data.accel_x = accel_ev.acceleration.x;
        data.accel_y = accel_ev.acceleration.y;
        data.accel_z = accel_ev.acceleration.z;

        // Detect significant motion (vector magnitude deviation from rest)
        float mag = sqrt(data.accel_x * data.accel_x +
                         data.accel_y * data.accel_y +
                         (data.accel_z - 9.81f) * (data.accel_z - 9.81f));
        data.motion = (mag > 1.5f);

        _last = data;
        return data;
    }

private:
    Adafruit_SGP40    _sgp40;
    Adafruit_INA219   _ina219;
    Adafruit_MPU6050  _mpu6050;
    DHT               _dht;
    SensorData        _last;
};
