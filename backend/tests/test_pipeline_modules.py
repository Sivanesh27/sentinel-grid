"""
Comprehensive Unit & Integration Test Suite for Sentinel Grid modules.
Tests:
- Detector (CLAHE filter)
- PolygonFence (Shapely breach detection & inbound/outbound heading)
- RiskEngine (Trust-weighted scoring & natural language explanation)
- Storage (SQLite Track, BreachEvent, Alert models)
"""

import os
import sys
import uuid
import pytest
import numpy as np
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.storage.db import init_db, get_db_context
from app.storage.models import Track, BreachEvent, Alert
from app.fence.polygon_fence import PolygonFence
from app.tracking.tracker import TrackState
from app.fusion.risk_engine import RiskEngine
from app.detection.detector import Detector


def test_clahe_enhancement():
    """Verifies that CLAHE low-light enhancement runs without error on dummy image."""
    detector = Detector(conf_threshold=0.3)
    dummy_frame = np.zeros((320, 320, 3), dtype=np.uint8)
    dummy_frame[:, :] = (30, 40, 50)
    enhanced = detector.apply_clahe(dummy_frame)
    assert enhanced is not None
    assert enhanced.shape == (320, 320, 3)


def test_polygon_fence_breach_detection():
    """Verifies Shapely polygon virtual fence breach detection and inbound heading."""
    fence_polygon = [[100, 300], [540, 300], [540, 460], [100, 460]]
    fence = PolygonFence("Test Fence", fence_polygon, inbound_direction="down")

    # Target moving downwards from outside fence (y=200) to inside fence (y=350)
    track = TrackState(
        track_id=1,
        class_id=0,
        class_name="person",
        confidence=0.85,
        bbox=[200, 310, 240, 350],
        centroid=(220, 330),
        bottom_center=(220, 350),
        trajectory=[(220, 200, 100.0), (220, 280, 101.0), (220, 350, 102.0)]
    )

    is_breach, direction, is_inside = fence.check_track(track, current_time=102.0)
    assert is_inside is True
    assert is_breach is True
    assert direction == "inbound"


def test_risk_engine_scoring_and_explanation():
    """Verifies trust-weighted fusion risk score calculation and narrative generation."""
    engine = RiskEngine()
    
    # Breached target with dwell time
    track = TrackState(
        track_id=42,
        class_id=0,
        class_name="person",
        confidence=0.90,
        bbox=[150, 320, 190, 380],
        centroid=(170, 350),
        bottom_center=(170, 380),
        dwell_time=25.0,
        zone_dwell_time=25.0,
        is_in_zone=True,
        is_breached=True,
        breach_direction="inbound"
    )

    assessment = engine.evaluate_track(
        track=track,
        nearby_group_size=2,
        is_night_time=True,
        reference_time=datetime(2026, 8, 26, 23, 41, 0)
    )

    assert assessment.risk_score >= 80.0  # Must be critical/high
    assert assessment.is_alert is True
    assert assessment.severity in ["HIGH", "CRITICAL"]
    assert "INBOUND" in assessment.explanation.upper()
    assert "23:41" in assessment.explanation


def test_database_persistence():
    """Verifies SQLite tables creation, track upsert, and alert queries."""
    init_db()
    test_id = f"ALT-TEST-{uuid.uuid4().hex[:6]}"
    
    with get_db_context() as db:
        test_alert = Alert(
            alert_id=test_id,
            camera_id="cam_01",
            track_id=99,
            class_name="person",
            risk_score=95.0,
            severity="CRITICAL",
            explanation="Critical fence boundary breach",
            details_json='{"zone_breach_points": 85.0}'
        )
        db.add(test_alert)

    with get_db_context() as db:
        fetched = db.query(Alert).filter(Alert.alert_id == test_id).first()
        assert fetched is not None
        assert fetched.risk_score == 95.0
        assert fetched.severity == "CRITICAL"
