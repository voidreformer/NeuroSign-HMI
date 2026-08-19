"""
NeuroSign-HMI: 3D Synthetic Dataset Generator
Generates full 3D hand gesture sequences (30 frames x 21 joints x 3 coords = 63 features)
for all 7 vocabulary classes using kinematics, trajectories, and parametric 3D augmentations.
"""

import numpy as np
import os
import json

# Joint Indices Reference
WRIST = 0
THUMB = [1, 2, 3, 4]
INDEX = [5, 6, 7, 8]
MIDDLE = [9, 10, 11, 12]
RING = [13, 14, 15, 16]
PINKY = [17, 18, 19, 20]

def get_base_hand_rest():
    """Generates standard MediaPipe 21-joint 3D rest hand pose."""
    pts = np.zeros((21, 3), dtype=np.float32)
    # Wrist at origin
    pts[0] = [0.0, 0.0, 0.0]

    # Thumb
    pts[1] = [-0.03, 0.02, 0.01]
    pts[2] = [-0.05, 0.04, 0.02]
    pts[3] = [-0.06, 0.06, 0.03]
    pts[4] = [-0.07, 0.08, 0.04]

    # Index
    pts[5] = [-0.03, 0.08, 0.0]
    pts[6] = [-0.03, 0.12, 0.0]
    pts[7] = [-0.03, 0.15, 0.0]
    pts[8] = [-0.03, 0.18, 0.0]

    # Middle
    pts[9] = [0.0, 0.085, 0.0]
    pts[10] = [0.0, 0.13, 0.0]
    pts[11] = [0.0, 0.165, 0.0]
    pts[12] = [0.0, 0.20, 0.0]

    # Ring
    pts[13] = [0.028, 0.08, 0.0]
    pts[14] = [0.028, 0.12, 0.0]
    pts[15] = [0.028, 0.155, 0.0]
    pts[16] = [0.028, 0.185, 0.0]

    # Pinky
    pts[17] = [0.052, 0.07, 0.0]
    pts[18] = [0.052, 0.10, 0.0]
    pts[19] = [0.052, 0.125, 0.0]
    pts[20] = [0.052, 0.15, 0.0]

    return pts

def curl_finger(pts, joint_indices, curl_amount):
    """Curls a finger inwards towards the palm."""
    res = pts.copy()
    base_mcp = res[joint_indices[0]]
    for idx in joint_indices[1:]:
        vec = res[idx] - base_mcp
        # Rotate vector down towards palm (Y decreases, Z increases)
        theta = curl_amount * np.pi * 0.5
        new_y = vec[1] * np.cos(theta) - vec[2] * np.sin(theta)
        new_z = vec[1] * np.sin(theta) + vec[2] * np.cos(theta)
        res[idx] = base_mcp + np.array([vec[0], new_y * 0.6, new_z])
    return res

