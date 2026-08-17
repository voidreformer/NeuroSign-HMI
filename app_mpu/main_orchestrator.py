"""
NeuroSign-HMI: Master Linux MPU Orchestrator Daemon
Integrates 60 FPS Video, Digital I2S Audio (TTS/STT), SmartElex 5" Touch UI,
Edge AI Gesture Classification (Nemotron-generated), and MessagePack IPC Bridge
for real-time dual-brain coordination on Arduino UNO Q (4GB LPDDR4X).
"""

import time
import sys
import logging
import cv2
import numpy as np

from ipc_bridge import IPCBridgeManager
from audio_i2s import AudioI2SSubsystem
from vision_pipeline import VisionPipeline
from display_touch_ui import DisplayTouchUI
from landmark_extractor import LandmarkExtractor       # Nemotron Phase 3
from gesture_classifier import GestureClassifier       # Nemotron Phase 3

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("Main_Orchestrator")


class NeuroSignOrchestrator:
    def __init__(self):
        logger.info("=======================================================")
        logger.info("   Starting NeuroSign-HMI Orchestration Engine         ")
        logger.info("   Arduino UNO Q (Qualcomm QRB2210 + STM32U585 Dual-Brain)")
        logger.info("=======================================================")

        # 1. Initialize IPC Bridge
        self.ipc = IPCBridgeManager()

        # 2. Initialize Audio Subsystem (I2S Mic & Amp)
        self.audio = AudioI2SSubsystem(sample_rate=16000, i2s_device="default")

        # 3. Initialize Vision Pipeline (RPi Camera v3 @ 60 FPS)
        self.vision = VisionPipeline(camera_index=0, width=640, height=480, fps=60)

        # 4. Initialize Touchscreen UI (800x480)
        self.ui = DisplayTouchUI(width=800, height=480)
        self.ui.set_touch_callback(self._on_ui_touch_button)

        # 5. Initialize Nemotron-generated AI Pipeline
        self.landmark_extractor = LandmarkExtractor(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
            model_complexity=1,
            smoothing_alpha=0.7,
        )
        self.gesture_classifier = GestureClassifier(
            model_path="/app/models/gesture_lstm_int8.tflite",
            labels_path="/app/models/labels.json",
            sequence_length=30,
            confidence_threshold=0.85,
            use_gpu_delegate=True,     # Adreno 702 OpenCL
        )
        # State tracking
        self.running = False
        self.light_state = False
        self.last_radar_wake = time.time()
        self.current_pan = 90
        self.current_tilt = 90
        self.emergency_contact = "+919876543210"

        # Register MCU Telemetry Callbacks
        self.ipc.register_callback("radar_presence", self._on_radar_update)
        self.ipc.register_callback("sensor_telemetry", self._on_sensor_update)

    def _on_radar_update(self, payload: dict):
        """Dispatched when HLK-LD2410C radar detects human presence."""
        is_present = payload.get("present", False)
        self.ui.update_sensors({"radar_present": is_present})
        if is_present:
            self.last_radar_wake = time.time()

    def _on_sensor_update(self, payload: dict):
        """Dispatched when SGP40, INA219, and DHT22 telemetry arrives from MCU."""
        self.ui.update_sensors(payload)

    def _on_ui_touch_button(self, button_id: str):
        """Handles physical touch interactions on the SmartElex 5" display."""
        if button_id == "btn_sos":
            self.trigger_emergency_protocol()
        elif button_id == "btn_light":
            self.light_state = not self.light_state
            self.ipc.trigger_relay(1, self.light_state)
            self.audio.speak(f"Room light turned {'on' if self.light_state else 'off'}")
        elif button_id == "btn_tts":
            self.audio.speak(self.ui.current_subtitle, priority=True)
        elif button_id == "btn_calib":
            self.audio.speak("Entering gesture calibration mode.")
            self.ipc.update_matrix_glyph(0)

    def trigger_emergency_protocol(self):
        """Fires complete multi-channel emergency alert sequence."""
        logger.warning("[EMERGENCY] Triggering full emergency alert protocol!")
        self.ui.update_subtitle("EMERGENCY - NEED HELP!", 1.0)
        self.audio.speak("Emergency alert triggered! Sending SOS dispatch!", priority=True)
        self.ipc.trigger_relay(2, True)  # Strobe Alarm Relay ON
        self.ipc.update_matrix_glyph(2)  # SOS Flash on 8x13 LED Matrix
        self.ipc.send_emergency_sms(
            self.emergency_contact,
            "URGENT SOS: User triggered emergency assistance via NeuroSign-HMI Station."
        )

    def handle_classified_gesture(self, gesture_label: str, confidence: float, hand_center: tuple):
        """
        Called when the AI Edge model classifies a dynamic gesture.
        """
        if confidence < 0.80:
            return

        self.ui.update_subtitle(gesture_label, confidence)
        self.ipc.update_matrix_glyph(1)  # Success tick glyph

        # Perform Action based on recognized gesture
        if gesture_label == "Emergency - Need Help":
            self.trigger_emergency_protocol()
        elif gesture_label == "Turn On Room Light":
            self.light_state = True
            self.ipc.trigger_relay(1, True)
            self.audio.speak("Turning on room light.")
        elif gesture_label == "Turn Off Room Light":
            self.light_state = False
            self.ipc.trigger_relay(1, False)
            self.audio.speak("Turning off room light.")
        elif gesture_label == "Water Please":
            self.audio.speak("I need a glass of water, please.")
        elif gesture_label == "Thank You":
            self.audio.speak("Thank you very much.")
        elif gesture_label == "Yes":
            self.audio.speak("Yes, understood.")
        elif gesture_label == "No":
            self.audio.speak("No, thank you.")

        # Smooth servo camera auto-tracking
        if hand_center:
            pan_delta, tilt_delta = self.vision.calculate_hand_tracking_offset(hand_center[0], hand_center[1])
            self.current_pan = max(10, min(170, self.current_pan + pan_delta))
            self.current_tilt = max(20, min(160, self.current_tilt + tilt_delta))
            self.ipc.set_camera_pan_tilt(self.current_pan, self.current_tilt)

    def start(self):
        """Starts main execution loop."""
        self.running = True
        if not self.vision.start():
            logger.error("Failed to start vision pipeline. Exiting.")
            return

        self.audio.speak("NeuroSign assistive station online and ready.")
        self.ipc.set_camera_pan_tilt(90, 90)
        self.ipc.update_matrix_glyph(0)
        self.landmark_extractor.begin()

        logger.info("Entering main orchestration loop...")
        try:
            while self.running:
                # 1. Fetch latest camera frame (60 FPS)
                ret, frame = self.vision.get_latest_frame()

                annotated_frame = frame

                if ret and frame is not None:
                    # 2. Extract MediaPipe 3D hand landmarks (Nemotron pipeline)
                    landmarks, hand_center, annotated_frame = \
                        self.landmark_extractor.process(frame)

                    if landmarks is not None:
                        # 3. Feed landmarks into 1D-LSTM classifier (Adreno 702 GPU)
                        self.gesture_classifier.update(landmarks)
                        result = self.gesture_classifier.classify()

                        if result is not None:
                            gesture_label, confidence = result
                            # 4. Dispatch classified gesture to action handler
                            self.handle_classified_gesture(
                                gesture_label, confidence, hand_center
                            )

                # 5. Render the 800x480 Touch UI canvas with annotated frame
                ui_canvas = self.ui.render_frame(annotated_frame)
                cv2.imshow("NeuroSign-HMI UI", ui_canvas)
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or key == ord('q'):
                    break

                time.sleep(0.005)   # ~200 Hz UI refresh budget

        except KeyboardInterrupt:
            logger.info("Shutdown signal received.")
        finally:
            self.shutdown()

    def shutdown(self):
        """Gracefully tears down all hardware and worker threads."""
        logger.info("Shutting down NeuroSign-HMI...")
        self.running = False
        self.vision.stop()
        self.audio.shutdown()
        self.landmark_extractor.close()
        cv2.destroyAllWindows()
        logger.info("Shutdown complete.")



if __name__ == "__main__":
    app = NeuroSignOrchestrator()
    app.start()
