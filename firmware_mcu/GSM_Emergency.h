// ==============================================================================
// GSM_Emergency.h — SIM800C GSM/GPRS Offline Emergency SMS Driver
// Interface: UART3 @ 9600 baud (D8=TX3/PD8, D11=RX3/PD9)
// Power:     3.7V–4.4V @ peak 2.0A via dedicated LM2596 buck converter (NOT 5V pin)
// Features:  AT command sequencer, GSM network registration check, SMS dispatch,
//            retry logic, and response timeout protection.
// ==============================================================================
#pragma once
#include <Arduino.h>

static constexpr uint16_t GSM_CMD_TIMEOUT_MS   = 3000;
static constexpr uint16_t GSM_SMS_TIMEOUT_MS   = 10000;
static constexpr uint8_t  GSM_MAX_RETRY        = 3;

class GSMEmergency {
public:
    explicit GSMEmergency(HardwareSerial& serial) : _serial(serial) {}

    void begin(uint32_t baud = 9600) {
        _serial.begin(baud);
        delay(2000);  // SIM800C cold-start time (~2s)
        _initialized = _initModem();
        if (_initialized) {
            Serial.println("[GSM] SIM800C modem ready. Network registration OK.");
        } else {
            Serial.println("[GSM] WARNING: Modem init failed. SMS will be retried.");
        }
    }

    /**
     * @brief Sends a plain-text SMS to the specified E.164 phone number.
     * @param phone  Recipient number, e.g. "+919876543210"
     * @param msg    Message body (max 160 ASCII characters)
     * @return true if SMS was accepted by the modem network.
     */
    bool sendSMS(const char* phone, const char* msg) {
        if (!_initialized) {
            _initialized = _initModem();
        }

        for (uint8_t attempt = 0; attempt < GSM_MAX_RETRY; attempt++) {
            Serial.printf("[GSM] SMS attempt %d/%d to %s\n", attempt + 1, GSM_MAX_RETRY, phone);

            if (!_sendCmd("AT+CMGF=1", "OK", GSM_CMD_TIMEOUT_MS)) continue;

            // Set recipient number
            String cmd = String("AT+CMGS=\"") + phone + "\"";
            _serial.println(cmd);
            if (!_waitFor(">", GSM_CMD_TIMEOUT_MS)) continue;

            // Send message body followed by Ctrl+Z (0x1A)
            _serial.print(msg);
            _serial.write(0x1A);

            if (_waitFor("+CMGS:", GSM_SMS_TIMEOUT_MS)) {
                Serial.println("[GSM] SMS dispatched successfully.");
                return true;
            }
        }

        Serial.println("[GSM] ERROR: All SMS send attempts failed.");
        return false;
    }

    bool isNetworkRegistered() {
        _serial.println("AT+CREG?");
        delay(500);
        String resp = _readResponse(1000);
        return (resp.indexOf("+CREG: 0,1") >= 0 || resp.indexOf("+CREG: 0,5") >= 0);
    }

private:
    HardwareSerial& _serial;
    bool _initialized = false;

    bool _initModem() {
        if (!_sendCmd("AT",        "OK", GSM_CMD_TIMEOUT_MS)) return false;
        if (!_sendCmd("ATE0",      "OK", GSM_CMD_TIMEOUT_MS)) return false;  // Echo off
        if (!_sendCmd("AT+CMGF=1","OK", GSM_CMD_TIMEOUT_MS)) return false;  // SMS text mode
        if (!_sendCmd("AT+CSCS=\"GSM\"", "OK", GSM_CMD_TIMEOUT_MS)) return false;
        return isNetworkRegistered();
    }

    bool _sendCmd(const char* cmd, const char* expected, uint16_t timeout_ms) {
        _serial.println(cmd);
        return _waitFor(expected, timeout_ms);
    }

    bool _waitFor(const char* expected, uint16_t timeout_ms) {
        uint32_t deadline = millis() + timeout_ms;
        String   accum    = "";
        while (millis() < deadline) {
            while (_serial.available()) {
                char c = _serial.read();
                accum += c;
                if (accum.indexOf(expected) >= 0) return true;
            }
            delay(5);
        }
        return false;
    }

    String _readResponse(uint16_t timeout_ms) {
        uint32_t deadline = millis() + timeout_ms;
        String   accum    = "";
        while (millis() < deadline) {
            while (_serial.available()) {
                accum += (char)_serial.read();
            }
            delay(5);
        }
        return accum;
    }
};
