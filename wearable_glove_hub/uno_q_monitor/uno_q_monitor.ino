/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Arduino UNO Q Live Monitor & Multi-Channel Serial Waveform Plotter
 * TARGET HARDWARE: Arduino UNO Q (4GB) / Arduino UNO R4 / Standalone Plotter
 * 
 * DESCRIPTION:
 * Receives the continuous high-speed JSON telemetry stream from the ESP32-S3
 * Hub over UART at 115200 baud, decodes the biomedical flex sensors, 3-axis
 * orientation, tremor frequency, and power diagnostics, and outputs real-time
 * multi-channel waveform plots for external display screens & serial plotters.
 * ============================================================================
 */

#include "config.h"

String inputBuffer = "";
bool stringComplete = false;

void setup() {
    // Initialize Primary Hardware Serial for Monitor & Plotter
    Serial.begin(MONITOR_BAUD_RATE);
    inputBuffer.reserve(350);

    pinMode(PIN_SYNC_LED, OUTPUT);
    digitalWrite(PIN_SYNC_LED, LOW);

    // Initial Telemetry Header for Plotter
    Serial.println(F("\n========================================================"));
    Serial.println(F("       NEURO SIGN - ARDUINO UNO Q LIVE PLOTTER         "));
    Serial.println(F("          Developed by: Rudra Attri Pandey              "));
    Serial.println(F("========================================================\n"));
    Serial.println(F("F1_Thumb F2_Index F3_Middle Pitch Roll Tremor VOC Current_mA Power_mW"));
}

void loop() {
    while (Serial.available()) {
        char inChar = (char)Serial.read();
        if (inChar == '\n') {
            stringComplete = true;
            break;
        } else if (inChar != '\r') {
            inputBuffer += inChar;
        }
    }

    if (stringComplete) {
        digitalWrite(PIN_SYNC_LED, HIGH);
        parseAndPlotTelemetry(inputBuffer);
        inputBuffer = "";
        stringComplete = false;
        digitalWrite(PIN_SYNC_LED, LOW);
    }
}

// Simple fast parser for incoming JSON key-values
int extractInt(const String &str, const char* key) {
    int pos = str.indexOf(key);
    if (pos == -1) return 0;
    int colon = str.indexOf(':', pos);
    if (colon == -1) return 0;
    int comma = str.indexOf(',', colon);
    int brace = str.indexOf('}', colon);
    int end = (comma != -1 && (brace == -1 || comma < brace)) ? comma : brace;
    if (end == -1) end = str.length();
    return str.substring(colon + 1, end).toInt();
}

float extractFloat(const String &str, const char* key) {
    int pos = str.indexOf(key);
    if (pos == -1) return 0.0f;
    int colon = str.indexOf(':', pos);
    if (colon == -1) return 0.0f;
    int comma = str.indexOf(',', colon);
    int brace = str.indexOf('}', colon);
    int end = (comma != -1 && (brace == -1 || comma < brace)) ? comma : brace;
    if (end == -1) end = str.length();
    return str.substring(colon + 1, end).toFloat();
}

void parseAndPlotTelemetry(const String &json) {
    if (!json.startsWith("{") || !json.endsWith("}")) return;

    int f1     = extractInt(json, "\"f1\"");
    int f2     = extractInt(json, "\"f2\"");
    int f3     = extractInt(json, "\"f3\"");
    int pitch  = extractInt(json, "\"p\"");
    int roll   = extractInt(json, "\"r\"");
    int tremor = extractInt(json, "\"trm\"");
    int voc    = extractInt(json, "\"voc\"");
    float ma   = extractFloat(json, "\"ma\"");
    float mw   = extractFloat(json, "\"mw\"");

    // Output formatted multi-variable telemetry for Arduino IDE Serial Plotter
    // Format: "Key:Value Key:Value ..."
    Serial.print(F("F1_Thumb:"));
    Serial.print(f1);
    Serial.print(F(" F2_Index:"));
    Serial.print(f2);
    Serial.print(F(" F3_Middle:"));
    Serial.print(f3);
    Serial.print(F(" Pitch:"));
    Serial.print(pitch);
    Serial.print(F(" Roll:"));
    Serial.print(roll);
    Serial.print(F(" Tremor:"));
    Serial.print(tremor);
    Serial.print(F(" VOC_AQI:"));
    Serial.print(voc);
    Serial.print(F(" Current_mA:"));
    Serial.print(ma);
    Serial.print(F(" Power_mW:"));
    Serial.println(mw);
}
