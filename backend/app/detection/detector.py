"""
High-Performance YOLOv8 Object Detection module with CLAHE low-light enhancement.
Optimized for multi-stream CPU/GPU inference with torch.inference_mode and 320px tensor size.
"""

import os
from typing import List, Dict, Any, Tuple
import cv2
import numpy as np
from dataclasses import dataclass
import torch
from ultralytics import YOLO
import supervision as sv

# Optimize PyTorch CPU thread count
torch.set_num_threads(max(1, min(4, os.cpu_count() or 4)))


TARGET_CLASSES = {
    0: "person",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}


@dataclass
class DetectionResult:
    xyxy: List[float]
    class_id: int
    class_name: str
    confidence: float


class Detector:
    def __init__(self, model_name: str = "yolov8n.pt", conf_threshold: float = 0.35, imgsz: int = 320):
        """
        Initializes YOLOv8 model with optimized inference size for high multi-camera FPS.
        """
        self.conf_threshold = conf_threshold
        self.target_class_ids = list(TARGET_CLASSES.keys())
        self.imgsz = imgsz
        
        try:
            self.model = YOLO(model_name)
        except Exception as e:
            print(f"[Detector] Error loading {model_name}: {e}. Retrying default yolov8n.pt...")
            self.model = YOLO("yolov8n.pt")

        # Warm up model to ensure weights and layers are fused safely
        try:
            dummy = np.zeros((320, 320, 3), dtype=np.uint8)
            with torch.inference_mode():
                self.model(dummy, imgsz=self.imgsz, verbose=False)
        except Exception as e:
            print(f"[Detector] Warm-up notice: {e}")

        # Initialize CLAHE filter for night mode
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

    def apply_clahe(self, frame: np.ndarray) -> np.ndarray:
        """
        Applies CLAHE on the L-channel in LAB color space for low-light enhancement.
        """
        if frame is None or frame.size == 0:
            return frame
        try:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            cl = self.clahe.apply(l_channel)
            limg = cv2.merge((cl, a_channel, b_channel))
            enhanced_bgr = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
            return enhanced_bgr
        except Exception as e:
            print(f"[Detector] CLAHE enhancement failed: {e}")
            return frame

    def detect(self, frame: np.ndarray, night_mode: bool = False) -> Tuple[sv.Detections, List[DetectionResult], np.ndarray]:
        """
        Performs high-speed object detection on frame using torch.inference_mode.
        """
        processed_frame = self.apply_clahe(frame) if night_mode else frame

        with torch.inference_mode():
            results = self.model(
                processed_frame,
                classes=self.target_class_ids,
                conf=self.conf_threshold,
                imgsz=self.imgsz,
                verbose=False
            )[0]

        sv_detections = sv.Detections.from_ultralytics(results)

        detection_list: List[DetectionResult] = []
        if len(sv_detections) > 0:
            for i in range(len(sv_detections)):
                xyxy = sv_detections.xyxy[i].tolist()
                class_id = int(sv_detections.class_id[i]) if sv_detections.class_id is not None else 0
                class_name = TARGET_CLASSES.get(class_id, "unknown")
                confidence = float(sv_detections.confidence[i]) if sv_detections.confidence is not None else 0.0

                detection_list.append(DetectionResult(
                    xyxy=xyxy,
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence
                ))

        return sv_detections, detection_list, processed_frame
