#include "audio_engine.h"
#include "driver/i2s.h"
#include <math.h>

#define I2S_NUM         (I2S_NUM_0)
#define DMA_BUF_COUNT   8
#define DMA_BUF_LEN     256
#define FILE_CHUNK_SIZE 512

static SPIClass sdSpi(FSPI); // Hardware SPI bus for MicroSD Card on ESP32-S3

AudioEngine::AudioEngine() :
    _masterVolume(0.85f),
    _isPlaying(false),
    _sdAvailable(false),
    _isFilePlaying(false),
    _audioDataSize(0),
    _audioDataBytesRead(0),
    _numChannels(1),
    _sampleRate(16000),
    _currentAlert(SOUND_NONE),
    _alertStartTime(0),
    _alertDuration(0),
    _phase(0.0f),
    _freq(440.0f)
{
}

bool AudioEngine::begin() {
    initI2S();
    _sdAvailable = initSdCard();
    playAlert(SOUND_STARTUP);
    return true;
}

void AudioEngine::initI2S() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = AUDIO_SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = DMA_BUF_COUNT,
        .dma_buf_len = DMA_BUF_LEN,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = PIN_I2S_BCLK,
        .ws_io_num = PIN_I2S_LRC,
        .data_out_num = PIN_I2S_DIN,
        .data_in_num = I2S_PIN_NO_CHANGE
    };

    i2s_driver_install(I2S_NUM, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_NUM, &pin_config);
    i2s_zero_dma_buffer(I2S_NUM);
}

bool AudioEngine::initSdCard() {
    pinMode(PIN_SD_CS, OUTPUT);
    digitalWrite(PIN_SD_CS, HIGH);

    sdSpi.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);

    if (!SD.begin(PIN_SD_CS, sdSpi, 20000000)) { // 20 MHz SPI clock
        Serial.println(F("[WARN] MicroSD Card Module not detected on SPI (GPIO 5,6,7,21). Using algorithmic audio synthesis fallback."));
        return false;
    }

    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE) {
        Serial.println(F("[WARN] No MicroSD Card attached."));
        return false;
    }

    uint64_t cardSizeMB = SD.cardSize() / (1024 * 1024);
    Serial.printf("[OK] MicroSD Card Mounted Successfully (%llu MB). Voice Prompt Engine Active.\n", cardSizeMB);
    return true;
}

void AudioEngine::setVolume(float vol) {
    _masterVolume = constrain(vol, 0.0f, 1.0f);
}

const char* AudioEngine::getFilePathForAlert(SoundAlertId alertId) {
    switch (alertId) {
        case SOUND_STARTUP:          return "/startup.wav";
        case SOUND_CALIBRATED:       return "/calibrated.wav";
        case SOUND_WATER_REQUEST:    return "/water.wav";
        case SOUND_FOOD_REQUEST:     return "/food.wav";
        case SOUND_MEDICINE_REQUEST: return "/medicine.wav";
        case SOUND_EMERGENCY_ALARM:  return "/emergency.wav";
        case SOUND_LIGHT_TOGGLE:     return "/light.wav";
        case SOUND_FAN_TOGGLE:       return "/fan.wav";
        case SOUND_BED_ADJUST:       return "/bed.wav";
        case SOUND_CALL_NURSE:       return "/nurse.wav";
        case SOUND_PAIN_ALERT:       return "/pain.wav";
        case SOUND_ALL_OFF:          return "/all_off.wav";
        case SOUND_TREMOR_WARNING:   return "/spasm.wav";
        default:                     return "";
    }
}

bool AudioEngine::parseWavHeader() {
    // Basic RIFF / WAVE Header Parser
    uint8_t header[44];
    if (_audioFile.read(header, 44) < 44) return false;

    // Check "RIFF" and "WAVE"
    if (memcmp(header, "RIFF", 4) != 0 || memcmp(header + 8, "WAVE", 4) != 0) {
        return false;
    }

    _numChannels = header[22] | (header[23] << 8);
    _sampleRate  = header[24] | (header[25] << 8) | (header[26] << 16) | (header[27] << 24);
    uint16_t bitsPerSample = header[34] | (header[35] << 8);

    // Look for 'data' chunk
    if (memcmp(header + 36, "data", 4) == 0) {
        _audioDataSize = header[40] | (header[41] << 8) | (header[42] << 16) | (header[43] << 24);
    } else {
        _audioDataSize = _audioFile.size() - 44;
    }

    _audioDataBytesRead = 0;

    // Adjust I2S sample rate dynamically if needed (e.g. 16kHz, 22.05kHz, 44.1kHz)
    if (_sampleRate >= 8000 && _sampleRate <= 48000 && bitsPerSample == 16) {
        i2s_set_sample_rates(I2S_NUM, _sampleRate);
    }

    return true;
}

