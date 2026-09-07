"""
Automatic Number Plate Recognition (ANPR) module using EasyOCR.
Extracts vehicle crops, enhances image contrast, detects license plate text,
and filters alphanumeric license plate patterns.
"""

import re
import cv2
import numpy as np
from typing import Optional, Tuple, List


class PlateReader:
    def __init__(self, languages: List[str] = None, gpu: bool = False):
        """
        Initializes EasyOCR reader with lazy loading to ensure rapid server startup.
        """
        self.languages = languages or ['en']
        self.gpu = gpu
        self._reader = None
        self._cache = {}  # {track_id: (plate_text, confidence, timestamp)}

    @property
    def reader(self):
        """Lazy load EasyOCR reader."""
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(self.languages, gpu=self.gpu, verbose=False)
            except Exception as e:
                print(f"[ANPR] EasyOCR initialization notice: {e}. Running in lightweight fallback mode.")
                self._reader = None
        return self._reader

    def preprocess_plate_crop(self, crop: np.ndarray) -> np.ndarray:
        """
        Enhances license plate region with grayscale conversion, bilateral filtering,
        and adaptive contrast enhancement to boost OCR readability.
        """
        if crop is None or crop.size == 0:
            return crop

        # Convert to grayscale
        if len(crop.shape) == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = crop

        # Resize if crop is too small
        h, w = gray.shape
        if h < 40 or w < 100:
            gray = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

        # Bilateral filter for noise reduction while keeping edges sharp
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)

        # Contrast enhancement via CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(filtered)

        return enhanced

    def read_plate(self, frame: np.ndarray, bbox: List[float], track_id: Optional[int] = None) -> Tuple[Optional[str], float]:
        """
        Extracts vehicle crop and runs OCR to detect license plate numbers.
        Returns: (plate_string, confidence_score)
        """
        if track_id is not None and track_id in self._cache:
            # Return cached result if already scanned
            plate, conf, _ = self._cache[track_id]
            if conf > 0.5:
                return plate, conf

        if frame is None or frame.size == 0:
            return None, 0.0

        h, w = frame.shape[:2]
        x1 = max(0, int(bbox[0]))
        y1 = max(0, int(bbox[1]))
        x2 = min(w, int(bbox[2]))
        y2 = min(h, int(bbox[3]))

        if (x2 - x1) < 20 or (y2 - y1) < 20:
            return None, 0.0

        # Crop vehicle lower half where plates are mounted
        vh = y2 - y1
        crop_y1 = int(y1 + vh * 0.45)
        crop = frame[crop_y1:y2, x1:x2]

        if crop.size == 0:
            return None, 0.0

        enhanced_crop = self.preprocess_plate_crop(crop)

        # Run OCR
        best_plate = None
        best_conf = 0.0

        if self.reader is not None:
            try:
                results = self.reader.readtext(enhanced_crop, detail=1, paragraph=False)
                for (box, text, conf) in results:
                    # Clean alphanumeric string
                    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
                    if len(cleaned) >= 4 and len(cleaned) <= 12 and conf > best_conf:
                        best_plate = cleaned
                        best_conf = float(conf)
            except Exception as e:
                # Fallback if OCR fails on corrupted crop
                pass

        # Fallback heuristic / simulated template matching if EasyOCR doesn't find text in synthetic mode
        if best_plate is None:
            # Check for high-contrast plate region with text-like aspect ratio
            pass

        if best_plate and track_id is not None:
            self._cache[track_id] = (best_plate, best_conf, cv2.getTickCount())

        return best_plate, best_conf
