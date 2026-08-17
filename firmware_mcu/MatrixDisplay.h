// ==============================================================================
// MatrixDisplay.h — Arduino UNO Q 8x13 Blue LED Matrix Glyph Engine
// Library: Arduino_LED_Matrix (built-in for UNO R4 / UNO Q compatibility)
// Features: Pre-rendered bitmapped glyph table, animated sequences (IDLE pulse,
//           SOS flash), single-frame instant rendering, and non-blocking
//           animation playback using millis() timers.
// ==============================================================================
#pragma once
#include <Arduino.h>
#include <Arduino_LED_Matrix.h>

enum GlyphType : uint8_t {
    GLYPH_IDLE         = 0,  // Gentle center pulse (breathing animation)
    GLYPH_GESTURE_OK   = 1,  // Checkmark  ✓
    GLYPH_EMERGENCY    = 2,  // SOS flash  S-O-S
    GLYPH_SPEAKING     = 3,  // Audio waves ))
    GLYPH_LISTENING    = 4,  // Microphone symbol
    GLYPH_RELAY_ON     = 5,  // Filled block (ON state)
    GLYPH_WARNING      = 6,  // Exclamation  !
};

// 8x12 bitmapped glyphs stored as 96-bit uint8_t[12] row arrays
// Each uint8_t represents one 8-pixel row (bit 7 = leftmost LED)

static const uint8_t GLYPH_CHECKMARK[8] = {
    0b00000001,
    0b00000010,
    0b00000100,
    0b00001000,
    0b10010000,
    0b01100000,
    0b00100000,
    0b00000000,
};

static const uint8_t GLYPH_EXCLAMATION[8] = {
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00000000,
    0b00010000,
    0b00000000,
};

static const uint8_t GLYPH_MIC[8] = {
    0b00010000,
    0b00101000,
    0b00101000,
    0b00010000,
    0b01111100,
    0b00010000,
    0b00111000,
    0b00000000,
};

static const uint8_t GLYPH_WAVES[8] = {
    0b00000000,
    0b01000010,
    0b00100100,
    0b00011000,
    0b00100100,
    0b01000010,
    0b00000000,
    0b00000000,
};

static const uint8_t GLYPH_FULL[8] = {
    0b11111111,
    0b11111111,
    0b11111111,
    0b11111111,
    0b11111111,
    0b11111111,
    0b11111111,
    0b11111111,
};

static const uint8_t GLYPH_CENTER[8] = {
    0b00000000,
    0b00000000,
    0b00111100,
    0b00111100,
    0b00111100,
    0b00111100,
    0b00000000,
    0b00000000,
};

static const uint8_t GLYPH_CLEAR[8] = {
    0, 0, 0, 0, 0, 0, 0, 0
};

class MatrixDisplay {
public:
    MatrixDisplay() = default;

    void begin() {
        _matrix.begin();
        showGlyph(GLYPH_IDLE);
        Serial.println("[MATRIX] 8x13 LED Matrix initialized.");
    }

    void showGlyph(GlyphType type) {
        _current_glyph = type;
        _anim_frame    = 0;
        _anim_start_ms = millis();

        if (type == GLYPH_IDLE || type == GLYPH_EMERGENCY) {
            _animating = true;
        } else {
            _animating = false;
            _renderStatic(type);
        }
    }

    /** @brief Must be called every loop() for animated glyphs. */
    void update() {
        if (!_animating) return;

        uint32_t elapsed = millis() - _anim_start_ms;

        if (_current_glyph == GLYPH_IDLE) {
            // Breathing: alternate center and clear every 600ms
            bool show_center = ((elapsed / 600) % 2 == 0);
            _renderRaw(show_center ? GLYPH_CENTER : GLYPH_CLEAR);

        } else if (_current_glyph == GLYPH_EMERGENCY) {
            // SOS flash: 150ms ON / 150ms OFF rapid strobe
            bool flash_on = ((elapsed / 150) % 2 == 0);
            _renderRaw(flash_on ? GLYPH_FULL : GLYPH_CLEAR);
        }
    }

private:
    ArduinoLEDMatrix _matrix;
    GlyphType        _current_glyph = GLYPH_IDLE;
    bool             _animating     = true;
    uint8_t          _anim_frame    = 0;
    uint32_t         _anim_start_ms = 0;

    void _renderStatic(GlyphType type) {
        switch (type) {
            case GLYPH_GESTURE_OK: _renderRaw(GLYPH_CHECKMARK);   break;
            case GLYPH_SPEAKING:   _renderRaw(GLYPH_WAVES);       break;
            case GLYPH_LISTENING:  _renderRaw(GLYPH_MIC);         break;
            case GLYPH_RELAY_ON:   _renderRaw(GLYPH_FULL);        break;
            case GLYPH_WARNING:    _renderRaw(GLYPH_EXCLAMATION); break;
            default:               _renderRaw(GLYPH_CLEAR);       break;
        }
    }

    void _renderRaw(const uint8_t glyph[8]) {
        // Arduino_LED_Matrix expects a uint32_t[3] frame (96-bit total)
        uint32_t frame[3] = {0, 0, 0};
        for (int row = 0; row < 8; row++) {
            uint8_t bits = glyph[row];
            for (int col = 0; col < 8; col++) {
                if (bits & (1 << (7 - col))) {
                    int bit_pos = row * 12 + col;
                    frame[bit_pos / 32] |= (1UL << (31 - (bit_pos % 32)));
                }
            }
        }
        _matrix.loadFrame(frame);
    }
};
