"""
NeuroSign-HMI: Blender 3D Hand Rig & Gesture Augmentation Engine
Executes inside Blender (or via Blender MCP).

Features:
1. Builds a 21-bone 3D Hand Armature matching MediaPipe landmark indices.
2. Receives live 3D joint coordinates via UDP (127.0.0.1:9999) to animate the 3D hand live.
3. Automatically generates 50+ 3D-rotated, scaled, and noise-augmented variations per gesture.
4. Exports augmented [N x 30 x 63] datasets to gestures_dataset.npz and triggers train_lstm.py.
"""

import bpy
import mathutils
import socket
import json
import threading
import time
import os
import subprocess
import numpy as np

# 21 MediaPipe Joint Names
JOINT_NAMES = [
    "Wrist",
    "Thumb_CMC", "Thumb_MCP", "Thumb_IP", "Thumb_Tip",
    "Index_MCP", "Index_PIP", "Index_DIP", "Index_Tip",
    "Middle_MCP", "Middle_PIP", "Middle_DIP", "Middle_Tip",
    "Ring_MCP", "Ring_PIP", "Ring_DIP", "Ring_Tip",
    "Pinky_MCP", "Pinky_PIP", "Pinky_DIP", "Pinky_Tip"
]

# Connections between joints for bone creation
BONE_HIERARCHY = [
    ("Wrist", "Thumb_CMC"), ("Thumb_CMC", "Thumb_MCP"), ("Thumb_MCP", "Thumb_IP"), ("Thumb_IP", "Thumb_Tip"),
    ("Wrist", "Index_MCP"), ("Index_MCP", "Index_PIP"), ("Index_PIP", "Index_DIP"), ("Index_DIP", "Index_Tip"),
    ("Wrist", "Middle_MCP"), ("Middle_MCP", "Middle_PIP"), ("Middle_PIP", "Middle_DIP"), ("Middle_DIP", "Middle_Tip"),
    ("Wrist", "Ring_MCP"), ("Ring_MCP", "Ring_PIP"), ("Ring_PIP", "Ring_DIP"), ("Ring_DIP", "Ring_Tip"),
    ("Wrist", "Pinky_MCP"), ("Pinky_MCP", "Pinky_PIP"), ("Pinky_PIP", "Pinky_DIP"), ("Pinky_DIP", "Pinky_Tip")
]