def generate_gesture_trajectory(class_idx, num_frames=30):
    """
    Generates a realistic 30-frame sequence for each of the 7 gesture classes:
    0: Emergency - Need Help (Rapid waving / open-close hand alarm motion)
    1: Turn On Room Light (Fist opening upwards into bright expanded palm)
    2: Turn Off Room Light (Open hand descending & curling down into fist)
    3: Water Please (Cupped palm tipping towards mouth / drinking trajectory)
    4: Thank You (Flat open palm extending forward and slightly bowing)
    5: Yes (Fist nodding up and down vertically like affirmative gesture)
    6: No (Index finger waving horizontally left and right)
    """
    frames = []
    base = get_base_hand_rest()
    t = np.linspace(0, 1, num_frames)

    for i in range(num_frames):
        alpha = t[i]
        hand = base.copy()

        if class_idx == 0:  # Emergency - Rapid waving & pulsing
            wave_x = np.sin(alpha * 4 * np.pi) * 0.06
            wave_y = np.sin(alpha * 2 * np.pi) * 0.03
            curl = (np.sin(alpha * 4 * np.pi) + 1.0) * 0.4
            hand = curl_finger(hand, INDEX, curl)
            hand = curl_finger(hand, MIDDLE, curl)
            hand = curl_finger(hand, RING, curl)
            hand = curl_finger(hand, PINKY, curl)
            hand[:, 0] += wave_x
            hand[:, 1] += wave_y

        elif class_idx == 1:  # Turn On Room Light - Fist opening & moving up
            open_progress = alpha
            # Start closed, open fully
            curl = 1.0 - open_progress
            hand = curl_finger(hand, THUMB, curl)
            hand = curl_finger(hand, INDEX, curl)
            hand = curl_finger(hand, MIDDLE, curl)
            hand = curl_finger(hand, RING, curl)
            hand = curl_finger(hand, PINKY, curl)
            hand[:, 1] += open_progress * 0.08  # Ascending

        elif class_idx == 2:  # Turn Off Room Light - Open hand closing & moving down
            close_progress = alpha
            curl = close_progress
            hand = curl_finger(hand, THUMB, curl)
            hand = curl_finger(hand, INDEX, curl)
            hand = curl_finger(hand, MIDDLE, curl)
            hand = curl_finger(hand, RING, curl)
            hand = curl_finger(hand, PINKY, curl)
            hand[:, 1] -= close_progress * 0.08  # Descending

        elif class_idx == 3:  # Water Please - Cupped hand tipping
            hand = curl_finger(hand, THUMB, 0.4)
            hand = curl_finger(hand, INDEX, 0.3)
            hand = curl_finger(hand, MIDDLE, 0.3)
            hand = curl_finger(hand, RING, 0.3)
            hand = curl_finger(hand, PINKY, 0.3)
            # Tip back and forth (drinking motion)
            tilt_z = np.sin(alpha * 2 * np.pi) * 0.04
            hand[:, 2] += tilt_z
            hand[:, 1] += np.sin(alpha * 2 * np.pi) * 0.03

        elif class_idx == 4:  # Thank You - Flat hand pushing forward
            push_z = np.sin(alpha * np.pi) * 0.08
            hand[:, 2] += push_z
            hand[:, 1] -= alpha * 0.03

        elif class_idx == 5:  # Yes - Closed fist nodding vertically
            hand = curl_finger(hand, THUMB, 0.9)
            hand = curl_finger(hand, INDEX, 0.9)
            hand = curl_finger(hand, MIDDLE, 0.9)
            hand = curl_finger(hand, RING, 0.9)
            hand = curl_finger(hand, PINKY, 0.9)
            nod_y = np.sin(alpha * 3 * np.pi) * 0.05
            hand[:, 1] += nod_y

        elif class_idx == 6:  # No - Index finger wagging left and right
            hand = curl_finger(hand, THUMB, 0.9)
            hand = curl_finger(hand, MIDDLE, 0.9)
            hand = curl_finger(hand, RING, 0.9)
            hand = curl_finger(hand, PINKY, 0.9)
            # Index extended and wagging
            wag_x = np.sin(alpha * 3 * np.pi) * 0.04
            hand[INDEX, 0] += wag_x

        # Normalize relative to wrist
        wrist = hand[0:1]
        norm = (hand - wrist).flatten()
        frames.append(norm)

    return np.array(frames, dtype=np.float32)

def augment_sequence(seq_30x63, num_variations=75):
    """Augments single sequence into multiple spatial 3D variations."""
    augmented = [seq_30x63]
    seq = seq_30x63.reshape(30, 21, 3)

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

        aug_seq = np.zeros_like(seq)
        for f in range(30):
            for j in range(21):
                aug_seq[f, j] = (R @ (seq[f, j] * scale)) + noise[f, j]

        wrist = aug_seq[:, 0:1, :]
        norm_seq = (aug_seq - wrist).reshape(30, 63).astype(np.float32)
        augmented.append(norm_seq)

    return np.array(augmented, dtype=np.float32)

def build_full_dataset(samples_per_class=300):
    """Builds complete balanced 7-class synthetic dataset."""
    X_all, y_all = [], []

    for c in range(7):
        print(f"[GENERATING] Class {c}...")
        # Generate base trajectories with slight variations
        num_bases = samples_per_class // 75
        for _ in range(num_bases):
            base_seq = generate_gesture_trajectory(c, num_frames=30)
            augmented = augment_sequence(base_seq, num_variations=74)
            for s in augmented:
                X_all.append(s)
                y_all.append(c)

    X_arr = np.array(X_all, dtype=np.float32)
    y_arr = np.array(y_all, dtype=np.int32)

    # Shuffle dataset
    indices = np.arange(len(X_arr))
    np.random.seed(42)
    np.random.shuffle(indices)

    X_arr = X_arr[indices]
    y_arr = y_arr[indices]

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gestures_dataset.npz")
    np.savez(out_path, X=X_arr, y=y_arr)
    print(f"\n[COMPLETE] Generated {len(X_arr)} samples across 7 classes -> {out_path}")
    return out_path

if __name__ == "__main__":
    build_full_dataset(samples_per_class=350)
