// ==============================================================================
// RadarDriver.h — HLK-LD2410C 24 GHz Human Presence Radar Driver
// Interface: UART2 @ 115200 baud (Arduino UNO Q: D0=RX2/PA3, D1=TX2/PA2)
//            Digital OUT pin on D2 (PB4) for fast interrupt-driven presence flag
// Protocol:  Hi-Link binary frame protocol v2.x (0xFD 0xFC 0xFB 0xFA header)
// ==============================================================================
#pragma once
#include <Arduino.h>

// Radar UART frame constants
static constexpr uint8_t LD2410_FRAME_HEADER[]  = {0xFD, 0xFC, 0xFB, 0xFA};
static constexpr uint8_t LD2410_FRAME_FOOTER[]  = {0x04, 0x03, 0x02, 0x01};
static constexpr uint8_t LD2410_REPORT_DATA_CMD = 0x02;
static constexpr uint8_t RADAR_OUT_PIN          = 2;   // D2 = PB4 (instant presence GPIO)

class RadarDriver {
public:
    explicit RadarDriver(HardwareSerial& serial) : _serial(serial) {}

    void begin(uint32_t baud = 115200) {
        _serial.begin(baud);
        pinMode(RADAR_OUT_PIN, INPUT);
        _buf_idx  = 0;
        _present  = false;
        _dist_cm  = 0;
        _energy   = 0;
        Serial.println("[RADAR] HLK-LD2410C initialized at 115200 baud on UART2.");
    }

    /**
     * @brief Non-blocking UART byte ingestion — call every loop iteration.
     *        Parses complete binary frames when available.
     */
    void update() {
        // Fast-path: read the dedicated GPIO OUT pin first
        _present = (digitalRead(RADAR_OUT_PIN) == HIGH);

        // Slow-path: parse detailed UART binary frame for distance and energy
        while (_serial.available()) {
            uint8_t byte = _serial.read();
            _rx_buf[_buf_idx++] = byte;

            if (_buf_idx > 128) {
                _buf_idx = 0;  // Overflow guard
            }

            if (_tryParseFrame()) {
                _buf_idx = 0;
            }
        }
    }

    /** @return True if human micro-motion or static presence detected. */
    bool     isPresent()    const { return _present;  }

    /** @return Distance to the nearest detected target in centimetres. */
    uint16_t getDistanceCm() const { return _dist_cm;  }

    /** @return Raw energy level (0-100) of the strongest detected gate. */
    uint8_t  getEnergy()    const { return _energy;   }

private:
    HardwareSerial& _serial;
    uint8_t  _rx_buf[128];
    uint8_t  _buf_idx  = 0;
    bool     _present  = false;
    uint16_t _dist_cm  = 0;
    uint8_t  _energy   = 0;

    bool _tryParseFrame() {
        if (_buf_idx < 12) return false;

        // Search for 4-byte header
        int start = -1;
        for (int i = 0; i <= (int)_buf_idx - 4; i++) {
            if (_rx_buf[i]   == LD2410_FRAME_HEADER[0] &&
                _rx_buf[i+1] == LD2410_FRAME_HEADER[1] &&
                _rx_buf[i+2] == LD2410_FRAME_HEADER[2] &&
                _rx_buf[i+3] == LD2410_FRAME_HEADER[3]) {
                start = i;
                break;
            }
        }
        if (start < 0) return false;

        // Minimum viable frame: 4 header + 2 length + data + 4 footer = 12 bytes
        if ((int)_buf_idx < start + 12) return false;

        uint16_t data_len = (uint16_t)_rx_buf[start + 4] | ((uint16_t)_rx_buf[start + 5] << 8);
        uint8_t  cmd      = _rx_buf[start + 6];

        // Validate footer position
        int footer_pos = start + 6 + data_len;
        if ((int)_buf_idx < footer_pos + 4) return false;
        if (_rx_buf[footer_pos]   != LD2410_FRAME_FOOTER[0] ||
            _rx_buf[footer_pos+1] != LD2410_FRAME_FOOTER[1] ||
            _rx_buf[footer_pos+2] != LD2410_FRAME_FOOTER[2] ||
            _rx_buf[footer_pos+3] != LD2410_FRAME_FOOTER[3]) {
            return false;
        }

        if (cmd == LD2410_REPORT_DATA_CMD && data_len >= 9) {
            uint8_t target_status = _rx_buf[start + 7];   // 0=None, 1=Moving, 2=Static, 3=Both
            _present = (target_status != 0);
            _dist_cm = (uint16_t)_rx_buf[start + 8] | ((uint16_t)_rx_buf[start + 9] << 8);
            _energy  = _rx_buf[start + 10];
        }

        return true;
    }
};
