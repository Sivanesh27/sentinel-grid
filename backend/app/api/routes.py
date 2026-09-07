"""
REST API routes for Sentinel Grid surveillance dashboard.
Handles camera status, night mode toggles, alert history, track logs, fusion config,
and live drag-and-drop virtual fence polygon updates.
"""

import os
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.storage.db import get_db
from app.storage.models import Alert, Track, BreachEvent
from app.fusion.risk_engine import RiskEngine

router = APIRouter()

active_pipelines: Dict[str, Any] = {}
global_risk_engine: Optional[RiskEngine] = None
CAMERAS_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../config/cameras.json"))


class ConfigUpdate(BaseModel):
    weights: Dict[str, float]
    alert_threshold: float = Field(..., ge=0.0, le=100.0)


class NightModeToggleRequest(BaseModel):
    enabled: Optional[bool] = None


class FenceUpdateRequest(BaseModel):
    polygon: List[List[float]]
    name: Optional[str] = None
    inbound_direction: Optional[str] = None


@router.get("/health")
async def get_health():
    """Returns system status, active camera feeds, and health metrics."""
    return {
        "status": "online",
        "system": "Sentinel Grid PS-26187",
        "active_cameras": len(active_pipelines),
        "cameras": [
            {
                "id": cid,
                "name": p.name,
                "fps": round(p.current_fps, 1),
                "night_mode": p.night_mode,
                "is_synthetic": p.video_source.is_synthetic
            }
            for cid, p in active_pipelines.items()
        ]
    }


@router.get("/cameras")
async def list_cameras():
    """Returns all configured cameras and their virtual fence definitions."""
    results = []
    for cid, p in active_pipelines.items():
        results.append({
            "id": p.camera_id,
            "name": p.name,
            "source": p.source_path,
            "fps": round(p.current_fps, 1),
            "night_mode": p.night_mode,
            "fence": {
                "name": p.fence.name,
                "polygon": p.fence.points,
                "inbound_direction": p.fence.inbound_direction
            }
        })
    return results


@router.post("/cameras/{camera_id}/night_mode")
async def toggle_camera_night_mode(camera_id: str, req: NightModeToggleRequest):
    """Toggles or sets night vision CLAHE low-light enhancement for a specific camera."""
    pipeline = active_pipelines.get(camera_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")

    new_state = pipeline.toggle_night_mode(req.enabled)
    return {
        "camera_id": camera_id,
        "night_mode": new_state,
        "message": f"Night mode {'enabled' if new_state else 'disabled'} for {pipeline.name}"
    }


@router.post("/cameras/{camera_id}/fence")
async def update_camera_fence(camera_id: str, req: FenceUpdateRequest):
    """
    Updates the virtual fence polygon coordinates in real-time and persists to config/cameras.json.
    """
    pipeline = active_pipelines.get(camera_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")

    if len(req.polygon) < 3:
        raise HTTPException(status_code=400, detail="Polygon must have at least 3 vertices")

    # 1. Update running pipeline instance in memory
    pipeline.fence.set_polygon(
        polygon_points=req.polygon,
        name=req.name,
        inbound_direction=req.inbound_direction
    )

    # 2. Persist updated polygon to config/cameras.json
    try:
        if os.path.exists(CAMERAS_CONFIG_PATH):
            with open(CAMERAS_CONFIG_PATH, "r", encoding="utf-8") as f:
                cams = json.load(f)
            
            for cam in cams:
                if cam.get("id") == camera_id:
                    if "fence" not in cam:
                        cam["fence"] = {}
                    cam["fence"]["polygon"] = req.polygon
                    if req.name:
                        cam["fence"]["name"] = req.name
                    if req.inbound_direction:
                        cam["fence"]["inbound_direction"] = req.inbound_direction

            with open(CAMERAS_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cams, f, indent=2)
    except Exception as e:
        print(f"[Routes] Error saving updated fence to cameras.json: {e}")

    return {
        "status": "success",
        "camera_id": camera_id,
        "fence": {
            "name": pipeline.fence.name,
            "polygon": pipeline.fence.points,
            "inbound_direction": pipeline.fence.inbound_direction
        },
        "message": "Virtual fence updated successfully."
    }


@router.get("/alerts")
async def get_alerts(
    camera_id: Optional[str] = None,
    min_risk: Optional[float] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Fetches historical security alerts sorted by newest first."""
    query = db.query(Alert)
    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    if min_risk is not None:
        query = query.filter(Alert.risk_score >= min_risk)

    alerts = query.order_by(desc(Alert.timestamp)).limit(limit).all()

    return [
        {
            "id": a.id,
            "alert_id": a.alert_id,
            "camera_id": a.camera_id,
            "track_id": a.track_id,
            "class_name": a.class_name,
            "risk_score": a.risk_score,
            "severity": a.severity,
            "explanation": a.explanation,
            "timestamp": a.timestamp.isoformat(),
            "snapshot": a.snapshot_base64,
            "details": a.details_json,
            "acknowledged": a.acknowledged
        }
        for a in alerts
    ]


@router.get("/alerts/{alert_id}")
async def get_alert_detail(alert_id: str, db: Session = Depends(get_db)):
    """Fetches full details for a specific alert."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "id": alert.id,
        "alert_id": alert.alert_id,
        "camera_id": alert.camera_id,
        "track_id": alert.track_id,
        "class_name": alert.class_name,
        "risk_score": alert.risk_score,
        "severity": alert.severity,
        "explanation": alert.explanation,
        "timestamp": alert.timestamp.isoformat(),
        "snapshot": alert.snapshot_base64,
        "details": alert.details_json,
        "acknowledged": alert.acknowledged
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """Marks an alert as acknowledged by the operator."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.acknowledged = True
    db.commit()
    return {"status": "success", "alert_id": alert_id, "acknowledged": True}


@router.get("/tracks")
async def get_tracks(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Returns recent tracked identities logged in the database."""
    tracks = db.query(Track).order_by(desc(Track.last_seen)).limit(limit).all()
    return [
        {
            "id": t.id,
            "track_id": t.track_id,
            "camera_id": t.camera_id,
            "class_name": t.class_name,
            "confidence": t.confidence,
            "first_seen": t.first_seen.isoformat(),
            "last_seen": t.last_seen.isoformat(),
            "total_dwell_time": round(t.total_dwell_time, 1),
            "max_risk_score": round(t.max_risk_score, 1),
            "plate_number": t.plate_number,
            "is_breached": t.is_breached,
            "inbound_breach": t.inbound_breach
        }
        for t in tracks
    ]


@router.get("/config")
async def get_fusion_config():
    """Returns current trust-weighted risk engine rules and alert threshold."""
    if not global_risk_engine:
        raise HTTPException(status_code=500, detail="Risk engine not initialized")
    return {
        "weights": global_risk_engine.weights,
        "alert_threshold": global_risk_engine.alert_threshold
    }


@router.post("/config")
async def update_fusion_config(req: ConfigUpdate):
    """Updates fusion risk weights and alert threshold in real-time."""
    if not global_risk_engine:
        raise HTTPException(status_code=500, detail="Risk engine not initialized")

    global_risk_engine.save_config(req.weights, req.alert_threshold)
    return {
        "status": "success",
        "weights": global_risk_engine.weights,
        "alert_threshold": global_risk_engine.alert_threshold,
        "message": "Fusion weights updated successfully."
    }
