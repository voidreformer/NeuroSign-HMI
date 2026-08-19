"""
NeuroSign-HMI: 3D Gesture Library & Bilingual Voice Dictionary Manager
Manages 3D Hand Motion Assets, Live Camera Recording, Blender Animation Export,
and 1-Click Neural Training with Bilingual Spoken Voice Phrases (English & Hindi).
"""

import os
import sys
import json
import time
import argparse
import numpy as np
import cv2

# Ensure UTF-8 stdout support on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    mp = None
    MEDIAPIPE_AVAILABLE = False


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIBRARY_DIR = os.path.join(SCRIPT_DIR, "gesture_library_3d")
LABELS_PATH = os.path.join(SCRIPT_DIR, "labels.json")
DATASET_PATH = os.path.join(SCRIPT_DIR, "gestures_dataset.npz")


DEFAULT_GESTURES_15 = [
    {
        "id": 0, "name": "emergency",
        "label": "Emergency - Need Help", "label_hi": "आपातकालीन सहायता",
        "spoken_phrase": "Emergency! I need urgent help immediately!", "phrase_hi": "आपातकाल! मुझे तुरंत सहायता की आवश्यकता है!",
        "action": "EMERGENCY_SMS_ALARM", "led_glyph": "SOS_STROBE"
    },
    {
        "id": 1, "name": "light_on",
        "label": "Turn On Room Light", "label_hi": "कमरे की लाइट चालू करें",
        "spoken_phrase": "Please turn on the room light.", "phrase_hi": "कृपया कमरे की लाइट चालू कर दीजिए।",
        "action": "RELAY_CH1_ON", "led_glyph": "LIGHT_BULB"
    },
    {
        "id": 2, "name": "light_off",
        "label": "Turn Off Room Light", "label_hi": "कमरे की लाइट बंद करें",
        "spoken_phrase": "Please turn off the room light.", "phrase_hi": "कृपया कमरे की लाइट बंद कर दीजिए।",
        "action": "RELAY_CH1_OFF", "led_glyph": "MOON"
    },
    {
        "id": 3, "name": "water",
        "label": "Water Please", "label_hi": "कृपया पानी दीजिए",
        "spoken_phrase": "Could you please give me a glass of water?", "phrase_hi": "कृपया मुझे एक गिलास पानी दीजिए।",
        "action": "SPEECH_ASSIST", "led_glyph": "WATER_DROP"
    },
    {
        "id": 4, "name": "thanks",
        "label": "Thank You", "label_hi": "धन्यवाद / शुक्रिया",
        "spoken_phrase": "Thank you very much!", "phrase_hi": "आपका बहुत-बहुत धन्यवाद!",
        "action": "SPEECH_ASSIST", "led_glyph": "HEART"
    },
    {
        "id": 5, "name": "yes",
        "label": "Yes", "label_hi": "हाँ / स्वीकार",
        "spoken_phrase": "Yes, affirmative.", "phrase_hi": "हाँ, बिल्कुल।",
        "action": "SPEECH_ASSIST", "led_glyph": "CHECKMARK"
    },
    {
        "id": 6, "name": "no",
        "label": "No", "label_hi": "नहीं / मना",
        "spoken_phrase": "No, thank you.", "phrase_hi": "नहीं, धन्यवाद।",
        "action": "SPEECH_ASSIST", "led_glyph": "CROSS"
    },
    {
        "id": 7, "name": "food",
        "label": "Food Please", "label_hi": "खाना / भोजन दीजिए",
        "spoken_phrase": "I am hungry, please bring me some food.", "phrase_hi": "मुझे भूख लगी है, कृपया खाना लाइए।",
        "action": "SPEECH_ASSIST", "led_glyph": "CHECKMARK"
    },
    {
        "id": 8, "name": "medicine",
        "label": "Medicine Doctor", "label_hi": "दवाई / डॉक्टर सहायता",
        "spoken_phrase": "I need my medicine or doctor assistance.", "phrase_hi": "मुझे मेरी दवाई और डॉक्टर की आवश्यकता है।",
        "action": "SPEECH_ASSIST", "led_glyph": "CHECKMARK"
    },
    {
        "id": 9, "name": "pain",
        "label": "Severe Pain", "label_hi": "तेज दर्द हो रहा है",
        "spoken_phrase": "I am experiencing severe pain, please help!", "phrase_hi": "मुझे बहुत तेज दर्द हो रहा है, कृपया मदद कीजिए!",
        "action": "SPEECH_ASSIST", "led_glyph": "SOS_STROBE"
    },
    {
        "id": 10, "name": "fan_on",
        "label": "Turn On Fan", "label_hi": "पंखा / AC चालू करें",
        "spoken_phrase": "Please turn on the fan or air conditioning.", "phrase_hi": "कृपया पंखा या एसी चालू कर दीजिए।",
        "action": "RELAY_CH2_ON", "led_glyph": "CHECKMARK"
    },
    {
        "id": 11, "name": "fan_off",
        "label": "Turn Off Fan", "label_hi": "पंखा / AC बंद करें",
        "spoken_phrase": "Please turn off the fan or air conditioning.", "phrase_hi": "कृपया पंखा या एसी बंद कर दीजिए।",
        "action": "RELAY_CH2_OFF", "led_glyph": "CHECKMARK"
    },
    {
        "id": 12, "name": "washroom",
        "label": "Washroom Assistance", "label_hi": "शौचालय सहायता चाहिए",
        "spoken_phrase": "I need assistance to go to the washroom.", "phrase_hi": "मुझे शौचालय जाने के लिए सहायता चाहिए।",
        "action": "SPEECH_ASSIST", "led_glyph": "CHECKMARK"
    },
    {
        "id": 13, "name": "call_family",
        "label": "Call Family Caregiver", "label_hi": "परिवार को कॉल करें",
        "spoken_phrase": "Please call my family or caregiver.", "phrase_hi": "कृपया मेरे परिवार या देखभालकर्ता को फोन करें।",
        "action": "SPEECH_ASSIST", "led_glyph": "CHECKMARK"
    },
    {
        "id": 14, "name": "sleep",
        "label": "Sleep Rest", "label_hi": "सोना / आराम करना है",
        "spoken_phrase": "I want to rest and sleep now, thank you.", "phrase_hi": "मैं अब आराम करना चाहता हूँ, धन्यवाद।",
        "action": "SPEECH_ASSIST", "led_glyph": "CHECKMARK"
    }
]


