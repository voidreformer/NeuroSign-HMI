"""
NeuroSign-HMI: Blender 3D Gesture Generator & Library Exporter (15 Gestures)
Runs inside Blender to generate rigged, keyframed 3D hand animations for all 15 gesture classes,
exports standard .blend animation project files, and extracts wrist-invariant 3D coordinates into gesture_library_3d/.
"""

import os
import sys
import json
import math
import bpy
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIBRARY_DIR = os.path.join(SCRIPT_DIR, "gesture_library_3d")
os.makedirs(LIBRARY_DIR, exist_ok=True)

# 21 MediaPipe Standard Joint Names & Proportions
JOINT_NAMES = [
    "Wrist",
    "Thumb_CMC", "Thumb_MCP", "Thumb_IP", "Thumb_Tip",
    "Index_MCP", "Index_PIP", "Index_DIP", "Index_Tip",
    "Middle_MCP", "Middle_PIP", "Middle_DIP", "Middle_Tip",
    "Ring_MCP", "Ring_PIP", "Ring_DIP", "Ring_Tip",
    "Pinky_MCP", "Pinky_PIP", "Pinky_DIP", "Pinky_Tip"
]

DEFAULT_REST_POSITIONS = {
    "Wrist": (0.0, 0.0, 0.0),
    "Thumb_CMC": (-0.03, 0.02, 0.01), "Thumb_MCP": (-0.05, 0.04, 0.02), "Thumb_IP": (-0.06, 0.06, 0.03), "Thumb_Tip": (-0.07, 0.08, 0.04),
    "Index_MCP": (-0.03, 0.08, 0.0), "Index_PIP": (-0.03, 0.12, 0.0), "Index_DIP": (-0.03, 0.15, 0.0), "Index_Tip": (-0.03, 0.18, 0.0),
    "Middle_MCP": (0.0, 0.085, 0.0), "Middle_PIP": (0.0, 0.13, 0.0), "Middle_DIP": (0.0, 0.165, 0.0), "Middle_Tip": (0.0, 0.20, 0.0),
    "Ring_MCP": (0.028, 0.08, 0.0), "Ring_PIP": (0.028, 0.12, 0.0), "Ring_DIP": (0.028, 0.155, 0.0), "Ring_Tip": (0.028, 0.185, 0.0),
    "Pinky_MCP": (0.052, 0.07, 0.0), "Pinky_PIP": (0.052, 0.10, 0.0), "Pinky_DIP": (0.052, 0.125, 0.0), "Pinky_Tip": (0.052, 0.15, 0.0),
}


