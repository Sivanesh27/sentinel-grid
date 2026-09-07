"""
ByteTrack Multi-Object Tracking module using Supervision.
Tracks targets across video frames, maintaining persistent IDs and trajectory histories.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import numpy as np
import supervision as sv
from app.detection.detector import TARGET_CLASSES


@dataclass
class TrackState:
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    centroid: Tuple[float, float]
    bottom_center: Tuple[float, float]
    trajectory: List[Tuple[float, float, float]] = field(default_factory=list)  # (x, y, timestamp)
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    dwell_time: float = 0.0
    zone_dwell_time: float = 0.0
    is_in_zone: bool = False
    is_breached: bool = False
    breach_direction: str = "none"  # "inbound", "outbound", "none"
    plate_number: Optional[str] = None
    plate_confidence: float = 0.0


class MultiObjectTracker:
    def __init__(self, track_activation_threshold: float = 0.25, lost_track_buffer: int = 30, max_trajectory_len: int = 40):
        """
        Initializes ByteTrack tracker from Supervision.
        """
        self.tracker = sv.ByteTrack(
            track_activation_threshold=track_activation_threshold,
            lost_track_buffer=lost_track_buffer,
            minimum_matching_threshold=0.8,
            frame_rate=15
        )
        self.tracks: Dict[int, TrackState] = {}
        self.max_trajectory_len = max_trajectory_len

    def update(self, sv_detections: sv.Detections) -> List[TrackState]:
        """
        Updates tracker with new detections and updates track states and trajectories.
        Returns list of currently active TrackState objects in this frame.
        """
        now = time.time()
        tracked_detections = self.tracker.update_with_detections(sv_detections)
        active_tracks: List[TrackState] = []

        if len(tracked_detections) == 0:
            return active_tracks

        for i in range(len(tracked_detections)):
            if tracked_detections.tracker_id is None or tracked_detections.tracker_id[i] is None:
                continue

            track_id = int(tracked_detections.tracker_id[i])
            bbox = tracked_detections.xyxy[i].tolist()
            class_id = int(tracked_detections.class_id[i]) if tracked_detections.class_id is not None else 0
            class_name = TARGET_CLASSES.get(class_id, "unknown")
            conf = float(tracked_detections.confidence[i]) if tracked_detections.confidence is not None else 0.5

            x1, y1, x2, y2 = bbox
            centroid = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
            bottom_center = ((x1 + x2) / 2.0, y2)  # Ground contact position

            if track_id not in self.tracks:
                self.tracks[track_id] = TrackState(
                    track_id=track_id,
                    class_id=class_id,
                    class_name=class_name,
                    confidence=conf,
                    bbox=bbox,
                    centroid=centroid,
                    bottom_center=bottom_center,
                    trajectory=[(bottom_center[0], bottom_center[1], now)],
                    first_seen=now,
                    last_seen=now,
                    dwell_time=0.0
                )
            else:
                track = self.tracks[track_id]
                track.bbox = bbox
                track.centroid = centroid
                track.bottom_center = bottom_center
                track.last_seen = now
                track.dwell_time = max(0.0, now - track.first_seen)
                track.confidence = (track.confidence * 0.7) + (conf * 0.3)  # EMA smoothing
                
                # Append position to trajectory
                track.trajectory.append((bottom_center[0], bottom_center[1], now))
                if len(track.trajectory) > self.max_trajectory_len:
                    track.trajectory.pop(0)

            active_tracks.append(self.tracks[track_id])

        # Cleanup stale tracks older than 60 seconds
        stale_ids = [tid for tid, t in self.tracks.items() if now - t.last_seen > 60.0]
        for tid in stale_ids:
            del self.tracks[tid]

        return active_tracks
