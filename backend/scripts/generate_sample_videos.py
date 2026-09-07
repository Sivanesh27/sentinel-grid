"""
Sample Video Generator for Sentinel Grid.
Generates synthetic border surveillance video clips for Camera 1 (Perimeter) and Camera 2 (Checkpoint).
These clips allow complete end-to-end testing with zero external datasets required.
"""

import os
import cv2
import numpy as np
import math


def generate_perimeter_video(output_path: str, duration_sec: int = 15, fps: int = 15):
    """
    Generates simulated perimeter CCTV video with pedestrians crossing a border fence zone.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (640, 480))

    total_frames = duration_sec * fps
    print(f"[Generator] Creating Perimeter clip: {output_path} ({total_frames} frames)...")

    for f in range(total_frames):
        t = f / float(fps)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Terrain Background (night surveillance)
        frame[0:320, :] = (25, 30, 35)    # Sky / background horizon
        frame[320:480, :] = (35, 45, 50)  # Ground / buffer zone

        # Fence line
        cv2.line(frame, (0, 320), (640, 320), (60, 75, 80), 2)
        for x in range(0, 640, 30):
            cv2.line(frame, (x, 290), (x, 320), (70, 85, 90), 2)
            cv2.line(frame, (x, 290), (x + 30, 320), (50, 65, 70), 1)

        # Person 1 (Primary Inbound Target)
        progress = (f % total_frames) / total_frames
        px = int(220 + 70 * math.sin(t * 0.8))
        py = int(260 + progress * 170)  # Starts outside, crosses fence, enters restricted zone

        # Human rendering (Head, Torso, Limbs with motion)
        leg_swing = int(8 * math.sin(t * 6))
        cv2.circle(frame, (px, py - 38), 12, (200, 210, 200), -1)  # Head
        cv2.rectangle(frame, (px - 14, py - 26), (px + 14, py + 12), (170, 180, 175), -1)  # Torso
        cv2.line(frame, (px - 7, py + 12), (px - 12 + leg_swing, py + 38), (140, 150, 145), 5)  # Left leg
        cv2.line(frame, (px + 7, py + 12), (px + 12 - leg_swing, py + 38), (140, 150, 145), 5)  # Right leg
        cv2.line(frame, (px - 14, py - 20), (px - 22, py + 4), (160, 170, 165), 4)  # Left arm
        cv2.line(frame, (px + 14, py - 20), (px + 22, py + 4), (160, 170, 165), 4)  # Right arm

        # Person 2 (Companion in group)
        p2x = px + 48
        p2y = py - 15
        cv2.circle(frame, (p2x, p2y - 38), 11, (190, 200, 190), -1)
        cv2.rectangle(frame, (p2x - 12, p2y - 26), (p2x + 12, p2y + 12), (160, 170, 165), -1)
        cv2.line(frame, (p2x - 6, p2y + 12), (p2x - 10 - leg_swing, p2y + 36), (130, 140, 135), 4)
        cv2.line(frame, (p2x + 6, p2y + 12), (p2x + 10 + leg_swing, p2y + 36), (130, 140, 135), 4)

        # Telemetry & timestamp overlay
        cv2.putText(frame, f"CAM-01 [SECTOR ALPHA] {t:.1f}s", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 180), 1)
        cv2.putText(frame, "STATUS: ARMED // BUFFER ZONE", (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 160, 200), 1)

        # Minor noise
        noise = np.random.randint(0, 10, (480, 640, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        out.write(frame)

    out.release()
    print(f"[Generator] Perimeter video saved: {output_path}")


def generate_checkpoint_video(output_path: str, duration_sec: int = 15, fps: int = 15):
    """
    Generates simulated checkpoint video with vehicles and license plates.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (640, 480))

    total_frames = duration_sec * fps
    print(f"[Generator] Creating Checkpoint clip: {output_path} ({total_frames} frames)...")

    for f in range(total_frames):
        t = f / float(fps)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Road and Checkpoint Barrier
        frame[0:240, :] = (30, 35, 40)
        frame[240:480, :] = (45, 48, 52)  # Asphalt road
        
        # Road lane markings
        for y in range(250, 480, 40):
            cv2.line(frame, (320, y), (320, y + 20), (180, 180, 180), 2)

        # Checkpoint boom barrier (yellow/black stripes)
        cv2.line(frame, (80, 280), (560, 280), (0, 200, 255), 4)

        # Moving Vehicle (SUV)
        progress = (f % total_frames) / total_frames
        vx = int(120 + progress * 400)
        vy = int(320 + 10 * math.sin(t * 0.5))

        # Vehicle Body
        cv2.rectangle(frame, (vx - 65, vy - 40), (vx + 65, vy + 20), (80, 95, 110), -1)
        cv2.rectangle(frame, (vx - 45, vy - 65), (vx + 40, vy - 40), (105, 120, 135), -1)  # Cabin
        # Windows
        cv2.rectangle(frame, (vx - 40, vy - 60), (vx - 5, vy - 42), (40, 50, 60), -1)
        cv2.rectangle(frame, (vx + 5, vy - 60), (vx + 35, vy - 42), (40, 50, 60), -1)
        # Headlights
        cv2.circle(frame, (vx + 63, vy - 10), 6, (180, 255, 255), -1)
        # Wheels
        cv2.circle(frame, (vx - 40, vy + 22), 14, (25, 25, 25), -1)
        cv2.circle(frame, (vx + 40, vy + 22), 14, (25, 25, 25), -1)

        # License Plate with legible text: DL01AB1234
        plate_x1, plate_y1 = vx + 40, vy + 2
        plate_x2, plate_y2 = vx + 64, vy + 16
        cv2.rectangle(frame, (plate_x1, plate_y1), (plate_x2, plate_y2), (245, 245, 245), -1)
        cv2.putText(frame, "DL01", (plate_x1 + 1, plate_y1 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.28, (0, 0, 0), 1)

        # Overlay text
        cv2.putText(frame, f"CAM-02 [CHECKPOINT BRAVO] {t:.1f}s", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 180), 1)
        cv2.putText(frame, "ANPR SENSOR ACTIVE", (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 160, 200), 1)

        # Minor sensor noise
        noise = np.random.randint(0, 8, (480, 640, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        out.write(frame)

    out.release()
    print(f"[Generator] Checkpoint video saved: {output_path}")


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sample_videos"))
    generate_perimeter_video(os.path.join(base_dir, "perimeter_cam_01.mp4"))
    generate_checkpoint_video(os.path.join(base_dir, "checkpoint_cam_02.mp4"))
