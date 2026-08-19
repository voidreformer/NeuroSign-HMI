#pragma once
#include "config.h"
#include "sound_data.h"

/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: I2S Digital Audio Engine (MAX98357A Class-D Mono Amp Driver)
 * ============================================================================
 */

#include <FS.h>
#include <SD.h>
#include <SPI.h>

class AudioEngine {
public:
    AudioEngine();
    bool begin();
    void playAlert(SoundAlertId alertId);
    bool playAudioFile(const char* filepath);
    void playTone(float freqHz, uint32_t durationMs, float volume = 0.8f);
    void update(); // Non-blocking audio pump & synthesis update
    void setVolume(float vol); // 0.0 to 1.0
    bool isPlaying() const { return _isPlaying; }
    bool isSdCardAvailable() const { return _sdAvailable; }

private:
    float _masterVolume;
    bool  _isPlaying;
    bool  _sdAvailable;
    bool  _isFilePlaying;
    File  _audioFile;
    uint32_t _audioDataSize;
    uint32_t _audioDataBytesRead;
    uint16_t _numChannels;
    uint32_t _sampleRate;

    SoundAlertId _currentAlert;
    uint32_t _alertStartTime;
    uint32_t _alertDuration;
    float _phase;
    float _freq;

    void initI2S();
    bool initSdCard();
    const char* getFilePathForAlert(SoundAlertId alertId);
    void generateAudioFrame();
    void streamFileChunk();
    bool parseWavHeader();
};
