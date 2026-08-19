"""
NeuroSign-HMI: Real-Time 3D Gesture Motion Capture & Blender Streamer
Streams live 21-joint MediaPipe coordinates to Blender (UDP 127.0.0.1:9999)
and records 30-frame gesture sequences with automated 3D data augmentation and model retraining.
"""

import cv2
import socket
import json
import time
import sys
import os
import numpy as np
import mediapipe as mp

# Target gesture labels
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
UDP_IP = "127.0.0.1"
UDP_PORT = 9999


def generate_3d_augmentations(sequence_30x63, num_variations=50):
    """Generates synthetic 3D spatial variations (Euler rotations, bone scaling, jitter)."""
    augmented = [sequence_30x63]
    seq = np.array(sequence_30x63).reshape(30, 21, 3)

    for _ in range(num_variations):
        yaw = np.random.uniform(-np.radians(25), np.radians(25))
        pitch = np.random.uniform(-np.radians(20), np.radians(20))
        roll = np.random.uniform(-np.radians(15), np.radians(15))

        R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
        R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)], [0, 1, 0], [-np.sin(pitch), 0, np.cos(pitch)]])
        R_x = np.array([[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]])
        R = R_z @ R_y @ R_x

        scale = np.random.uniform(0.85, 1.15)
        noise = np.random.normal(0, 0.003, seq.shape)

        rotated_seq = np.zeros_like(seq)
        for f in range(30):
            for j in range(21):
                rotated_seq[f, j] = (R @ (seq[f, j] * scale)) + noise[f, j]

        wrist_series = rotated_seq[:, 0:1, :]
        norm_seq = (rotated_seq - wrist_series).reshape(30, 63).astype(np.float32)
        augmented.append(norm_seq)

    return np.array(augmented, dtype=np.float32)


def main():
    print("================================================================")
    print("  NeuroSign-HMI: 3D Gesture Motion Capture & Blender Streamer   ")
    print("  Streaming UDP packets to Blender at 127.0.0.1:9999            ")
    print("================================================================")

    # Initialize UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Initialize MediaPipe Hands
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.6,
        model_complexity=1
    )
    mp_draw = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not access webcam. Check camera index.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)

    dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gestures_dataset.npz")
    existing_X, existing_y = [], []
    if os.path.exists(dataset_path):
        data = np.load(dataset_path)
        existing_X = list(data['X'])
        existing_y = list(data['y'])
        print(f"[DATASET] Loaded existing dataset with {len(existing_X)} sequences.")

    current_class = 0
    recording = False
    recorded_frames = []

    print("\nControls:")
    print("  1 - 7 : Select Gesture Class")
    print("  R     : Record 30-frame sequence (Auto-Augments in 3D & Saves)")
    print("  T     : Train LSTM Model (Runs train_lstm.py)")
    print("  Q     : Quit\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        h, w = frame.shape[:2]
        landmarks_21x3 = None

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style()
            )

            # Extract raw coordinates [21, 3]
            raw_pts = []
            for lm in hand_landmarks.landmark:
                raw_pts.append([lm.x, lm.y, lm.z])
            landmarks_21x3 = np.array(raw_pts, dtype=np.float32)

            # Stream to Blender over UDP in real time
            payload = json.dumps({"landmarks": landmarks_21x3.tolist()})
            try:
                sock.sendto(payload.encode('utf-8'), (UDP_IP, UDP_PORT))
            except Exception:
                pass

            # If recording, compute wrist-relative normalized vector
            if recording:
                wrist = landmarks_21x3[0:1]
                norm_frame = (landmarks_21x3 - wrist).flatten()
                recorded_frames.append(norm_frame)

                if len(recorded_frames) >= WINDOW_SIZE:
                    base_seq = np.array(recorded_frames[:WINDOW_SIZE], dtype=np.float32)
                    # Generate 50 3D synthetic augmentations
                    aug_samples = generate_3d_augmentations(base_seq, num_variations=50)

                    for sample in aug_samples:
                        existing_X.append(sample)
                        existing_y.append(current_class)

                    # Save dataset
                    np.savez(dataset_path, X=np.array(existing_X, dtype=np.float32), y=np.array(existing_y, dtype=np.int32))
                    print(f"Recorded & Augmented: Added 51 samples for '{GESTURE_LABELS[current_class]}'. Total: {len(existing_X)}")
                    recording = False
                    recorded_frames = []

        # UI Overlay
        cv2.rectangle(frame, (0, 0), (w, 100), (20, 20, 25), -1)
        status_text = f"Class [{current_class+1}/7]: {GESTURE_LABELS[current_class]}"
        cv2.putText(frame, status_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 240, 120), 2)

        rec_status = f"RECORDING ({len(recorded_frames)}/{WINDOW_SIZE})..." if recording else "Press 'R' to Record (Auto-Augments in Blender)"
        rec_color = (0, 0, 255) if recording else (200, 220, 240)
        cv2.putText(frame, rec_status, (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.60, rec_color, 2)

        # Connection status
        cv2.putText(frame, "Blender UDP: Active (127.0.0.1:9999)", (350, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 200, 255), 1)
        cv2.putText(frame, f"Dataset Samples: {len(existing_X)}", (350, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 200, 100), 1)

        cv2.imshow("NeuroSign Mocap Studio", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == ord('Q') or key == 27:
            break
        elif ord('1') <= key <= ord('7'):
            current_class = key - ord('1')
            print(f"[SELECTION] Active gesture: {GESTURE_LABELS[current_class]}")
        elif key == ord('r') or key == ord('R'):
            if not recording:
                recording = True
                recorded_frames = []
                print(f"[RECORDING] Started capture for '{GESTURE_LABELS[current_class]}'...")
        elif key == ord('t') or key == ord('T'):
            print("\n[TRAINING] Invoking train_lstm.py...")
            train_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_lstm.py")
            subprocess.run([sys.executable, train_script])

    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    sock.close()
    print("[MOCAP] Studio closed.")


if __name__ == "__main__":
    main()
