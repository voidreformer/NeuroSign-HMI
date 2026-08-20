"""
NeuroSign-HMI: Digital I2S Audio Subsystem with 1st-Person WAV Playback & 11 Indic Languages
Handles bidirectional digital audio across the INMP441 Microphone (Speech-to-Text)
and MAX98357A I2S Amplifier with support for studio pre-recorded .WAV files and live TTS synthesis.
"""

import os
import time
import queue
import logging
import threading
import subprocess
from typing import Optional, Callable, Dict

logger = logging.getLogger("Audio_I2S")

# Mapping gesture labels to standard .wav audio prompt filenames
GESTURE_WAV_MAP = {
    "Emergency - Need Help": "01_emergency_sos",
    "Turn On Room Light": "02_light_on",
    "Turn Off Room Light": "03_light_off",
    "Water Please": "04_water",
    "Thank You": "05_thank_you",
    "Yes": "06_yes",
    "No": "07_no",
    "Food / Hungry": "08_food_hungry",
    "Medicine / Painkiller": "09_medicine",
    "Severe Pain": "10_severe_pain",
    "Turn On Fan": "11_fan_on",
    "Turn Off Fan": "12_fan_off",
    "Need Washroom": "13_washroom",
    "Call Family": "14_call_family",
    "Time to Sleep": "15_time_to_sleep",
    "spasm_alert": "spasm_alert",
    "startup_online": "startup_online"
}

# eSpeak-NG voice flag mapping
ESPEAK_VOICE_MAP = {
    "en": "en-us",
    "hi": "hi",
    "bn": "bn",
    "ta": "ta",
    "te": "te",
    "mr": "mr",
    "gu": "gu",
    "kn": "kn",
    "ml": "ml",
    "pa": "pa",
    "or": "or"
}


class AudioI2SSubsystem:
    """
    Handles real-time I2S audio playback and recording via ALSA / aplay / arecord.
    """
    def __init__(self, sample_rate: int = 16000, i2s_device: str = "default", default_lang: str = "hi"):
        self.sample_rate = sample_rate
        self.i2s_device = i2s_device
        self.current_lang = default_lang
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.is_listening = False
        self.piper_model_path = "/models/en_US-lessac-medium.onnx"

        # Resolve audio_prompts directory path
        candidate_audio_dirs = [
            "/app/audio_prompts",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio_prompts"),
            os.path.join(os.getcwd(), "audio_prompts"),
        ]
        self.audio_prompts_dir = next((d for d in candidate_audio_dirs if os.path.exists(d)), candidate_audio_dirs[0])

        self._stop_event = threading.Event()
        self._tts_worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._tts_worker_thread.start()
        logger.info(f"AudioI2SSubsystem initialized. Prompts dir: {self.audio_prompts_dir} | Active Lang: {default_lang}")

    def set_language(self, lang_code: str):
        """Set active speech language ('en', 'hi', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'pa', 'or')."""
        if lang_code in ESPEAK_VOICE_MAP:
            self.current_lang = lang_code
            logger.info(f"[AUDIO] Active language switched to: '{lang_code}'")

    def play_wav_file(self, wav_path: str) -> bool:
        """Plays a standard PCM 16-bit WAV file directly through I2S audio device."""
        if not os.path.exists(wav_path):
            return False

        try:
            cmd = f"aplay -D {self.i2s_device} -q \"{wav_path}\""
            subprocess.run(cmd, shell=True, check=True)
            return True
        except Exception as e:
            # Fallback to Windows winsound if testing on Windows PC
            try:
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                return True
            except Exception:
                logger.error(f"Failed to play WAV file {wav_path}: {e}")
                return False

    def speak_gesture(self, gesture_label: str, priority: bool = False) -> str:
        """
        Attempts to play pre-recorded studio .WAV file for the gesture in active language,
        falling back to speech synthesis if needed.
        """
        wav_key = GLOVE_GESTURE_MAP.get(gesture_label)
        if wav_key:
            # Check if language-specific WAV exists
            if self.current_lang == "hi":
                wav_file = os.path.join(self.audio_prompts_dir, "hindi", f"{wav_key}_hi.wav")
            else:
                wav_file = os.path.join(self.audio_prompts_dir, "english", f"{wav_key}.wav")

            if os.path.exists(wav_file):
                logger.info(f"[AUDIO OUT] Playing studio WAV prompt: {wav_file}")
                self.speech_queue.put(("__FILE__:" + wav_file, self.current_lang))
                return gesture_label

        # Fallback to text synthesis
        self.speak(gesture_label, priority=priority, lang=self.current_lang)
        return gesture_label

    def _tts_worker(self):
        """Background worker consuming text/file payloads and vocalizing."""
        while not self._stop_event.is_set():
            try:
                item = self.speech_queue.get(timeout=0.2)
                if item is None:
                    break
                text_payload, lang = item

                if text_payload.startswith("__FILE__:"):
                    wav_path = text_payload.replace("__FILE__:", "")
                    self.play_wav_file(wav_path)
                else:
                    self._synthesize_and_play(text_payload, lang)

                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in Audio worker: {e}")

    def speak(self, text: str, priority: bool = False, lang: Optional[str] = None):
        """
        Queue or immediately synthesize text to voice output.
        """
        if not text or not text.strip():
            return

        speech_lang = lang or self.current_lang
        logger.info(f"[TTS QUEUE] Queuing [{speech_lang}]: '{text}' (Priority={priority})")
        if priority:
            with self.speech_queue.mutex:
                self.speech_queue.queue.clear()
        self.speech_queue.put((text, speech_lang))

    def _synthesize_and_play(self, text: str, lang: str):
        """Executes low-latency offline TTS in selected language."""
        self.is_speaking = True
        logger.info(f"[AUDIO OUT] [{lang}] Vocalizing: '{text}'")
        start_time = time.time()

        try:
            if lang == "en" and os.path.exists("/usr/local/bin/piper") and os.path.exists(self.piper_model_path):
                cmd = f"echo '{text}' | /usr/local/bin/piper --model {self.piper_model_path} --output-raw | aplay -D {self.i2s_device} -r 22050 -f S16_LE -t raw -q"
                subprocess.run(cmd, shell=True, check=True)
            else:
                voice_id = ESPEAK_VOICE_MAP.get(lang, "hi")
                cmd = ["espeak-ng", "-s", "140", "-v", voice_id, text]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            latency = (time.time() - start_time) * 1000.0
            logger.info(f"[AUDIO OUT] Speech completed in {latency:.1f} ms")
        except Exception as e:
            logger.error(f"TTS Playback failed: {e}")
        finally:
            self.is_speaking = False

    def start_listening(self, callback: Callable[[bytes], None], duration_sec: float = 3.0):
        """Captures audio from the INMP441 digital microphone for STT."""
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
