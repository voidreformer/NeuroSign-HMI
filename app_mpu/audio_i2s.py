"""
NeuroSign-HMI Max: Digital I2S Audio Subsystem
Manages bidirectional audio across the INMP441 Microphone (Speech-to-Text)
and MAX98357A I2S Amplifier (Piper Offline Text-to-Speech Engine).
"""

import os
import time
import wave
import queue
import logging
import threading
import subprocess
from typing import Optional, Callable

logger = logging.getLogger("Audio_I2S")

class AudioI2SSubsystem:
    """
    Handles real-time I2S audio playback and recording via ALSA / PulseAudio.
    """
    def __init__(self, sample_rate: int = 16000, i2s_device: str = "default"):
        self.sample_rate = sample_rate
        self.i2s_device = i2s_device
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.is_listening = False
        self.piper_model_path = "/models/en_US-lessac-medium.onnx"
        self._stop_event = threading.Event()
        self._tts_worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._tts_worker_thread.start()

    def _tts_worker(self):
        """Background worker consuming text from speech queue and vocalizing."""
        while not self._stop_event.is_set():
            try:
                text_payload = self.speech_queue.get(timeout=0.2)
                if text_payload is None:
                    break
                self._synthesize_and_play(text_payload)
                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in TTS worker: {e}")

    def speak(self, text: str, priority: bool = False):
        """
        Queue or immediately synthesize text to voice output.
        """
        if not text or not text.strip():
            return

        logger.info(f"[TTS QUEUE] Queuing speech: '{text}' (Priority={priority})")
        if priority:
            # Clear old queue for urgent emergency speech
            with self.speech_queue.mutex:
                self.speech_queue.queue.clear()
        self.speech_queue.put(text)

    def _synthesize_and_play(self, text: str):
        """Executes low-latency offline Piper TTS or fallback eSpeak-NG."""
        self.is_speaking = True
        logger.info(f"[AUDIO OUT] Vocalizing: '{text}'")
        start_time = time.time()

        try:
            # Check if Piper TTS binary exists
            if os.path.exists("/usr/local/bin/piper") and os.path.exists(self.piper_model_path):
                # Piper generates raw PCM / WAV streamed directly into aplay
                cmd = f"echo '{text}' | /usr/local/bin/piper --model {self.piper_model_path} --output-raw | aplay -D {self.i2s_device} -r 22050 -f S16_LE -t raw -q"
                subprocess.run(cmd, shell=True, check=True)
            else:
                # Fallback to ultra-lightweight eSpeak-NG
                cmd = ["espeak-ng", "-s", "140", "-v", "en-us", text]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            latency = (time.time() - start_time) * 1000.0
            logger.info(f"[AUDIO OUT] Speech completed in {latency:.1f} ms")
        except Exception as e:
            logger.error(f"TTS Playback failed: {e}")
        finally:
            self.is_speaking = False

    def start_listening(self, callback: Callable[[bytes], None], duration_sec: float = 3.0):
        """
        Captures audio from the INMP441 digital microphone for STT.
        """
        def _recorder():
            self.is_listening = True
            logger.info("[AUDIO IN] Recording from INMP441 I2S Microphone...")
            temp_wav = "/tmp/inmp441_recording.wav"
            try:
                cmd = [
                    "arecord",
                    "-D", self.i2s_device,
                    "-r", str(self.sample_rate),
                    "-c", "1",
                    "-f", "S16_LE",
                    "-d", str(int(duration_sec)),
                    "-q",
                    temp_wav
                ]
                subprocess.run(cmd, check=True)
                if os.path.exists(temp_wav):
                    with open(temp_wav, "rb") as f:
                        audio_data = f.read()
                    callback(audio_data)
            except Exception as e:
                logger.error(f"Microphone capture error: {e}")
            finally:
                self.is_listening = False

        record_thread = threading.Thread(target=_recorder, daemon=True)
        record_thread.start()

    def shutdown(self):
        """Cleans up audio worker threads."""
        self._stop_event.set()
        self.speech_queue.put(None)
        if self._tts_worker_thread.is_alive():
            self._tts_worker_thread.join(timeout=1.0)
