"""
NeuroSign-HMI: Multi-Lingual Indic Language & Translation Engine
Supports dynamic real-time language switching across 11 Indian languages:
English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia.
"""

import os
import json
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("IndicLanguageEngine")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LANGUAGES_JSON_PATH = os.path.join(SCRIPT_DIR, "..", "models", "indic_languages.json")


class IndicLanguageEngine:
    """
    Manages multi-lingual text translation, UI strings, and TTS speech synthesis phrases
    for 11 official Indian languages.
    """
    def __init__(self, default_lang: str = "hi", secondary_lang: str = "en"):
        self.active_lang = default_lang
        self.secondary_lang = secondary_lang
        self.data: Dict[str, Any] = {}
        self.lang_cycle = ["hi", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "or", "en"]
        self.current_cycle_idx = self.lang_cycle.index(default_lang) if default_lang in self.lang_cycle else 0
        self._load_data()

    def _load_data(self):
        """Loads translations from indic_languages.json."""
        if not os.path.exists(LANGUAGES_JSON_PATH):
            logger.error(f"Indic languages file not found at: {LANGUAGES_JSON_PATH}")
            return

        try:
            with open(LANGUAGES_JSON_PATH, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            logger.info(f"Indic Language Engine initialized with {len(self.get_available_languages())} languages.")
        except Exception as e:
            logger.error(f"Failed to load indic_languages.json: {e}")

    def get_available_languages(self) -> List[Tuple[str, str, str]]:
        """Returns list of (code, name, native_name) for all supported languages."""
        if not self.data or "metadata" not in self.data:
            return [("en", "English", "English"), ("hi", "Hindi", "हिंदी")]
        langs = self.data["metadata"]["supported_languages"]
        return [(code, info["name"], info["native"]) for code, info in langs.items()]

    def set_language(self, lang_code: str) -> bool:
        """Sets the active primary language (e.g. 'hi', 'bn', 'ta', 'en')."""
        langs = self.data.get("metadata", {}).get("supported_languages", {})
        if lang_code in langs:
            self.active_lang = lang_code
            if lang_code in self.lang_cycle:
                self.current_cycle_idx = self.lang_cycle.index(lang_code)
            logger.info(f"[LANGUAGE] Active language switched to: {langs[lang_code]['name']} ({langs[lang_code]['native']})")
            return True
        logger.warning(f"[LANGUAGE] Unsupported language code: {lang_code}")
        return False

    def cycle_language(self) -> str:
        """Cycles to the next Indian language (called when tapping the LANG button on screen)."""
        self.current_cycle_idx = (self.current_cycle_idx + 1) % len(self.lang_cycle)
        self.active_lang = self.lang_cycle[self.current_cycle_idx]
        langs = self.data.get("metadata", {}).get("supported_languages", {})
        active_name = langs.get(self.active_lang, {}).get("native", self.active_lang)
        logger.info(f"[LANGUAGE CYCLE] Switched to: {self.active_lang} ({active_name})")
        return self.active_lang

    def get_gesture_translation(self, gesture_id_or_name: Any, lang_code: Optional[str] = None) -> Tuple[str, str]:
        """
        Returns (label, spoken_phrase) in the requested or active language.
        """
        lang = lang_code or self.active_lang
        gestures = self.data.get("gestures", {})

        # Find gesture entry by ID or Name
        target = None
        key_str = str(gesture_id_or_name)
        if key_str in gestures:
            target = gestures[key_str]
        else:
            for gid, gdata in gestures.items():
                if gdata.get("name") == str(gesture_id_or_name) or gdata.get("en", {}).get("label") == str(gesture_id_or_name):
                    target = gdata
                    break

        if not target:
            return (str(gesture_id_or_name), str(gesture_id_or_name))

        # Retrieve in specified language or fallback to English
        trans = target.get(lang, target.get("en", {}))
        label = trans.get("label", target.get("en", {}).get("label", str(gesture_id_or_name)))
        phrase = trans.get("phrase", target.get("en", {}).get("phrase", label))

        return (label, phrase)

    def get_ui_string(self, string_id: str, lang_code: Optional[str] = None) -> str:
        """Returns translated UI string (buttons, HUD, status)."""
        lang = lang_code or self.active_lang
        ui_strings = self.data.get("ui_strings", {})
        if string_id in ui_strings:
            return ui_strings[string_id].get(lang, ui_strings[string_id].get("en", string_id))
        return string_id

    def get_bilingual_pair(self, gesture_id_or_name: Any) -> Tuple[str, str, str]:
        """
        Returns (english_label, active_indic_label, spoken_phrase) for screen subtitle rendering.
        """
        en_label, en_phrase = self.get_gesture_translation(gesture_id_or_name, "en")
        indic_label, indic_phrase = self.get_gesture_translation(gesture_id_or_name, self.active_lang)

        # Spoken phrase is chosen in active language
        return (en_label, indic_label, indic_phrase)
