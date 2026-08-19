"""
NeuroSign-HMI: SmartElex 5" Capacitive Touch Display UI (800x480)
Renders real-time live camera feed, bilingual subtitle ribbons (English + Active Indian Language),
skeletal hand tracking, recognized speech subtitles, sensor metrics HUD,
and interactive touch controls with multi-lingual TrueType Indian language font support.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Ensure local import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indic_language_engine import IndicLanguageEngine

logger = logging.getLogger("Display_Touch_UI")


class DisplayTouchUI:
    """
    800x480 Touchscreen UI Engine rendering bilingual HUD over Framebuffer / OpenCV Window
    supporting 11 Indian Languages.
    """
    def __init__(self, width: int = 800, height: int = 480, default_lang: str = "hi"):
        self.width = width
        self.height = height
        self.lang_engine = IndicLanguageEngine(default_lang=default_lang)

        self.current_subtitle_en = "Waiting for gesture..."
        self.current_subtitle_indic = self.lang_engine.get_ui_string("waiting_gesture")
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
            {"id": "btn_sos", "rect": (620, 20, 160, 55), "label_id": "btn_sos", "color": (40, 40, 220)},
            {"id": "btn_light", "rect": (620, 85, 160, 50), "label_id": "btn_light", "color": (180, 140, 40)},
            {"id": "btn_lang", "rect": (620, 145, 160, 50), "label_id": "btn_lang", "color": (140, 70, 180)},
            {"id": "btn_tts", "rect": (620, 205, 160, 50), "label_id": "btn_tts", "color": (50, 160, 50)}
        ]
        self.touch_callback: Optional[Callable[[str], None]] = None
        self._init_fonts()

    def _init_fonts(self):
        """Finds and loads Indian multi-script TrueType fonts across Windows and Linux."""
        font_candidates = [
            "C:/Windows/Fonts/Nirmala.ttf",
            "C:/Windows/Fonts/mangal.ttf",
            "C:/Windows/Fonts/aparaj.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        self.font_large = None
        self.font_indic = None
        self.font_btn = None
        self.font_hud = None

        for font_path in font_candidates:
            if os.path.exists(font_path):
                try:
                    self.font_large = ImageFont.truetype(font_path, 22)
                    self.font_indic = ImageFont.truetype(font_path, 20)
                    self.font_btn = ImageFont.truetype(font_path, 13)
                    self.font_hud = ImageFont.truetype(font_path, 14)
                    logger.info(f"Loaded Indic TrueType font from {font_path}")
                    return
                except Exception:
                    pass

        # Fallback to Pillow default
        self.font_large = ImageFont.load_default()
        self.font_indic = ImageFont.load_default()
        self.font_btn = ImageFont.load_default()
        self.font_hud = ImageFont.load_default()

    def set_touch_callback(self, callback: Callable[[str], None]):
        self.touch_callback = callback

    def update_subtitle(self, text_en: str, text_indic: str = "", confidence: float = 0.0):
        """Updates bilingual subtitles for English and active Indian language."""
        self.current_subtitle_en = text_en
        self.current_subtitle_indic = text_indic if text_indic else text_en
        self.confidence = confidence

    def update_sensors(self, data: Dict[str, Any]):
        self.sensor_data.update(data)

    def cycle_language(self) -> str:
        """Cycles active Indian language and updates UI text."""
        new_lang = self.lang_engine.cycle_language()
        self.current_subtitle_indic = self.lang_engine.get_ui_string("waiting_gesture")
        return new_lang

    def handle_touch_event(self, x: int, y: int):
        """Processes capacitive touch coordinates from SmartElex screen."""
        for btn in self.buttons:
            bx, by, bw, bh = btn["rect"]
            if bx <= x <= bx + bw and by <= y <= by + bh:
                logger.info(f"[TOUCH EVENT] Button clicked: {btn['id']}")
                if btn["id"] == "btn_lang":
                    self.cycle_language()

                if self.touch_callback:
                    self.touch_callback(btn["id"])
                return

    def render_frame(self, camera_frame: Optional[np.ndarray]) -> np.ndarray:
        """
        Composites camera feed, gesture overlays, bilingual subtitles, and HUD onto an 800x480 canvas.
        """
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Background gradient dark theme
        canvas[:] = (24, 20, 28)

        # 1. Main Camera Viewport (Left side: 590x350)
        if camera_frame is not None:
            resized_cam = cv2.resize(camera_frame, (590, 350))
            canvas[15:365, 15:605] = resized_cam
            cv2.rectangle(canvas, (15, 15), (605, 365), (80, 80, 120), 2)
        else:
            cv2.rectangle(canvas, (15, 15), (605, 365), (40, 40, 60), -1)
            cv2.putText(canvas, "CAMERA STREAM INACTIVE", (150, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2)

        # 2. Live Bilingual Subtitle Banner (Bottom: 590x90)
        cv2.rectangle(canvas, (15, 375), (605, 465), (35, 25, 45), -1)
        cv2.rectangle(canvas, (15, 375), (605, 465), (160, 100, 240), 2)

        # 3. Interactive Touch Action Buttons (Right column)
        for btn in self.buttons:
            bx, by, bw, bh = btn["rect"]
            cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), btn["color"], -1)
            cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (220, 220, 220), 1)

        # 4. Sensor Telemetry HUD (Lower right)
        hud_x, hud_y = 620, 265
        cv2.rectangle(canvas, (hud_x, hud_y), (hud_x + 160, 465), (32, 28, 40), -1)
        cv2.rectangle(canvas, (hud_x, hud_y), (hud_x + 160, 465), (70, 60, 90), 1)

        # Convert OpenCV canvas to PIL Image for rendering TrueType Indian Scripts + English text
        pil_img = Image.fromarray(canvas)
        draw = ImageDraw.Draw(pil_img)

        # Draw Bilingual Subtitles
        active_code = self.lang_engine.active_lang.upper()
        en_text = f"EN: \"{self.current_subtitle_en}\""
        indic_text = f"{active_code}: \"{self.current_subtitle_indic}\""
        conf_str = f"[{int(self.confidence * 100)}%]" if self.confidence > 0 else ""

        draw.text((25, 383), f"{en_text}  {conf_str}", font=self.font_large, fill=(255, 255, 255))
        draw.text((25, 420), indic_text, font=self.font_indic, fill=(255, 215, 90))

        # Draw Bilingual Buttons with Active Language
        for btn in self.buttons:
            bx, by, bw, bh = btn["rect"]
            lbl_id = btn["label_id"]
            lbl_en = self.lang_engine.get_ui_string(lbl_id, "en")
            lbl_indic = self.lang_engine.get_ui_string(lbl_id, self.lang_engine.active_lang)

            if btn["id"] == "btn_lang":
                # Special dynamic language switcher badge
                langs = self.lang_engine.data.get("metadata", {}).get("supported_languages", {})
                curr_native = langs.get(self.lang_engine.active_lang, {}).get("native", "हिंदी")
                draw.text((bx + 12, by + 8), f"LANG: {active_code}", font=self.font_btn, fill=(255, 255, 255))
                draw.text((bx + 12, by + 26), f"> {curr_native}", font=self.font_btn, fill=(255, 230, 100))
            else:
                draw.text((bx + 12, by + 8), lbl_en, font=self.font_btn, fill=(255, 255, 255))
                if lbl_indic and lbl_indic != lbl_en:
                    draw.text((bx + 12, by + 26), lbl_indic, font=self.font_btn, fill=(255, 220, 120))

        # Draw HUD Sensor Metrics
        draw.text((hud_x + 10, hud_y + 8), "SYSTEM TELEMETRY", font=self.font_hud, fill=(180, 180, 240))
        metrics = [
            f"Air VOC: {self.sensor_data.get('voc_index', 0)}",
            f"Power: {self.sensor_data.get('power_mw', 0):.0f} mW",
            f"Temp: {self.sensor_data.get('temp_c', 0):.1f}°C",
            f"Hum: {self.sensor_data.get('humidity', 0):.0f}%",
            f"Radar: {'ACTIVE' if self.sensor_data.get('radar_present') else 'STANDBY'}"
        ]
        for i, m in enumerate(metrics):
            draw.text((hud_x + 12, hud_y + 32 + (i * 22)), m, font=self.font_hud, fill=(210, 220, 230))

        # Convert back to OpenCV NumPy format
        return np.array(pil_img)
