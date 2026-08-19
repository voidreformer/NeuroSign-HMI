#include "oled_display.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1

static Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

OledDisplay::OledDisplay() :
    _animationFrame(0),
    _lastAnimTime(0)
{
}

bool OledDisplay::begin() {
    if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDRESS)) {
        return false;
    }
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    showSplashScreen();
    return true;
}

void OledDisplay::showSplashScreen() {
    display.clearDisplay();

    // Outer border
    display.drawRoundRect(0, 0, 128, 64, 4, SSD1306_WHITE);
    display.drawRoundRect(2, 2, 124, 60, 2, SSD1306_WHITE);

    // Title
    display.setTextSize(2);
    display.setCursor(8, 8);
    display.print(F("NEURO SIGN"));

    // Subtitle & Author
    display.setTextSize(1);
    display.setCursor(12, 28);
    display.print(F("Paralysis Assist"));

    display.setCursor(8, 40);
    display.print(F("Dev: R. A. Pandey"));

    display.setCursor(18, 51);
    display.print(F("433MHz Ready..."));

    display.display();
    delay(1800);
}

void OledDisplay::showCalibrationScreen(uint8_t step) {
    display.clearDisplay();
    display.drawRect(0, 0, 128, 64, SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(16, 8);
    display.print(F("SENSOR CALIBRATION"));
    display.drawLine(10, 20, 118, 20, SSD1306_WHITE);

    display.setCursor(8, 28);
    display.print(F("Hold Hand Flat & Rest"));

    display.setCursor(8, 42);
    display.print(F("Auto-Zeroing ADC: "));
    display.print(step);
    display.print(F("%"));

    display.drawRect(14, 52, 100, 6, SSD1306_WHITE);
    display.fillRect(16, 54, step, 2, SSD1306_WHITE);

    display.display();
}

void OledDisplay::drawBattery(int x, int y, uint8_t percent) {
    // Battery shell
    display.drawRect(x, y, 16, 8, SSD1306_WHITE);
    display.fillRect(x + 16, y + 2, 2, 4, SSD1306_WHITE); // Positive nipple

    // Fill bars based on percentage
    int fillWidth = map(percent, 0, 100, 0, 12);
    if (fillWidth > 0) {
        display.fillRect(x + 2, y + 2, fillWidth, 4, SSD1306_WHITE);
    }
}

void OledDisplay::drawTowerAnimation(int x, int y, uint8_t frame, bool isTransmitting) {
    // 1. Draw Radio Mast / Tower Legs (A-frame structure)
    // Tower base is at y + 14, apex at (x+6, y+4)
    display.drawLine(x + 6, y + 4, x + 1, y + 14, SSD1306_WHITE);
    display.drawLine(x + 6, y + 4, x + 11, y + 14, SSD1306_WHITE);
    // Crossbars
    display.drawLine(x + 3, y + 9, x + 9, y + 9, SSD1306_WHITE);
    display.drawLine(x + 2, y + 12, x + 10, y + 12, SSD1306_WHITE);
    // Center mast & beacon emitter dot
    display.drawLine(x + 6, y + 1, x + 6, y + 5, SSD1306_WHITE);
    display.drawPixel(x + 6, y, SSD1306_WHITE);

    // 2. Animated Expanding Radio Waves (Tower Signal Emission)
    uint8_t waveStage = frame % 4; // 0, 1, 2, 3

    if (waveStage >= 1 || isTransmitting) {
        // Inner arc
        display.drawPixel(x + 3, y + 1, SSD1306_WHITE);
        display.drawPixel(x + 9, y + 1, SSD1306_WHITE);
    }
    if (waveStage >= 2 || isTransmitting) {
        // Mid arc
        display.drawPixel(x + 1, y, SSD1306_WHITE);
        display.drawPixel(x + 11, y, SSD1306_WHITE);
        display.drawPixel(x, y + 1, SSD1306_WHITE);
        display.drawPixel(x + 12, y + 1, SSD1306_WHITE);
    }
    if (waveStage >= 3 || isTransmitting) {
        // Outer pulsing signal bar indicators
        display.drawLine(x + 15, y + 13, x + 15, y + 14, SSD1306_WHITE);
        display.drawLine(x + 17, y + 11, x + 17, y + 14, SSD1306_WHITE);
        display.drawLine(x + 19, y + 8,  x + 19, y + 14, SSD1306_WHITE);
        display.drawLine(x + 21, y + 5,  x + 21, y + 14, SSD1306_WHITE);
    } else {
        display.drawLine(x + 15, y + 13, x + 15, y + 14, SSD1306_WHITE);
        display.drawLine(x + 17, y + 11, x + 17, y + 14, SSD1306_WHITE);
    }

    // Flash TX beacon dot when transmitting
    if (isTransmitting) {
        display.fillRect(x + 5, y - 1, 3, 3, SSD1306_WHITE);
    }
}

void OledDisplay::drawFlexBars(int x, int y, const uint8_t flex[3]) {
    // 3 mini horizontal bar graphs for F1, F2, F3
    const char* labels[3] = {"T", "I", "M"}; // Thumb, Index, Middle
    for (int i = 0; i < 3; i++) {
        int rowY = y + (i * 9);
        display.setCursor(x, rowY);
        display.print(labels[i]);
        display.drawRect(x + 8, rowY, 32, 6, SSD1306_WHITE);
        int fill = map(flex[i], 0, 100, 0, 30);
        if (fill > 0) {
            display.fillRect(x + 9, rowY + 1, fill, 4, SSD1306_WHITE);
        }
    }
}

const char* OledDisplay::getGestureName(uint8_t gestureId) {
    switch (gestureId) {
        case 1:  return "NEED WATER";
        case 2:  return "NEED FOOD";
        case 3:  return "NEED MEDICINE";
        case 4:  return "EMERGENCY!";
        case 11: return "TOGGLE LIGHT 1";
        case 12: return "TOGGLE FAN";
        case 13: return "TOGGLE BED";
        case 21: return "CALL NURSE";
        case 22: return "PAIN ALERT";
        case 23: return "ALL OFF / SLEEP";
        case 99: return "TREMOR / SPASM";
        default: return "NEUTRAL / REST";
    }
}

void OledDisplay::update(const GloveSensorData &sensorData, uint8_t packetSeq, bool txBurst) {
    if (millis() - _lastAnimTime > 150) {
        _lastAnimTime = millis();
        _animationFrame = (_animationFrame + 1) % 4;
    }

    display.clearDisplay();

    // Top Status Header Bar
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(F("NEURO SIGN"));

    // Animated Tower & TX Indicator (Top-Center)
    drawTowerAnimation(66, 0, _animationFrame, txBurst);

    // Battery Icon (Top-Right)
    drawBattery(108, 2, sensorData.batteryPercent);

    display.drawLine(0, 16, 127, 16, SSD1306_WHITE);

    // Left Column: 3 Flex Sensor Meters
    drawFlexBars(0, 19, sensorData.flexPercent);

    // Right Column: Pitch / Roll & Tremor
    display.setCursor(50, 20);
    display.print(F("P:"));
    display.print(sensorData.pitch);
    display.print((char)247); // Degree symbol

    display.setCursor(90, 20);
    display.print(F("R:"));
    display.print(sensorData.roll);
    display.print((char)247);

    display.setCursor(50, 31);
    display.print(F("Tremor:"));
    display.print(sensorData.tremorLevel);
    display.print(F("%"));

    display.setCursor(50, 40);
    display.print(F("PKT:#"));
    display.print(packetSeq);

    // Bottom Action / Gesture Banner (Inverted Highlight Box)
    display.fillRect(0, 50, 128, 14, SSD1306_WHITE);
    display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
    display.setCursor(4, 53);
    display.print(F("ACT: "));
    display.print(getGestureName(sensorData.rawGestureId));
    display.setTextColor(SSD1306_WHITE);

    display.display();
}
