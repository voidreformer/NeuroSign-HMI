"""
NeuroSign-HMI: High-Speed Vision Pipeline
Captures 60 FPS video streams from Raspberry Pi Camera Module 3 over MIPI-CSI (1.8V domain)
and provides frame buffers for MediaPipe 3D landmark extraction on the Qualcomm Dragonwing MPU.
"""

import time
import logging
import threading
from typing import Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger("Vision_Pipeline")

class VisionPipeline:
    """
    High-throughput camera ingestion worker for 60 FPS gesture perception.
    """
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480, fps: int = 60):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.fps_actual = 0.0
        self._frame_count = 0
        self._fps_timer = time.time()

    def _get_gstreamer_pipeline(self) -> str:
        """GStreamer pipeline for Qualcomm Spectra 340L ISP on Debian Linux."""
        return (
            f"v4l2src device=/dev/video{self.camera_index} ! "
            f"video/x-raw, width={self.width}, height={self.height}, framerate={self.fps}/1 ! "
            f"videoconvert ! video/x-raw, format=BGR ! appsink drop=true sync=false"
        )

    def start(self) -> bool:
        """Initializes the camera capture device and starts ingestion loop."""
        try:
            # First try optimized V4L2 GStreamer pipeline
            pipeline = self._get_gstreamer_pipeline()
            self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

            # Fallback to direct V4L2 device index
            if not self.cap.isOpened():
                logger.warning("GStreamer pipeline failed. Falling back to direct V4L2 capture.")
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self.cap.isOpened():
                logger.error(f"Cannot open camera device /dev/video{self.camera_index}")
                return False

            self.running = True
            self.worker_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.worker_thread.start()
            logger.info(f"Camera started: {self.width}x{self.height} @ {self.fps} FPS target.")
            return True
        except Exception as e:
            logger.error(f"Failed to start vision pipeline: {e}")
            return False

    def _capture_loop(self):
        """Dedicated high-speed thread keeping frame latency at minimum."""
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.005)
                continue

            # Thread-safe frame swap
            with self.frame_lock:
                self.current_frame = frame

            self._frame_count += 1
            now = time.time()
            if now - self._fps_timer >= 1.0:
                self.fps_actual = self._frame_count / (now - self._fps_timer)
                self._frame_count = 0
                self._fps_timer = now

    def get_latest_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Returns the most recent camera frame."""
        with self.frame_lock:
            if self.current_frame is None:
                return False, None
            return True, self.current_frame.copy()

    def calculate_hand_tracking_offset(self, hand_center_x: float, hand_center_y: float) -> Tuple[int, int]:
        """
        Calculates pan and tilt angle deltas for the SG90 servo motors
        to center the user's hand in the camera frame.
        hand_center_x, hand_center_y: Normalized coordinates (0.0 to 1.0)
        """
        # Center of frame is (0.5, 0.5)
        error_x = hand_center_x - 0.5
        error_y = hand_center_y - 0.5

        # Proportional gain for servo nudging
        pan_delta = int(-error_x * 30)  # Invert for camera mirror
        tilt_delta = int(error_y * 20)

        return pan_delta, tilt_delta

    def stop(self):
        """Stops the camera stream."""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        logger.info("Vision pipeline stopped.")