bool AudioEngine::playAudioFile(const char* filepath) {
    if (!_sdAvailable || strlen(filepath) == 0) return false;

    if (_isFilePlaying && _audioFile) {
        _audioFile.close();
        _isFilePlaying = false;
    }

    if (!SD.exists(filepath)) {
        // Also check .mp3 or root files
        return false;
    }

    _audioFile = SD.open(filepath, FILE_READ);
    if (!_audioFile) return false;

    if (String(filepath).endsWith(".wav")) {
        if (!parseWavHeader()) {
            _audioFile.close();
            return false;
        }
    } else {
        // Raw PCM / MP3 fallback
        _audioDataSize = _audioFile.size();
        _audioDataBytesRead = 0;
        _numChannels = 1;
    }

    _isFilePlaying = true;
    _isPlaying = true;
    _currentAlert = SOUND_NONE;

    Serial.printf("[AUDIO] Playing SD Voice Recording: %s (%u bytes, %u Hz)\n", filepath, _audioDataSize, _sampleRate);
    return true;
}

void AudioEngine::playAlert(SoundAlertId alertId) {
    // 1. First attempt to play pre-recorded voice audio file from SD card
    const char* filePath = getFilePathForAlert(alertId);
    if (_sdAvailable && playAudioFile(filePath)) {
        return; // File playback active
    }

    // 2. Graceful Fallback: Built-in Algorithmic Speech Chime & Notification Engine
    if (_isFilePlaying && _audioFile) {
        _audioFile.close();
        _isFilePlaying = false;
    }

    // Restore standard 16kHz rate for internal synth
    i2s_set_sample_rates(I2S_NUM, AUDIO_SAMPLE_RATE);

    _currentAlert = alertId;
    _alertStartTime = millis();
    _isPlaying = true;
    _phase = 0.0f;

    switch (alertId) {
        case SOUND_STARTUP:          _alertDuration = 900;  break;
        case SOUND_CALIBRATED:       _alertDuration = 700;  break;
        case SOUND_WATER_REQUEST:    _alertDuration = 1200; break;
        case SOUND_FOOD_REQUEST:     _alertDuration = 1200; break;
        case SOUND_MEDICINE_REQUEST: _alertDuration = 1400; break;
        case SOUND_PAIN_ALERT:       _alertDuration = 2200; break;
        case SOUND_ALL_OFF:          _alertDuration = 800;  break;
        case SOUND_EMERGENCY_ALARM:  _alertDuration = 3000; break;
        case SOUND_LIGHT_TOGGLE:     _alertDuration = 350;  break;
        case SOUND_FAN_TOGGLE:       _alertDuration = 350;  break;
        case SOUND_BED_ADJUST:       _alertDuration = 500;  break;
        case SOUND_CALL_NURSE:       _alertDuration = 1800; break;
        case SOUND_TREMOR_WARNING:   _alertDuration = 2000; break;
        default:                     _isPlaying = false;    break;
    }
}

void AudioEngine::playTone(float freqHz, uint32_t durationMs, float volume) {
    if (_isFilePlaying && _audioFile) {
        _audioFile.close();
        _isFilePlaying = false;
    }
    i2s_set_sample_rates(I2S_NUM, AUDIO_SAMPLE_RATE);
    _freq = freqHz;
    _alertDuration = durationMs;
    _alertStartTime = millis();
    _isPlaying = true;
    _masterVolume = volume;
    _currentAlert = SOUND_NONE;
}

void AudioEngine::streamFileChunk() {
    if (!_audioFile || !_isFilePlaying) {
        _isFilePlaying = false;
        _isPlaying = false;
        return;
    }

    uint8_t readBuf[FILE_CHUNK_SIZE];
    int bytesRead = _audioFile.read(readBuf, sizeof(readBuf));

    if (bytesRead <= 0 || (_audioDataSize > 0 && _audioDataBytesRead >= _audioDataSize)) {
        // End of file reached
        _audioFile.close();
        _isFilePlaying = false;
        _isPlaying = false;
        i2s_zero_dma_buffer(I2S_NUM);
        return;
    }

    _audioDataBytesRead += bytesRead;

    // Apply volume scaling and interleave to Stereo for I2S DAC
    int16_t* inSamples = (int16_t*)readBuf;
    int sampleCount = bytesRead / sizeof(int16_t);

    if (_numChannels == 1) {
        // Mono to Stereo duplication
        int16_t outBuffer[DMA_BUF_LEN * 2];
        int samplesToProcess = min(sampleCount, DMA_BUF_LEN);

        for (int i = 0; i < samplesToProcess; i++) {
            int16_t sample = (int16_t)(inSamples[i] * _masterVolume);
            outBuffer[i * 2]     = sample;
            outBuffer[i * 2 + 1] = sample;
        }

        size_t bytesWritten;
        i2s_write(I2S_NUM, outBuffer, samplesToProcess * 2 * sizeof(int16_t), &bytesWritten, portMAX_DELAY);
    } else {
        // Stereo samples
        for (int i = 0; i < sampleCount; i++) {
            inSamples[i] = (int16_t)(inSamples[i] * _masterVolume);
        }
        size_t bytesWritten;
        i2s_write(I2S_NUM, inSamples, bytesRead, &bytesWritten, portMAX_DELAY);
    }
}