def update_labels_file():
    """Syncs labels.json with all gestures in the 3D library."""
    entries = list_library_gestures()
    labels_dict = {
        "metadata": {
            "description": "NeuroSign-HMI 3D Gesture & Bilingual Voice Dictionary",
            "version": "2.1",
            "total_gestures": len(entries),
            "bilingual_support": ["English", "Hindi"]
        },
        "gestures": {}
    }
    for e in entries:
        labels_dict["gestures"][str(e["id"])] = {
            "name": e["name"],
            "label": e["label"],
            "label_hi": e.get("label_hi", ""),
            "spoken_phrase": e["spoken_phrase"],
            "phrase_hi": e.get("phrase_hi", ""),
            "action": e.get("action", "SPEECH_ASSIST"),
            "led_glyph": e.get("led_glyph", "NONE")
        }
        
    with open(LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(labels_dict, f, indent=2, ensure_ascii=False)
    print(f"[3D LIBRARY] Updated bilingual labels dictionary: {LABELS_PATH}")


def list_library_gestures():
    """Lists all gestures currently saved in the 3D library."""
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    files = sorted([f for f in os.listdir(LIBRARY_DIR) if f.endswith(".json")], key=lambda x: int(x.split('_')[0]) if x.split('_')[0].isdigit() else 999)
    entries = []
    for f in files:
        fpath = os.path.join(LIBRARY_DIR, f)
        try:
            with open(fpath, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                # Inject default Hindi phrases if missing
                for d in DEFAULT_GESTURES_15:
                    if d["id"] == data.get("id"):
                        data["label_hi"] = data.get("label_hi", d["label_hi"])
                        data["phrase_hi"] = data.get("phrase_hi", d["phrase_hi"])
                entries.append(data)
        except Exception as err:
            print(f"Error reading {f}: {err}")
    return entries


def print_dictionary_summary():
    """Prints a beautiful formatted summary of the 3D Gesture Voice Dictionary."""
    entries = list_library_gestures()
    print("=" * 105)
    print("           NeuroSign-HMI: 3D Gesture & Bilingual Voice Dictionary (English + Hindi)")
    print("=" * 105)
    print(f"{'ID':<3} | {'English Label':<24} | {'Hindi Label (हिंदी)':<22} | {'Spoken Phrase':<40}")
    print("-" * 105)
    for e in entries:
        print(f"{e['id']:<3} | {e['label']:<24} | {e.get('label_hi',''):<22} | 🔊 \"{e['spoken_phrase']}\"")
    print("=" * 105)
    print(f"Total Gestures in Bilingual Dictionary: {len(entries)}\n")


def train_from_library(epochs: int = 25, samples_per_gesture: int = 300):
    """Compiles all gestures from 3D library, generates 3D augmentations, and trains model."""
    entries = list_library_gestures()
    if not entries:
        print("[ERROR] 3D Gesture Library is empty.")
        return

    from synthetic_dataset_generator import augment_sequence

    print(f"\n[AUTO-TRAIN] Compiling {len(entries)} gestures from 3D library...")
    all_X = []
    all_y = []

    for entry in entries:
        gid = entry["id"]
        samples = entry["samples"]
        print(f"  Processing '{entry['label']}' ({len(samples)} base clips) -> generating {samples_per_gesture} 3D variations...")

        variations_per_sample = max(1, samples_per_gesture // len(samples))
        for sample in samples:
            base_clip = np.array(sample, dtype=np.float32)
            aug_list = augment_sequence(base_clip, num_variations=variations_per_sample)
            for clip in aug_list:
                all_X.append(clip)
                all_y.append(gid)

    X = np.array(all_X, dtype=np.float32)
    y = np.array(all_y, dtype=np.int32)

    # Save to gestures_dataset.npz
    np.savez_compressed(DATASET_PATH, X=X, y=y)
    print(f"[AUTO-TRAIN] Saved compiled dataset: {DATASET_PATH} (Shape: {X.shape})")

    # Update labels.json
    update_labels_file()

    # Train model
    from train_lstm import main as train_main
    print("\n[AUTO-TRAIN] Launching 1D-LSTM Neural Training & Quantization...")
    sys.argv = ["train_lstm.py", "--epochs", str(epochs), "--batch_size", "32"]
    train_main()
    print("\n[AUTO-TRAIN] *** COMPLETE! Model trained and ready for live execution! ***\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NeuroSign-HMI: 3D Gesture & Bilingual Voice Dictionary Studio")
    parser.add_argument("--list", action="store_true", help="List all gestures in the 3D voice dictionary")
    parser.add_argument("--sync", action="store_true", help="Sync bilingual Hindi/English metadata to labels.json")
    parser.add_argument("--train", action="store_true", help="Auto-train model on all library gestures")
    parser.add_argument("--epochs", type=int, default=20, help="Training epochs")

    args = parser.parse_args()

    if args.sync:
        update_labels_file()
    elif args.train:
        train_from_library(epochs=args.epochs)
    else:
        update_labels_file()
        print_dictionary_summary()