def build_3d_hand_scene():
    """Cleans scene and builds 21 visual 3D joint spheres with color materials."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

    mat = bpy.data.materials.new(name="HandJointMat")
    joint_objects = {}
    for name, pos in DEFAULT_REST_POSITIONS.items():
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=pos)
        sphere = bpy.context.active_object
        sphere.name = f"Joint_{name}"
        sphere.data.materials.append(mat)
        joint_objects[name] = sphere

    return joint_objects


def curl_point(base_mcp, pt, curl_factor):
    """Curls a 3D finger point towards the palm."""
    vec = np.array(pt) - np.array(base_mcp)
    theta = curl_factor * math.pi * 0.5
    new_y = vec[1] * math.cos(theta) - vec[2] * math.sin(theta)
    new_z = vec[1] * math.sin(theta) + vec[2] * math.cos(theta)
    return (base_mcp[0] + vec[0], base_mcp[1] + new_y * 0.6, base_mcp[2] + new_z)


def animate_and_export_gesture(gid: int, name: str, label: str, spoken_phrase: str, action: str):
    """Calculates realistic 3D joint keyframes, keyframes them in Blender, and exports .blend and .json."""
    joint_objects = build_3d_hand_scene()
    num_frames = 30
    trajectory_3d_frames = []

    for t in range(num_frames):
        phase = t / (num_frames - 1)
        bpy.context.scene.frame_set(t + 1)
        frame_raw_pts = {}

        # 1. Base Wrist
        wrist_x, wrist_y, wrist_z = 0.0, 0.0, 0.0

        if gid == 0:  # Emergency: Rapid hand wave left/right
            wrist_x += math.sin(phase * 4 * math.pi) * 0.06
        elif gid == 1:  # Light On: Hand rises up
            wrist_y += phase * 0.05
        elif gid == 2:  # Light Off: Hand descends
            wrist_y -= phase * 0.05
        elif gid == 3:  # Water: Wrist tilts up to mouth
            wrist_y += math.sin(phase * math.pi) * 0.04
            wrist_z += math.sin(phase * math.pi) * 0.05
        elif gid == 4:  # Thank You: Wrist pushes forward
            wrist_z += math.sin(phase * math.pi) * 0.08
        elif gid == 7:  # Food: Hand moves towards mouth
            wrist_y += math.sin(phase * 2 * math.pi) * 0.05
            wrist_z += math.sin(phase * 2 * math.pi) * 0.06
        elif gid == 9:  # Pain: Trembling hand
            wrist_x += (np.random.uniform(-0.015, 0.015))
            wrist_y += (np.random.uniform(-0.015, 0.015))
        elif gid == 10: # Fan On: Circular wrist spin
            wrist_x += math.cos(phase * 3 * math.pi) * 0.04
            wrist_y += math.sin(phase * 3 * math.pi) * 0.04
        elif gid == 12: # Washroom: Side shake
            wrist_x += math.sin(phase * 4 * math.pi) * 0.03
        elif gid == 13: # Call Family: Move hand to ear
            wrist_x += phase * 0.06
            wrist_y += phase * 0.06
        elif gid == 14: # Sleep: Tilt sideways
            wrist_x += math.sin(phase * math.pi) * 0.05
            wrist_y -= math.sin(phase * math.pi) * 0.03

        frame_raw_pts["Wrist"] = (wrist_x, wrist_y, wrist_z)

        # 2. Compute Fingers based on gesture mechanics
        for j_name, base_pos in DEFAULT_REST_POSITIONS.items():
            if j_name == "Wrist":
                continue

            bx, by, bz = base_pos
            x, y, z = bx + wrist_x, by + wrist_y, bz + wrist_z
            finger_group = j_name.split("_")[0]

            if gid == 0:  # Emergency: Open palm waving
                x += math.sin(phase * 4 * math.pi) * 0.03

            elif gid == 1:  # Light On: Starts curled, opens fully
                open_factor = phase
                curl = 1.0 - open_factor
                mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP" if not "CMC" in j_name else "Wrist"]
                if "Tip" in j_name or "DIP" in j_name or "PIP" in j_name or "IP" in j_name:
                    curled = curl_point(mcp, (bx, by, bz), curl * 0.8)
                    x, y, z = curled[0] + wrist_x, curled[1] + wrist_y, curled[2] + wrist_z

            elif gid == 2:  # Light Off: Starts open, curls into closed fist
                close_factor = phase
                curl = close_factor
                mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP" if not "CMC" in j_name else "Wrist"]
                if "Tip" in j_name or "DIP" in j_name or "PIP" in j_name or "IP" in j_name:
                    curled = curl_point(mcp, (bx, by, bz), curl * 0.85)
                    x, y, z = curled[0] + wrist_x, curled[1] + wrist_y, curled[2] + wrist_z

            elif gid == 3:  # Water: Drinking cup tilt
                tilt = math.sin(phase * math.pi) * 0.7
                ry = by * math.cos(tilt) - bz * math.sin(tilt)
                rz = by * math.sin(tilt) + bz * math.cos(tilt)
                x = bx + wrist_x
                y = ry + wrist_y
                z = rz + wrist_z

            elif gid == 4:  # Thank you: Flat hand pushing forward
                push = math.sin(phase * math.pi) * 0.06
                z += push

            elif gid == 5:  # Yes: Closed fist nodding up and down
                mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP" if not "CMC" in j_name else "Wrist"]
                curled = curl_point(mcp, (bx, by, bz), 0.9)
                nod = math.sin(phase * 3 * math.pi) * 0.04
                x, y, z = curled[0] + wrist_x, curled[1] + wrist_y + nod, curled[2] + wrist_z

            elif gid == 6:  # No: Middle/Ring/Pinky curled, Index wagging
                if "Middle" in j_name or "Ring" in j_name or "Pinky" in j_name:
                    mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP"]
                    curled = curl_point(mcp, (bx, by, bz), 0.9)
                    x, y, z = curled[0] + wrist_x, curled[1] + wrist_y, curled[2] + wrist_z
                elif "Index" in j_name:
                    wag = math.sin(phase * 3 * math.pi) * 0.04
                    x += wag

            elif gid == 7:  # Food: All finger tips pinched together
                mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP" if not "CMC" in j_name else "Wrist"]
                pinch_target = (0.0, 0.11, 0.03)
                if "Tip" in j_name:
                    curled = np.array(base_pos) * 0.4 + np.array(pinch_target) * 0.6
                    x, y, z = curled[0] + wrist_x, curled[1] + wrist_y, curled[2] + wrist_z

            elif gid == 8:  # Medicine: Index & Thumb holding pill
                if "Ring" in j_name or "Pinky" in j_name or "Middle" in j_name:
                    mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP"]
                    curled = curl_point(mcp, (bx, by, bz), 0.85)
                    x, y, z = curled[0] + wrist_x, curled[1] + wrist_y, curled[2] + wrist_z
                elif "Thumb" in j_name or "Index" in j_name:
                    # Pinch pill together
                    x = bx * 0.6 + wrist_x
                    y = by * 0.8 + wrist_y + math.sin(phase * 2 * math.pi) * 0.02

            elif gid == 9:  # Pain: Clutched fist shaking with high tremor
                mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP" if not "CMC" in j_name else "Wrist"]
                curled = curl_point(mcp, (bx, by, bz), 0.95)
                jitter = np.random.uniform(-0.008, 0.008)
                x, y, z = curled[0] + wrist_x + jitter, curled[1] + wrist_y + jitter, curled[2] + wrist_z

            elif gid == 10: # Fan On: Index and Middle extended, spinning
                if "Ring" in j_name or "Pinky" in j_name:
                    mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP"]
                    curled = curl_point(mcp, (bx, by, bz), 0.9)
                    x, y, z = curled[0] + wrist_x, curled[1] + wrist_y, curled[2] + wrist_z
                elif "Index" in j_name or "Middle" in j_name:
                    rot = phase * 3 * math.pi
                    rx = bx * math.cos(rot) - bz * math.sin(rot)
                    x = rx + wrist_x

            elif gid == 11: # Fan Off: Extended fingers slowing and flattening
                if "Ring" in j_name or "Pinky" in j_name:
                    mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP"]
                    curled = curl_point(mcp, (bx, by, bz), 0.9)
                    x, y, z = curled[0] + wrist_x, curled[1] + wrist_y, curled[2] + wrist_z
                else:
                    # Stop motion
                    stop_factor = 1.0 - phase
                    x = bx + math.sin(stop_factor * math.pi) * 0.02 + wrist_x

            elif gid == 12: # Washroom: Thumb tucked, shaking
                mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP" if not "CMC" in j_name else "Wrist"]
                curled = curl_point(mcp, (bx, by, bz), 0.8)
                x, y, z = curled[0] + wrist_x, curled[1] + wrist_y, curled[2] + wrist_z

            elif gid == 13: # Call Family: Thumb & Pinky extended (Phone sign), middle 3 curled
                if "Index" in j_name or "Middle" in j_name or "Ring" in j_name:
                    mcp = DEFAULT_REST_POSITIONS[finger_group + "_MCP"]
                    curled = curl_point(mcp, (bx, by, bz), 0.95)
                    x, y, z = curled[0] + wrist_x, curled[1] + wrist_y, curled[2] + wrist_z
                elif "Thumb" in j_name or "Pinky" in j_name:
                    x = bx * 1.2 + wrist_x
                    y = by * 1.1 + wrist_y

            elif gid == 14: # Sleep: Flat palm tilted horizontally
                tilt_sleep = phase * 0.6
                rx = bx * math.cos(tilt_sleep) - by * math.sin(tilt_sleep)
                ry = bx * math.sin(tilt_sleep) + by * math.cos(tilt_sleep)
                x = rx + wrist_x
                y = ry + wrist_y

            frame_raw_pts[j_name] = (x, y, z)
            obj = joint_objects[j_name]
            obj.location = (x, y, z)
            obj.keyframe_insert(data_path="location", index=-1)

        # Set wrist keyframe
        joint_objects["Wrist"].location = frame_raw_pts["Wrist"]
        joint_objects["Wrist"].keyframe_insert(data_path="location", index=-1)

        # Normalize 21 landmarks relative to wrist
        w_pt = np.array(frame_raw_pts["Wrist"])
        norm_frame = []
        for j_name in JOINT_NAMES:
            pt = np.array(frame_raw_pts[j_name])
            norm_frame.extend((pt - w_pt).tolist())

        trajectory_3d_frames.append(norm_frame)

    # Set frame range in Blender
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = num_frames

    # Save Blender Project File (.blend)
    blend_filepath = os.path.join(LIBRARY_DIR, f"{gid}_{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_filepath)

    # Generate 15 augmented 3D trajectory variations
    all_clips = [trajectory_3d_frames]
    for _ in range(14):
        angle_z = np.random.uniform(-0.15, 0.15)
        scale = np.random.uniform(0.90, 1.10)
        c, s = np.cos(angle_z), np.sin(angle_z)
        Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

        aug_clip = []
        for frame in trajectory_3d_frames:
            pts = np.array(frame).reshape(21, 3) * scale
            pts = np.dot(pts, Rz.T)
            aug_clip.append(pts.flatten().tolist())
        all_clips.append(aug_clip)

    # Save 3D Library JSON File
    json_filepath = os.path.join(LIBRARY_DIR, f"{gid}_{name}.json")
    data = {
        "id": gid,
        "name": name,
        "label": label,
        "spoken_phrase": spoken_phrase,
        "action": action,
        "led_glyph": "CHECKMARK",
        "num_frames": num_frames,
        "num_landmarks": 21,
        "sample_count": len(all_clips),
        "blend_file": f"{gid}_{name}.blend",
        "samples": all_clips
    }

    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[BLENDER ENGINE] Exported: '{label}' (ID {gid}) -> Blend: {gid}_{name}.blend & JSON: {gid}_{name}.json")


def main():
    gestures = [
        (0, "emergency", "Emergency - Need Help", "Emergency! I need urgent help immediately!", "EMERGENCY_SMS_ALARM"),
        (1, "light_on", "Turn On Room Light", "Please turn on the room light.", "RELAY_CH1_ON"),
        (2, "light_off", "Turn Off Room Light", "Please turn off the room light.", "RELAY_CH1_OFF"),
        (3, "water", "Water Please", "Could you please give me a glass of water?", "SPEECH_ASSIST"),
        (4, "thanks", "Thank You", "Thank you very much!", "SPEECH_ASSIST"),
        (5, "yes", "Yes", "Yes, affirmative.", "SPEECH_ASSIST"),
        (6, "no", "No", "No, thank you.", "SPEECH_ASSIST"),
        (7, "food", "Food Please", "I am hungry, please bring me some food.", "SPEECH_ASSIST"),
        (8, "medicine", "Medicine Doctor", "I need my medicine or doctor assistance.", "SPEECH_ASSIST"),
        (9, "pain", "Severe Pain", "I am experiencing severe pain, please help!", "SPEECH_ASSIST"),
        (10, "fan_on", "Turn On Fan", "Please turn on the fan or air conditioning.", "RELAY_CH2_ON"),
        (11, "fan_off", "Turn Off Fan", "Please turn off the fan or air conditioning.", "RELAY_CH2_OFF"),
        (12, "washroom", "Washroom Assistance", "I need assistance to go to the washroom.", "SPEECH_ASSIST"),
        (13, "call_family", "Call Family Caregiver", "Please call my family or caregiver.", "SPEECH_ASSIST"),
        (14, "sleep", "Sleep Rest", "I want to rest and sleep now, thank you.", "SPEECH_ASSIST"),
    ]

    print("\n" + "=" * 70)
    print("   Starting Blender 5.2 3D Gesture Hand Generator (15 Gestures)")
    print("=" * 70)

    for gid, name, label, phrase, action in gestures:
        animate_and_export_gesture(gid, name, label, phrase, action)

    print("=" * 70)
    print("   All 15 3D Gestures Rendered and Exported to gesture_library_3d/")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