void AudioEngine::update() {
    if (!_isPlaying) return;

    if (_isFilePlaying) {
        streamFileChunk();
        return;
    }

    uint32_t elapsed = millis() - _alertStartTime;
    if (elapsed >= _alertDuration) {
        _isPlaying = false;
        _currentAlert = SOUND_NONE;
        i2s_zero_dma_buffer(I2S_NUM);
        return;
    }

    generateAudioFrame();
}

void AudioEngine::generateAudioFrame() {
    int16_t buffer[DMA_BUF_LEN * 2]; // Stereo interleaved
    uint32_t elapsed = millis() - _alertStartTime;

    float currentFreq = 440.0f;
    float currentAmp = _masterVolume;

    // Synthesize medical notification tones and melodic voice cues
    switch (_currentAlert) {
        case SOUND_STARTUP:
            if (elapsed < 200) currentFreq = 523.25f;       // C5
            else if (elapsed < 400) currentFreq = 659.25f;  // E5
            else if (elapsed < 600) currentFreq = 783.99f;  // G5
            else currentFreq = 1046.50f;                    // C6
            break;

        case SOUND_CALIBRATED:
            if (elapsed < 250) currentFreq = 880.0f;
            else if (elapsed < 350) currentAmp = 0.0f;
            else currentFreq = 1320.0f;
            break;

        case SOUND_WATER_REQUEST:
            if (elapsed < 300) {
                float progress = (float)elapsed / 300.0f;
                currentFreq = 600.0f + (progress * 800.0f);
            } else if (elapsed < 500) {
                currentAmp = 0.0f;
            } else if (elapsed < 800) {
                float progress = (float)(elapsed - 500) / 300.0f;
                currentFreq = 700.0f + (progress * 900.0f);
            } else {
                currentFreq = 1174.66f;
            }
            break;

        case SOUND_FOOD_REQUEST:
            if (elapsed < 300) currentFreq = 659.25f;
            else if (elapsed < 400) currentAmp = 0.0f;
            else if (elapsed < 700) currentFreq = 880.00f;
            else if (elapsed < 800) currentAmp = 0.0f;
            else currentFreq = 1318.51f;
            break;

        case SOUND_MEDICINE_REQUEST:
            if (elapsed < 300) currentFreq = 587.33f;
            else if (elapsed < 400) currentAmp = 0.0f;
            else if (elapsed < 700) currentFreq = 783.99f;
            else if (elapsed < 800) currentAmp = 0.0f;
            else currentFreq = 1174.66f;
            break;

        case SOUND_PAIN_ALERT:
            if ((elapsed % 300) < 150) currentFreq = 1200.0f;
            else currentFreq = 900.0f;
            break;

        case SOUND_ALL_OFF:
            currentFreq = 880.0f - ((float)elapsed / 800.0f) * 440.0f;
            currentAmp *= (1.0f - ((float)elapsed / 800.0f));
            break;

        case SOUND_EMERGENCY_ALARM:
            if ((elapsed / 250) % 2 == 0) currentFreq = 960.0f;
            else currentFreq = 770.0f;
            break;

        case SOUND_LIGHT_TOGGLE:
            currentFreq = 1200.0f;
            currentAmp *= (1.0f - ((float)elapsed / (float)_alertDuration));
            break;

        case SOUND_FAN_TOGGLE:
            currentFreq = 587.33f;
            currentAmp *= (1.0f - ((float)elapsed / (float)_alertDuration));
            break;

        case SOUND_BED_ADJUST:
            currentFreq = 440.0f + (sinf(elapsed * 0.02f) * 60.0f);
            break;

        case SOUND_CALL_NURSE:
            if ((elapsed % 400) < 200) currentFreq = 1000.0f;
            else currentAmp = 0.0f;
            break;

        case SOUND_TREMOR_WARNING:
            currentFreq = 500.0f + (sinf(elapsed * 0.04f) * 150.0f);
            break;

        default:
            currentFreq = _freq;
            break;
    }

    float phaseIncrement = (2.0f * M_PI * currentFreq) / (float)AUDIO_SAMPLE_RATE;

    for (int i = 0; i < DMA_BUF_LEN; i++) {
        float sampleF = (sinf(_phase) * 0.75f + sinf(_phase * 2.0f) * 0.25f) * currentAmp;
        int16_t sample = (int16_t)(sampleF * 28000.0f);

        _phase += phaseIncrement;
        if (_phase >= 2.0f * M_PI) _phase -= 2.0f * M_PI;

        buffer[i * 2]     = sample;
        buffer[i * 2 + 1] = sample;
    }

    size_t bytesWritten;
    i2s_write(I2S_NUM, buffer, sizeof(buffer), &bytesWritten, portMAX_DELAY);
}
