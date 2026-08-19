#include "uart_streamer.h"

static HardwareSerial UnoSerial(1); // ESP32 Hardware UART 1

UartStreamer::UartStreamer() :
    _lastStreamTime(0),
    _frameCounter(0)
{
}

bool UartStreamer::begin() {
    // Initialize UART 1 on GPIO 43 (TX) and GPIO 44 (RX)
    UnoSerial.begin(UART_STREAM_BAUD, SERIAL_8N1, PIN_UART_UNO_RX, PIN_UART_UNO_TX);
    return true;
}

void UartStreamer::streamTelemetry(const SystemTelemetry &telemetry) {
    uint32_t now = millis();
    if (now - _lastStreamTime < UART_STREAM_RATE_MS) return;
    _lastStreamTime = now;
    _frameCounter++;

    // Format compact JSON frame for Arduino UNO Q / Processing visualizer
    char buffer[320];
    int len = snprintf(buffer, sizeof(buffer),
        "{\"seq\":%u,\"rf\":%d,\"sig\":%u,\"f1\":%u,\"f2\":%u,\"f3\":%u,"
        "\"p\":%d,\"r\":%d,\"trm\":%u,\"bat\":%u,\"gid\":%u,\"conf\":%.2f,"
        "\"temp\":%.1f,\"hum\":%.1f,\"press\":%.1f,\"voc\":%d,"
        "\"v\":%.2f,\"ma\":%.1f,\"mw\":%.1f,\"rly\":[%d,%d,%d,%d]}\n",
        _frameCounter,
        telemetry.rfConnected ? 1 : 0,
        telemetry.rfSignalQuality,
        telemetry.flex[0],
        telemetry.flex[1],
        telemetry.flex[2],
        telemetry.pitch,
        telemetry.roll,
        telemetry.tremor,
        telemetry.battery,
        telemetry.gestureId,
        telemetry.gestureConfidence,
        telemetry.temperatureC,
        telemetry.humidityPercent,
        telemetry.pressureHpa,
        telemetry.vocIndex,
        telemetry.busVoltageV,
        telemetry.currentMA,
        telemetry.powerMW,
        telemetry.relayState[0] ? 1 : 0,
        telemetry.relayState[1] ? 1 : 0,
        telemetry.relayState[2] ? 1 : 0,
        telemetry.relayState[3] ? 1 : 0
    );

    if (len > 0 && len < (int)sizeof(buffer)) {
        UnoSerial.write((const uint8_t*)buffer, len);
    }
}
