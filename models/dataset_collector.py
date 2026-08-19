import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import sys

GESTURE_LABELS = [
    "Emergency - Need Help",
    "Turn On Room Light",
    "Turn Off Room Light",
    "Water Please",
    "Thank You",
    "Yes",
    "No"
]

WINDOW_SIZE = 30
TARGET_FPS = 60
CAMERA_INDEX = 0

def main():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    mp_draw = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Error: Could not open camera index {CAMERA_INDEX}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    dataset_X = []
    dataset_y = []
    samples_per_class = [0] * len(GESTURE_LABELS)
    current_class = 0
    recording = False
    current_sequence = []

    print("Dataset Collector started.")
    print("Controls:")
    print("  1-7 : Select gesture class")
    print("  R   : Start recording a 30-frame sequence for current class")
    print("  S   : Save dataset to gestures_dataset.npz")
    print("  Q   : Quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame")
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        hand_landmarks = None
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style()
            )

            raw_landmarks = np.array(
                [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark],
                dtype=np.float32
            )
            # Subtract wrist (landmark 0) for translation invariance matching landmark_extractor.py
            wrist = raw_landmarks[0:1]
            landmarks_normalized = (raw_landmarks - wrist).flatten()

            if recording:
                current_sequence.append(landmarks_normalized)
                if len(current_sequence) >= WINDOW_SIZE:
                    dataset_X.append(np.array(current_sequence[:WINDOW_SIZE], dtype=np.float32))
                    dataset_y.append(current_class)
                    samples_per_class[current_class] += 1
                    print(f"Recorded sample {samples_per_class[current_class]} for class '{GESTURE_LABELS[current_class]}'")
                    recording = False
                    current_sequence = []

        status_text = f"Class: {current_class+1} - {GESTURE_LABELS[current_class]}"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        rec_text = "RECORDING..." if recording else "Press R to record"
        rec_color = (0, 0, 255) if recording else (255, 255, 255)
        cv2.putText(frame, rec_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, rec_color, 2)

        if recording:
            progress = f"Frames: {len(current_sequence)}/{WINDOW_SIZE}"
            cv2.putText(frame, progress, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        y_offset = 130
        cv2.putText(frame, "Samples per class:", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        y_offset += 20
        for i, (label, count) in enumerate(zip(GESTURE_LABELS, samples_per_class)):
            prefix = "> " if i == current_class else "  "
            text = f"{prefix}{i+1}: {label} - {count}"
            color = (0, 255, 0) if i == current_class else (200, 200, 200)
            cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
            y_offset += 18

        cv2.imshow("Dataset Collector", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord('s') or key == ord('S'):
            if dataset_X:
                X_arr = np.array(dataset_X, dtype=np.float32)
                y_arr = np.array(dataset_y, dtype=np.int32)
                np.savez("gestures_dataset.npz", X=X_arr, y=y_arr)
                print(f"Saved dataset: X shape {X_arr.shape}, y shape {y_arr.shape}")
            else:
                print("No data to save.")
        elif key == ord('r') or key == ord('R'):
            if not recording:
                recording = True
                current_sequence = []
                print(f"Recording started for class '{GESTURE_LABELS[current_class]}'")
        elif ord('1') <= key <= ord('7'):
            current_class = key - ord('1')
            print(f"Selected class: {GESTURE_LABELS[current_class]}")

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    main()