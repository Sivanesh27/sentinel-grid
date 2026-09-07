"""
High-Performance Surveillance Pipeline Coordinator for Sentinel Grid.
Optimized for high multi-camera FPS with cadenced detection, async DB sync, and fast streaming.
"""

import os
import time
import base64
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import cv2
import numpy as np

from app.ingestion.video_source import VideoStreamSource
from app.detection.detector import Detector
from app.tracking.tracker import MultiObjectTracker, TrackState
from app.fence.polygon_fence import PolygonFence
from app.anpr.plate_reader import PlateReader
from app.fusion.risk_engine import RiskEngine, RiskAssessment
from app.storage.db import get_db_context
from app.storage.models import Track, BreachEvent, Alert
from app.api.ws import ws_manager


class CameraPipeline:
    def __init__(
        self,
        camera_config: Dict[str, Any],
        detector: Detector,
        plate_reader: PlateReader,
        risk_engine: RiskEngine,
        detect_interval: int = 2
    ):
        self.config = camera_config
        self.camera_id = camera_config.get("id", "cam_01")
        self.name = camera_config.get("name", f"Camera {self.camera_id}")
        self.source_path = camera_config.get("source", "sample_videos/perimeter_cam_01.mp4")
        self.target_fps = int(camera_config.get("fps", 15))
        self.night_mode = bool(camera_config.get("night_mode", False))
        self.detect_interval = detect_interval  # Run YOLO every N frames for max FPS

        # Core modules
        self.video_source = VideoStreamSource(self.source_path, target_fps=self.target_fps, camera_id=self.camera_id)
        self.detector = detector
        self.plate_reader = plate_reader
        self.risk_engine = risk_engine
        self.tracker = MultiObjectTracker()

        # Initialize Virtual Fence
        fence_cfg = camera_config.get("fence", {})
        fence_name = fence_cfg.get("name", "Restricted Perimeter")
        fence_poly = fence_cfg.get("polygon", [[100, 300], [540, 300], [540, 460], [100, 460]])
        inbound_dir = fence_cfg.get("inbound_direction", "down")
        self.fence = PolygonFence(name=fence_name, polygon_points=fence_poly, inbound_direction=inbound_dir)

        self.running = False
        self.last_alert_time: Dict[int, float] = {}
        self.last_anpr_time: Dict[int, float] = {}
        self.last_db_sync = 0.0
        self.fps_counter = 0
        self.current_fps = float(self.target_fps)
        self.last_fps_time = time.time()
        self.frame_idx = 0
        self.cached_tracks: List[TrackState] = []
        self.cached_assessments: Dict[int, RiskAssessment] = {}

    def toggle_night_mode(self, enabled: Optional[bool] = None) -> bool:
        """Toggles or sets night vision low-light enhancement mode."""
        if enabled is not None:
            self.night_mode = enabled
        else:
            self.night_mode = not self.night_mode
        print(f"[Pipeline:{self.camera_id}] Night mode set to: {self.night_mode}")
        return self.night_mode

    def _calculate_group_sizes(self, tracks: List[TrackState]) -> Dict[int, int]:
        """Calculates nearby clustering for each track."""
        group_sizes = {t.track_id: 1 for t in tracks}
        if len(tracks) < 2:
            return group_sizes

        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                t1 = tracks[i]
                t2 = tracks[j]
                dist = np.hypot(t1.centroid[0] - t2.centroid[0], t1.centroid[1] - t2.centroid[1])
                if dist < 120.0:
                    group_sizes[t1.track_id] += 1
                    group_sizes[t2.track_id] += 1

        return group_sizes

    def _draw_annotations(self, frame: np.ndarray, tracks: List[TrackState], assessments: Dict[int, RiskAssessment]) -> np.ndarray:
        """Renders tactical annotations, virtual fence, HUD, and tracking telemetry on the frame."""
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # 1. Draw Virtual Fence Polygon
        pts = np.array(self.fence.points, np.int32).reshape((-1, 1, 2))
        has_active_breach = any(t.is_breached or t.is_in_zone for t in tracks)
        fence_color = (0, 70, 255) if has_active_breach else (0, 220, 100)

        # Translucent filled zone
        overlay = annotated.copy()
        cv2.fillPoly(overlay, [pts], fence_color)
        cv2.addWeighted(overlay, 0.15, annotated, 0.85, 0, annotated)
        cv2.polylines(annotated, [pts], isClosed=True, color=fence_color, thickness=2, lineType=cv2.LINE_AA)

        # Fence label
        fx, fy = self.fence.points[0]
        cv2.putText(annotated, f"// VIRTUAL FENCE: {self.fence.name.upper()}", (int(fx), int(fy) - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, fence_color, 1, cv2.LINE_AA)

        # 2. Draw Object Tracks & Bounding Boxes
        for track in tracks:
            assessment = assessments.get(track.track_id)
            risk_score = assessment.risk_score if assessment else 0.0

            if risk_score >= 80.0:
                color = (0, 0, 255)       # Red (Critical)
            elif risk_score >= 60.0:
                color = (0, 140, 255)     # Amber (High)
            elif risk_score >= 40.0:
                color = (0, 220, 255)     # Yellow (Medium)
            else:
                color = (0, 220, 100)     # Green (Low)

            x1, y1, x2, y2 = [int(v) for v in track.bbox]

            # Tactical corner-bracket box
            corner_len = min(15, int((x2 - x1) * 0.25))
            thick = 2
            cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), color, thick)
            cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), color, thick)
            cv2.line(annotated, (x2, y1), (x2 - corner_len, y1), color, thick)
            cv2.line(annotated, (x2, y1), (x2, y1 + corner_len), color, thick)
            cv2.line(annotated, (x1, y2), (x1 + corner_len, y2), color, thick)
            cv2.line(annotated, (x1, y2), (x1, y2 - corner_len), color, thick)
            cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), color, thick)
            cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), color, thick)

            # Trajectory
            if len(track.trajectory) > 1:
                t_pts = np.array([(int(p[0]), int(p[1])) for p in track.trajectory], np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated, [t_pts], isClosed=False, color=color, thickness=1, lineType=cv2.LINE_AA)

            # Telemetry label
            label = f"ID:{track.track_id} {track.class_name.upper()} | RISK:{int(risk_score)}"
            if track.plate_number:
                label += f" | [{track.plate_number}]"

            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - 18)), (x1 + lw + 6, y1), (15, 20, 25), -1)
            cv2.rectangle(annotated, (x1, max(0, y1 - 18)), (x1 + lw + 6, y1), color, 1)
            cv2.putText(annotated, label, (x1 + 3, max(12, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

        # 3. Top HUD Bar
        cv2.rectangle(annotated, (0, 0), (w, 30), (10, 14, 20), -1)
        cv2.line(annotated, (0, 30), (w, 30), (0, 255, 180), 1)

        clean_name = self.name.encode('ascii', 'ignore').decode('ascii').upper()
        hud_title = f"{clean_name} // FPS: {self.current_fps:.1f}"
        cv2.putText(annotated, hud_title, (12, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 255, 180), 1, cv2.LINE_AA)

        mode_badge = "NIGHT CLAHE: ON" if self.night_mode else "MODE: DAY/OPT"
        mode_color = (0, 200, 255) if self.night_mode else (180, 180, 180)
        cv2.putText(annotated, mode_badge, (w - 170, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.36, mode_color, 1, cv2.LINE_AA)

        return annotated

    async def run(self):
        """High-throughput asynchronous pipeline loop."""
        self.running = True
        print(f"[Pipeline] Camera {self.camera_id} started processing (Cadence: 1/{self.detect_interval})...")

        loop = asyncio.get_running_loop()

        while self.running:
            try:
                self.frame_idx += 1
                ret, raw_frame = await loop.run_in_executor(None, self.video_source.get_frame)
                if not ret or raw_frame is None:
                    await asyncio.sleep(0.02)
                    continue

                curr_time = time.time()

                # FPS Calculation
                self.fps_counter += 1
                if curr_time - self.last_fps_time >= 1.0:
                    self.current_fps = self.fps_counter / (curr_time - self.last_fps_time)
                    self.fps_counter = 0
                    self.last_fps_time = curr_time

                # 1. Detection (Run on scheduled cadence for max FPS)
                if self.frame_idx % self.detect_interval == 0:
                    sv_dets, det_results, processed_frame = await loop.run_in_executor(
                        None, self.detector.detect, raw_frame, self.night_mode
                    )
                    active_tracks = self.tracker.update(sv_dets)
                    self.cached_tracks = active_tracks
                else:
                    active_tracks = self.cached_tracks

                # 2. Group Clustering
                group_sizes = self._calculate_group_sizes(active_tracks)

                # 3. Spatial Analytics, ANPR & Fusion Risk Scoring
                assessments: Dict[int, RiskAssessment] = {}

                for track in active_tracks:
                    is_breach, breach_dir, is_inside = self.fence.check_track(track, curr_time)

                    # ANPR for vehicles (throttled)
                    if track.class_name in ["car", "truck", "bus"] and not track.plate_number:
                        last_anpr = self.last_anpr_time.get(track.track_id, 0.0)
                        if curr_time - last_anpr > 1.0:  # Check at most once per second
                            self.last_anpr_time[track.track_id] = curr_time
                            plate_text, conf = await loop.run_in_executor(
                                None, self.plate_reader.read_plate, raw_frame, track.bbox, track.track_id
                            )
                            if plate_text:
                                track.plate_number = plate_text
                                track.plate_confidence = conf

                    # Risk Assessment
                    grp_size = group_sizes.get(track.track_id, 1)
                    assessment = self.risk_engine.evaluate_track(
                        track=track,
                        nearby_group_size=grp_size,
                        is_night_time=self.night_mode or (datetime.now().hour < 6 or datetime.now().hour > 19)
                    )
                    assessments[track.track_id] = assessment

                    # High-Priority Alert Dispatch
                    if assessment.is_alert:
                        last_sent = self.last_alert_time.get(track.track_id, 0.0)
                        if curr_time - last_sent > 4.0:
                            self.last_alert_time[track.track_id] = curr_time

                            _, snap_buf = cv2.imencode('.jpg', raw_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                            snap_b64 = base64.b64encode(snap_buf).decode('utf-8')
                            alert_uid = f"ALT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

                            alert_payload = {
                                "alert_id": alert_uid,
                                "camera_id": self.camera_id,
                                "camera_name": self.name,
                                "track_id": track.track_id,
                                "class_name": track.class_name,
                                "risk_score": assessment.risk_score,
                                "severity": assessment.severity,
                                "explanation": assessment.explanation,
                                "timestamp": assessment.timestamp.isoformat(),
                                "snapshot": f"data:image/jpeg;base64,{snap_b64}",
                                "factor_breakdown": assessment.factor_breakdown
                            }

                            try:
                                with get_db_context() as db:
                                    db_alert = Alert(
                                        alert_id=alert_uid,
                                        camera_id=self.camera_id,
                                        track_id=track.track_id,
                                        class_name=track.class_name,
                                        risk_score=assessment.risk_score,
                                        severity=assessment.severity,
                                        explanation=assessment.explanation,
                                        snapshot_base64=f"data:image/jpeg;base64,{snap_b64}",
                                        details_json=json.dumps(assessment.factor_breakdown)
                                    )
                                    db.add(db_alert)
                            except Exception:
                                pass

                            await ws_manager.broadcast_alert(alert_payload)

                self.cached_assessments = assessments

                # 4. Periodic DB Batch Sync (every 1.5s instead of every frame)
                if curr_time - self.last_db_sync > 1.5 and active_tracks:
                    self.last_db_sync = curr_time
                    try:
                        with get_db_context() as db:
                            for track in active_tracks:
                                track_rec = db.query(Track).filter(
                                    Track.camera_id == self.camera_id,
                                    Track.track_id == track.track_id
                                ).first()
                                if not track_rec:
                                    db.add(Track(
                                        track_id=track.track_id,
                                        camera_id=self.camera_id,
                                        class_name=track.class_name,
                                        confidence=track.confidence,
                                        total_dwell_time=track.dwell_time,
                                        max_risk_score=assessments.get(track.track_id, RiskAssessment(0,0,False,'','',{},datetime.now())).risk_score,
                                        plate_number=track.plate_number,
                                        is_breached=track.is_breached,
                                        inbound_breach=(track.breach_direction == "inbound")
                                    ))
                                else:
                                    track_rec.last_seen = datetime.utcnow()
                                    track_rec.total_dwell_time = track.dwell_time
                    except Exception:
                        pass

                # 5. Render tactical overlays and broadcast only if clients are connected
                has_viewers = len(ws_manager.active_connections) > 0

                if has_viewers:
                    annotated_frame = self._draw_annotations(raw_frame, active_tracks, assessments)
                    _, enc_buf = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 55])
                    frame_b64 = base64.b64encode(enc_buf).decode('utf-8')

                    await ws_manager.broadcast_frame(
                        camera_id=self.camera_id,
                        frame_base64=f"data:image/jpeg;base64,{frame_b64}",
                        fps=self.current_fps,
                        active_tracks=len(active_tracks)
                    )

                # Frame rate pacing
                elapsed = time.time() - curr_time
                if has_viewers:
                    target_delay = 1.0 / max(1.0, self.target_fps)
                    sleep_dur = max(0.015, target_delay - elapsed)
                    await asyncio.sleep(sleep_dur)
                else:
                    # Idle standby: 5 FPS sleep keeps CPU at <1% for cloud health probes
                    await asyncio.sleep(0.20)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Pipeline:{self.camera_id}] Loop error: {e}")
                await asyncio.sleep(0.05)

        self.video_source.release()
        print(f"[Pipeline:{self.camera_id}] Stopped.")

    def stop(self):
        self.running = False
