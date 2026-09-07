"""
Sentinel Grid — Main FastAPI Backend Application.
Border CCTV Video Analytics Platform for Smart India Hackathon 2026 (PS 26187).
"""

import os
import json
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.storage.db import init_db
from app.detection.detector import Detector
from app.anpr.plate_reader import PlateReader
from app.fusion.risk_engine import RiskEngine
from app.pipeline import CameraPipeline
from app.api.ws import ws_manager
from app.api.routes import router as api_router
import app.api.routes as routes_module


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CAMERAS_CONFIG_PATH = os.path.join(ROOT_DIR, "config/cameras.json")
SAMPLE_VIDEOS_DIR = os.path.join(ROOT_DIR, "backend/sample_videos")

pipeline_tasks: List[asyncio.Task] = []


def ensure_sample_videos():
    """Generates synthetic video clips if sample_videos folder is empty."""
    os.makedirs(SAMPLE_VIDEOS_DIR, exist_ok=True)
    v1 = os.path.join(SAMPLE_VIDEOS_DIR, "perimeter_cam_01.mp4")
    v2 = os.path.join(SAMPLE_VIDEOS_DIR, "checkpoint_cam_02.mp4")

    if not os.path.exists(v1) or not os.path.exists(v2):
        print("[Main] Sample videos not found. Auto-generating synthetic test video clips...")
        try:
            from scripts.generate_sample_videos import generate_perimeter_video, generate_checkpoint_video
            if not os.path.exists(v1):
                generate_perimeter_video(v1, duration_sec=15)
            if not os.path.exists(v2):
                generate_checkpoint_video(v2, duration_sec=15)
        except Exception as e:
            print(f"[Main] Notice: could not pre-generate video files: {e}. VideoStreamSource will use on-the-fly synthetic generation.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes models, database, and launches surveillance pipeline background workers."""
    print("=" * 65)
    print("  SENTINEL GRID // AI BORDER SURVEILLANCE PLATFORM")
    print("  Smart India Hackathon 2026 (PS 26187)")
    print("=" * 65)

    # 1. Initialize SQLite Database
    init_db()
    print("[Main] SQLite database initialized.")

    # 2. Check and generate sample videos if needed
    ensure_sample_videos()

    # 3. Initialize Shared Perception & Fusion Engines
    detector = Detector(model_name="yolov8n.pt", conf_threshold=0.35, imgsz=320)
    plate_reader = PlateReader(gpu=False)
    risk_engine = RiskEngine()

    routes_module.global_risk_engine = risk_engine

    # 4. Load Camera Configurations
    cameras_config: List[Dict[str, Any]] = []
    if os.path.exists(CAMERAS_CONFIG_PATH):
        try:
            with open(CAMERAS_CONFIG_PATH, "r", encoding="utf-8") as f:
                cameras_config = json.load(f)
        except Exception as e:
            print(f"[Main] Error reading cameras config: {e}")

    if not cameras_config:
        cameras_config = [
            {
                "id": "cam_01",
                "name": "Perimeter Sector Alpha",
                "source": "sample_videos/perimeter_cam_01.mp4",
                "fps": 15,
                "night_mode": False,
                "fence": {
                    "name": "Perimeter Buffer Zone",
                    "polygon": [[100, 300], [540, 300], [540, 460], [100, 460]],
                    "inbound_direction": "down"
                }
            }
        ]

    num_cams = len(cameras_config)
    cadence = 1 if num_cams <= 2 else (2 if num_cams <= 4 else 3)
    print(f"[Main] Auto-calibrated detection cadence: 1/{cadence} for {num_cams} simultaneous streams.")

    # 5. Launch per-camera surveillance pipelines
    for cam_cfg in cameras_config:
        pipeline = CameraPipeline(
            camera_config=cam_cfg,
            detector=detector,
            plate_reader=plate_reader,
            risk_engine=risk_engine,
            detect_interval=cadence
        )
        routes_module.active_pipelines[pipeline.camera_id] = pipeline
        task = asyncio.create_task(pipeline.run())
        pipeline_tasks.append(task)

    print(f"[Main] Successfully launched {len(pipeline_tasks)} camera pipeline workers.")

    yield

    # Clean shutdown
    print("[Main] Shutting down surveillance pipelines...")
    for p in list(routes_module.active_pipelines.values()):
        p.stop()
    for task in pipeline_tasks:
        task.cancel()
    try:
        await asyncio.wait_for(asyncio.gather(*pipeline_tasks, return_exceptions=True), timeout=2.0)
    except Exception:
        pass
    print("[Main] All pipelines terminated cleanly.")


app = FastAPI(
    title="Sentinel Grid Video Analytics API",
    version="1.0.0",
    description="Real-time AI Video Analytics Platform for Border Surveillance (SIH 2026 PS 26187)",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Sentinel Grid",
        "version": "1.0.0",
        "description": "AI Video Analytics for Border CCTV Surveillance (PS 26187)",
        "docs_url": "/docs",
        "websocket_endpoint": "/ws/live",
        "active_cameras": list(routes_module.active_pipelines.keys())
    }


@app.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    """Live WebSocket stream for video frames, object telemetry, and security alerts."""
    await ws_manager.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                if data.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
