"""
NeuroSign-HMI Max: SmartElex 5" Capacitive Touch Display UI (800x480)
Renders live video overlay, skeletal hand tracking, recognized speech subtitles,
sensor metrics HUD, and interactive touch controls.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, List
import cv2
import numpy as np

logger = logging.getLogger("Display_Touch_UI")

class DisplayTouchUI:
    """
    800x480 Touchscreen UI Engine rendering over Framebuffer / OpenCV Window.
    """
    def __init__(self, width: int = 800, height: int = 480):
        self.width = width
        self.height = height
        self.current_subtitle = "Waiting for gesture..."
        self.confidence = 0.0
        self.sensor_data: Dict[str, Any] = {
            "voc_index": 100,
            "power_mw": 1450.0,
            "temp_c": 26.5,
            "humidity": 55.0,
            "radar_present": True
        }
        self.system_status = "ONLINE (DUAL-BRAIN)"
        self.buttons = [
            {"id": "btn_sos", "rect": (620, 20, 160, 60), "label": "EMERGENCY SOS", "color": (40, 40, 220)},
            {"id": "btn_light", "rect": (620, 95, 160, 50), "label": "TOGGLE LIGHT", "color": (180, 140, 40)},
            {"id": "btn_tts", "rect": (620, 160, 160, 50), "label": "REPEAT VOICE", "color": (50, 160, 50)},
            {"id": "btn_calib", "rect": (620, 225, 160, 50), "label": "CALIBRATE", "color": (120, 80, 180)}
        ]
        self.touch_callback: Optional[Callable[[str], None]] = None

    def set_touch_callback(self, callback: Callable[[str], None]):
        self.touch_callback = callback

    def update_subtitle(self, text: str, confidence: float):
        self.current_subtitle = text
        self.confidence = confidence

    def update_sensors(self, data: Dict[str, Any]):
        self.sensor_data.update(data)

    def handle_touch_event(self, x: int, y: int):
        """Processes capacitive touch coordinates from SmartElex screen."""
        for btn in self.buttons:
            bx, by, bw, bh = btn["rect"]
            if bx <= x <= bx + bw and by <= y <= by + bh:
                logger.info(f"[TOUCH EVENT] Button clicked: {btn['id']}")
                if self.touch_callback:
                    self.touch_callback(btn["id"])
                return

    def render_frame(self, camera_frame: Optional[np.ndarray]) -> np.ndarray:
        """
        Composites camera feed, gesture overlays, subtitles, and HUD onto an 800x480 canvas.
        """
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Background gradient dark theme
        canvas[:] = (24, 20, 28)

        # 1. Main Camera Viewport (Left side: 600x450)
        if camera_frame is not None:
            resized_cam = cv2.resize(camera_frame, (590, 360))
            canvas[20:380, 20:610] = resized_cam
            cv2.rectangle(canvas, (20, 20), (610, 380), (80, 80, 120), 2)
        else:
            cv2.rectangle(canvas, (20, 20), (610, 380), (40, 40, 60), -1)
            cv2.putText(canvas, "CAMERA STREAM INACTIVE", (150, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2)

        # 2. Live Subtitle Banner (Bottom: 590x70)
        cv2.rectangle(canvas, (20, 390), (610, 460), (45, 35, 55), -1)
        cv2.rectangle(canvas, (20, 390), (610, 460), (140, 90, 220), 2)
        
        # Subtitle Text
        sub_text = f"\"{self.current_subtitle}\""
        conf_text = f"Confidence: {int(self.confidence * 100)}%" if self.confidence > 0 else ""
        cv2.putText(canvas, sub_text, (35, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)
        if conf_text:
            cv2.putText(canvas, conf_text, (430, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 230, 150), 1)

        # 3. Interactive Touch Action Buttons (Right column)
        for btn in self.buttons:
            bx, by, bw, bh = btn["rect"]
            cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), btn["color"], -1)
            cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (220, 220, 220), 1)
            cv2.putText(canvas, btn["label"], (bx + 12, by + int(bh * 0.62)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)

        # 4. Sensor Telemetry HUD (Lower right)
        hud_x, hud_y = 620, 290
        cv2.rectangle(canvas, (hud_x, hud_y), (hud_x + 160, 460), (32, 28, 40), -1)
        cv2.rectangle(canvas, (hud_x, hud_y), (hud_x + 160, 460), (70, 60, 90), 1)
        cv2.putText(canvas, "SYSTEM TELEMETRY", (hud_x + 10, hud_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 240), 1)

        metrics = [
            f"Air VOC: {self.sensor_data.get('voc_index', 0)}",
            f"Power: {self.sensor_data.get('power_mw', 0):.0f} mW",
            f"Temp: {self.sensor_data.get('temp_c', 0):.1f} C",
            f"Hum: {self.sensor_data.get('humidity', 0):.0f}%",
            f"Radar: {'ACTIVE' if self.sensor_data.get('radar_present') else 'STANDBY'}"
        ]
        for i, m in enumerate(metrics):
            cv2.putText(canvas, m, (hud_x + 12, hud_y + 45 + (i * 24)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 210, 220), 1)

        return canvas
