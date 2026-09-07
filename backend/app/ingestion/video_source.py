"""
High-Speed Video Source Ingestion module for Sentinel Grid.
Reads local .mp4 files or RTSP streams with low-overhead frame decoding and continuous looping.
"""

import os
import time
import math
import cv2
import numpy as np
from typing import Tuple, Optional

cv2.setNumThreads(1)


class VideoStreamSource:
    def __init__(self, source_path: str, target_fps: int = 15, camera_id: str = "cam_01"):
        """
        Initializes video stream reader.
        source_path: path to .mp4 or rtsp:// url.
        target_fps: frame rate throttle for simulated live streaming.
        """
        self.camera_id = camera_id
        self.target_fps = target_fps
        self.frame_delay = 1.0 / max(1, target_fps)
        self.source_path = source_path
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_synthetic = False
        self.synthetic_frame_count = 0
        self.last_frame_time = 0.0

        # Resolve relative paths relative to backend root
        if not source_path.startswith("rtsp://") and not os.path.isabs(source_path):
            backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            self.full_path = os.path.normpath(os.path.join(backend_root, source_path))
        else:
            self.full_path = source_path

        self._open_source()

    def _open_source(self):
        """Attempts to open video file or RTSP stream; falls back to synthetic mode if missing."""
        if os.path.exists(self.full_path) or self.full_path.startswith("rtsp://"):
            self.cap = cv2.VideoCapture(self.full_path)
            if self.cap.isOpened():
                self.is_synthetic = False
                print(f"[VideoSource] Opened real stream: {self.full_path} for {self.camera_id}")
                return
            else:
                print(f"[VideoSource] Failed to open {self.full_path}. Switching to synthetic generator.")
        else:
            print(f"[VideoSource] File {self.full_path} not found. Running in synthetic fallback mode.")

        self.is_synthetic = True

    def get_frame(self) -> Tuple[bool, np.ndarray]:
        """
        Retrieves the next frame with minimal decoding latency.
        Loops video automatically at EOF.
        """
        if not self.is_synthetic and self.cap is not None:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                # Loop back to beginning of video file
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.is_synthetic = True
                    frame = self._generate_synthetic_frame()
            if frame is not None and (frame.shape[1] != 640 or frame.shape[0] != 480):
                frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)
        else:
            frame = self._generate_synthetic_frame()

        return True, frame

    def _generate_synthetic_frame(self) -> np.ndarray:
        """
        Generates simulated border CCTV footage with moving objects and telemetry overlays.
        """
        self.synthetic_frame_count += 1
        t = self.synthetic_frame_count / 15.0

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :] = (20, 24, 28)

        cv2.line(frame, (0, 360), (640, 360), (45, 55, 60), 2)
        for fx in range(0, 640, 40):
            cv2.line(frame, (fx, 320), (fx, 360), (50, 60, 65), 1)

        if "01" in self.camera_id:
            px = int(220 + 80 * math.sin(t * 0.4))
            py = int(250 + ((t * 18) % 200))
            cv2.circle(frame, (px, py - 35), 12, (180, 190, 180), -1)
            cv2.rectangle(frame, (px - 14, py - 23), (px + 14, py + 15), (150, 160, 150), -1)
        else:
            vx = int(140 + ((t * 22) % 400))
            vy = int(320 + 15 * math.sin(t * 0.3))
            cv2.rectangle(frame, (vx - 60, vy - 35), (vx + 60, vy + 20), (70, 80, 95), -1)
            plate_x1, plate_y1 = vx - 25, vy + 2
            plate_x2, plate_y2 = vx + 25, vy + 16
            cv2.rectangle(frame, (plate_x1, plate_y1), (plate_x2, plate_y2), (240, 240, 240), -1)
            cv2.putText(frame, "DL01AB", (plate_x1 + 2, plate_y1 + 11), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (10, 10, 10), 1)

        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S") + f" [CAM:{self.camera_id}] (SIM)"
        cv2.putText(frame, timestamp_str, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 180), 1)

        return frame

    def release(self):
        """Releases video capture resource."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