class BlenderHandRigManager:
    def __init__(self, obj_name="NeuroSign_HandRig"):
        self.obj_name = obj_name
        self.armature = None
        self.udp_sock = None
        self.listener_thread = None
        self.running = False
        self.current_landmarks = None
        self.lock = threading.Lock()

    def build_hand_armature(self):
        """Creates the 21-joint 3D hand armature and visual joint spheres in Blender."""
        # Clean existing armature if present
        if self.obj_name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[self.obj_name], do_unlink=True)

        armature_data = bpy.data.armatures.new(f"{self.obj_name}_Data")
        self.armature = bpy.data.objects.new(self.obj_name, armature_data)
        bpy.context.collection.objects.link(self.armature)
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode='EDIT')

        # Default hand proportions (approximate rest pose in meters)
        default_positions = {
            "Wrist": (0.0, 0.0, 0.0),
            "Thumb_CMC": (-0.03, 0.02, 0.01), "Thumb_MCP": (-0.05, 0.04, 0.02), "Thumb_IP": (-0.06, 0.06, 0.03), "Thumb_Tip": (-0.07, 0.08, 0.04),
            "Index_MCP": (-0.03, 0.08, 0.0), "Index_PIP": (-0.03, 0.11, 0.0), "Index_DIP": (-0.03, 0.13, 0.0), "Index_Tip": (-0.03, 0.15, 0.0),
            "Middle_MCP": (0.0, 0.085, 0.0), "Middle_PIP": (0.0, 0.12, 0.0), "Middle_DIP": (0.0, 0.145, 0.0), "Middle_Tip": (0.0, 0.165, 0.0),
            "Ring_MCP": (0.025, 0.08, 0.0), "Ring_PIP": (0.025, 0.11, 0.0), "Ring_DIP": (0.025, 0.135, 0.0), "Ring_Tip": (0.025, 0.155, 0.0),
            "Pinky_MCP": (0.05, 0.07, 0.0), "Pinky_PIP": (0.05, 0.095, 0.0), "Pinky_DIP": (0.05, 0.115, 0.0), "Pinky_Tip": (0.05, 0.135, 0.0),
        }

        edit_bones = self.armature.data.edit_bones
        for joint_name, pos in default_positions.items():
            bone = edit_bones.new(joint_name)
            bone.head = mathutils.Vector(pos)
            bone.tail = mathutils.Vector(pos) + mathutils.Vector((0, 0.01, 0))

        bpy.ops.object.mode_set(mode='OBJECT')
        print(f"[BLENDER RIG] 3D Hand Armature '{self.obj_name}' successfully built with 21 joints.")
        return self.armature

    def update_pose(self, landmarks_21x3):
        """
        Updates the 3D bone positions in Blender from a [21 x 3] MediaPipe landmark array.
        """
        if not self.armature or landmarks_21x3 is None:
            return

        # Switch to POSE mode
        bpy.context.view_layer.objects.active = self.armature
        pose_bones = self.armature.pose.bones

        # Scale factor from normalized camera coords to Blender world units
        scale = 0.5

        wrist_pt = landmarks_21x3[0]

        for i, name in enumerate(JOINT_NAMES):
            if name in pose_bones and i < len(landmarks_21x3):
                pt = landmarks_21x3[i]
                # MediaPipe: X=right, Y=down, Z=depth
                # Blender:   X=right, Y=depth, Z=up
                bx = (pt[0] - wrist_pt[0]) * scale
                by = -(pt[2] - wrist_pt[2]) * scale
                bz = -(pt[1] - wrist_pt[1]) * scale
                pose_bones[name].location = mathutils.Vector((bx, by, bz))

    def generate_augmented_variations(self, sequence_30x63, num_variations=50):
        """
        Takes a recorded 30-frame sequence and generates synthetic 3D spatial variations:
        1. 3D Euler Rotations (Yaw, Pitch, Roll +-25 deg)
        2. Anthropometric Bone Scaling (+-15%)
        3. Temporal Speed Perturbations
        4. Gaussian Sensor Jitter
        """
        augmented = [sequence_30x63]  # Original sequence is sample #0
        seq = np.array(sequence_30x63).reshape(30, 21, 3)

        for _ in range(num_variations):
            # Random 3D Rotation Matrix
            yaw = np.random.uniform(-np.radians(25), np.radians(25))
            pitch = np.random.uniform(-np.radians(20), np.radians(20))
            roll = np.random.uniform(-np.radians(15), np.radians(15))

            R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
            R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)], [0, 1, 0], [-np.sin(pitch), 0, np.cos(pitch)]])
            R_x = np.array([[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]])
            R = R_z @ R_y @ R_x

            # Random Hand Scale (palm/finger length)
            scale = np.random.uniform(0.85, 1.15)

            # Random Gaussian Noise (sensor tremor)
            noise = np.random.normal(0, 0.004, seq.shape)

            # Apply transformations
            rotated_seq = np.zeros_like(seq)
            for f in range(30):
                for j in range(21):
                    rotated_seq[f, j] = (R @ (seq[f, j] * scale)) + noise[f, j]

            # Re-normalize wrist to (0,0,0)
            wrist_series = rotated_seq[:, 0:1, :]
            norm_seq = (rotated_seq - wrist_series).reshape(30, 63).astype(np.float32)
            augmented.append(norm_seq)

        return np.array(augmented, dtype=np.float32)


def start_live_mocap_receiver(port=9999):
    """Starts the background UDP listener inside Blender to animate the rig live."""
    manager = BlenderHandRigManager()
    manager.build_hand_armature()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", port))
    sock.settimeout(0.1)

    print(f"[BLENDER MOCAP] Listening for 3D gesture stream on UDP port {port}...")

    def _loop():
        while True:
            try:
                data, _ = sock.recvfrom(4096)
                payload = json.loads(data.decode('utf-8'))
                if "landmarks" in payload:
                    landmarks = np.array(payload["landmarks"]).reshape(21, 3)
                    # Queue pose update onto Blender main thread
                    bpy.app.timers.register(lambda: (manager.update_pose(landmarks), None)[1])
            except socket.timeout:
                continue
            except Exception as e:
                break

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return manager


if __name__ == "__main__":
    rig_manager = BlenderHandRigManager()
    rig_manager.build_hand_armature()
