#include "rf_receiver.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Native ESP32-S3 433 MHz RF Demodulator Implementation
 * ============================================================================
 */

// Timing thresholds in microseconds
#define SYNC_MIN_US        1000
#define SYNC_MAX_US        1600
#define BIT0_MAX_US        430
#define BIT1_MIN_US        440
#define BIT1_MAX_US        850
#define TOTAL_PACKET_BITS  88  // 11 bytes * 8 bits

enum RfRxState {
    STATE_WAIT_SYNC,
    STATE_RECEIVING_BITS
};

static volatile RfRxState g_rxState = STATE_WAIT_SYNC;
static volatile uint32_t  g_lastEdgeTime = 0;
static volatile uint32_t  g_highDuration = 0;
static volatile uint8_t   g_bitCount = 0;
static volatile uint8_t   g_rxRawBuffer[sizeof(NeuroTxPacket) + 2];
static volatile bool      g_newPacketReady = false;

// Hardware Interrupt Handler for GPIO 4 (Runs in IRAM for high speed)
void IRAM_ATTR isr_rf_pulse() {
    uint32_t now = micros();
    uint32_t duration = now - g_lastEdgeTime;
    g_lastEdgeTime = now;
    int pinLevel = digitalRead(PIN_RF_RX_DATA);

    // If pin went LOW, we just finished measuring a HIGH pulse
    if (pinLevel == LOW) {
        g_highDuration = duration;

        if (g_rxState == STATE_WAIT_SYNC) {
            // Check for Sync Marker (~1200us HIGH pulse)
            if (duration >= SYNC_MIN_US && duration <= SYNC_MAX_US) {
                g_rxState = STATE_RECEIVING_BITS;
                g_bitCount = 0;
                memset((void*)g_rxRawBuffer, 0, sizeof(g_rxRawBuffer));
            }
        }
    } else {
        // Pin went HIGH, we just finished measuring a LOW duration
        if (g_rxState == STATE_RECEIVING_BITS) {
            uint8_t bitVal = 0;

            // Classify bit based on previous HIGH pulse duration
            if (g_highDuration >= 150 && g_highDuration <= BIT0_MAX_US) {
                bitVal = 0; // Short HIGH pulse = 0
            } else if (g_highDuration >= BIT1_MIN_US && g_highDuration <= BIT1_MAX_US) {
                bitVal = 1; // Long HIGH pulse = 1
            } else {
                // Glitch / Noise: reset to wait for new sync
                g_rxState = STATE_WAIT_SYNC;
                return;
            }

            // Store bit in buffer
            uint8_t byteIdx = g_bitCount / 8;
            uint8_t bitIdx  = 7 - (g_bitCount % 8);
            if (byteIdx < sizeof(NeuroTxPacket)) {
                if (bitVal) {
                    g_rxRawBuffer[byteIdx] |= (1 << bitIdx);
                }
            }

            g_bitCount++;

            if (g_bitCount >= TOTAL_PACKET_BITS) {
                g_newPacketReady = true;
                g_rxState = STATE_WAIT_SYNC;
            }
        }
    }
}

RfReceiver::RfReceiver() :
    _lastSequenceId(0),
    _lastPacketReceivedTime(0),
    _totalReceivedCount(0),
    _totalDroppedCount(0),
    _linkQuality(0)
{
}

bool RfReceiver::begin() {
    pinMode(PIN_RF_RX_DATA, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIN_RF_RX_DATA), isr_rf_pulse, CHANGE);
    return true;
}

uint8_t RfReceiver::calculateChecksum(const NeuroTxPacket &pkt) {
    const uint8_t* ptr = (const uint8_t*)&pkt;
    uint8_t crc = 0xAA;
    for (size_t i = 0; i < sizeof(NeuroTxPacket) - 1; i++) {
        crc ^= ptr[i];
        crc = (crc << 1) | (crc >> 7);
    }
    return crc;
}

bool RfReceiver::pollPacket(NeuroTxPacket &outPacket) {
    if (g_newPacketReady) {
        g_newPacketReady = false;

        NeuroTxPacket* candidate = (NeuroTxPacket*)g_rxRawBuffer;
        if (candidate->preamble == PROTOCOL_MAGIC_BYTE) {
            uint8_t calculated = calculateChecksum(*candidate);
            if (calculated == candidate->checksum) {
                // Check sequence difference to track dropped packets
                if (_totalReceivedCount > 0) {
                    uint8_t expectedSeq = _lastSequenceId + 1;
                    if (candidate->sequenceId != expectedSeq) {
                        uint8_t diff = candidate->sequenceId - expectedSeq;
                        if (diff > 0 && diff < 50) {
                            _totalDroppedCount += diff;
                        }
                    }
                }

                _lastSequenceId = candidate->sequenceId;
                _lastPacketReceivedTime = millis();
                _totalReceivedCount++;
                memcpy(&outPacket, candidate, sizeof(NeuroTxPacket));
                return true;
            }
        }
    }
    return false;
}

void RfReceiver::updateLinkStats(SystemTelemetry &telemetry) {
    uint32_t now = millis();
    bool connected = (now - _lastPacketReceivedTime < RF_RX_TIMEOUT_MS) && (_totalReceivedCount > 0);
    telemetry.rfConnected = connected;
    telemetry.packetsReceived = _totalReceivedCount;
    telemetry.packetsDropped = _totalDroppedCount;

    if (!connected) {
        telemetry.rfSignalQuality = 0;
    } else {
        uint32_t total = _totalReceivedCount + _totalDroppedCount;
        if (total > 0) {
            float ratio = (float)_totalReceivedCount / (float)total;
            uint8_t qual = (uint8_t)(ratio * 100.0f);
            telemetry.rfSignalQuality = constrain(qual, 10, 100);
        } else {
            telemetry.rfSignalQuality = 100;
        }
    }
}
