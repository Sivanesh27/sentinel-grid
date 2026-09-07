# Sentinel Grid — AI Border CCTV Surveillance Platform
**Smart India Hackathon 2026 (Problem Statement 26187)**

![Sentinel Grid Architecture](https://img.shields.io/badge/Architecture-Edge--AI%20Surveillance-0284c7?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00ffff?style=for-the-badge)
![React](https://img.shields.io/badge/React%2018-Vite-61DAFB?style=for-the-badge&logo=react)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)

Sentinel Grid is an autonomous, end-to-end AI video analytics platform built for high-security border CCTV and perimeter surveillance. It provides real-time multi-target detection, persistent tracking across camera sectors, virtual fence intrusion detection, automatic number plate recognition (ANPR), and a **Trust-Weighted Fusion Risk Engine** that generates human-interpretable risk scores (0–100) and natural language threat explanations.

> 📖 **Full System Documentation**: For the complete technical and non-technical handbook, see [DOCUMENTATION.md](file:///d:/Sentinel%20Grid/DOCUMENTATION.md).

---

## Key Features

1. **Simulated & Real Ingestion**: Ingests video from local `.mp4` files with continuous looping and frame rate throttling, identical to live RTSP streams. Swapping to a live camera feed is a one-line config change. Includes an automated synthetic CCTV generator fallback.
2. **YOLOv8 Object Perception**: Pretrained on COCO (`yolov8n.pt`), optimized for border security targets (`person`, `car`, `truck`, `bus`, `motorcycle`).
3. **Multi-Target Tracking**: ByteTrack integration via `supervision` maintaining persistent track IDs, spatial centroids, and motion trajectories.
4. **Virtual Polygon Fence & Spatial Analytics**: Shapely-powered polygon containment and vector analysis to detect boundary crossing, inbound/outbound breach direction, and zone dwell duration.
5. **Edge ANPR (License Plate Recognition)**: Automated vehicle crop, contrast enhancement (CLAHE + bilateral filtering), and EasyOCR alphanumeric plate extraction with regex filtering.
6. **Trust-Weighted Rule-Based Fusion Risk Engine**: Completely transparent, editable scoring (0–100) combining breach status, dwell time, group size, time-of-day, and detection confidence into a composite risk score and natural language narrative (e.g., *"Inbound crossing, group of 2 individuals, 23:41 hrs, 40s dwell time."*).
7. **Tactical Command Center Dashboard**: React + Vite UI with dark command-center aesthetics, live video tiles, real-time alert ticker via WebSocket, incident inspector modal with snapshots, and live weight adjustment sliders.
8. **Night-Vision Low-Light Enhancement**: Per-camera or global CLAHE (Contrast Limited Adaptive Histogram Equalization) low-light filter toggle.
9. **One-Command Deployment**: Fully containerized with Docker Compose.

---

## System Architecture

```mermaid
flowchart TB
    subgraph Ingestion ["1. Video Ingestion Layer"]
        V1["Cam 1: Perimeter (.mp4 / RTSP)"]
        V2["Cam 2: Checkpoint (.mp4 / RTSP)"]
        SYNTH["Synthetic Video Generator (Fallback)"]
    end

    subgraph Perception ["2. Perception & Enhancements"]
        CLAHE["Night Mode (CLAHE Low-Light Enhancer)"]
        YOLO["YOLOv8 Detector (Target COCO Classes)"]
        TRACK["ByteTrack (Supervision - Persistent IDs & Vectors)"]
    end

    subgraph Analytics ["3. Spatial & Semantic Analytics"]
        FENCE["Polygon Fence Engine (Shapely: Inbound/Outbound Breach & Dwell)"]
        ANPR["ANPR Engine (EasyOCR + Plate Pattern Filtering)"]
        GROUP["Group & Proximity Clustering"]
    end

    subgraph Fusion ["4. Trust-Weighted Fusion Engine"]
        CONFIG["config/fusion_weights.json"]
        RISK["Composite Risk Scorer (0-100)"]
        EXPLAIN["Natural Language Narrative Generator"]
    end

    subgraph Storage ["5. Persistence & Dispatch"]
        DB[("SQLite sentinel.db")]
        WS["FastAPI WebSocket Hub (/ws/live)"]
        REST["FastAPI REST API (/api/*)"]
    end

    subgraph Dashboard ["6. Tactical Command Center (React + Vite)"]
        HUD["Command Center HUD & Threat Status"]
        TILES["Live Annotated Camera Feeds (Canvas/JPEG Stream)"]
        ALERTS["Real-time Alert Ticker & Severity Badges"]
        DETAIL["Alert Detail Inspector (Snapshot, Narrative, Metrics)"]
        WEIGHTS["Live Fusion Weight Tuning Sliders"]
    end

    V1 --> CLAHE
    V2 --> CLAHE
    SYNTH -.-> CLAHE
    CLAHE --> YOLO
    YOLO --> TRACK
    TRACK --> FENCE
    TRACK --> ANPR
    TRACK --> GROUP
    FENCE --> RISK
    ANPR --> RISK
    GROUP --> RISK
    CONFIG --> RISK
    RISK --> EXPLAIN
    EXPLAIN --> DB
    EXPLAIN --> WS
    WS --> Dashboard
    REST --> Dashboard
```

---

## Module Map

The codebase directly mirrors the five pillars of the technical surveillance documentation:

| Folder / File | Architecture Pillar | Description |
| :--- | :--- | :--- |
| `backend/app/ingestion/video_source.py` | **Video Ingestion** | Reads `.mp4` or `rtsp://` streams at fixed FPS, continuous looping, and generates synthetic frames on demand. |
| `backend/app/detection/detector.py` | **Perception (Vision)** | YOLOv8 inference wrapper, COCO class filter, and CLAHE low-light enhancement filter. |
| `backend/app/tracking/tracker.py` | **Perception (Tracking)** | ByteTrack tracker via Supervision, tracks centroids, ground positions, and trajectory histories. |
| `backend/app/fence/polygon_fence.py` | **Contextual Analytics** | Shapely polygon intersection, inbound/outbound heading classification, and zone dwell timer. |
| `backend/app/anpr/plate_reader.py` | **Perception (ANPR)** | Vehicle bounding box cropping, bilateral filtering, and EasyOCR plate recognition with regex. |
| `backend/app/fusion/risk_engine.py` | **Trust-Weighted Fusion** | Calculates 0–100 composite risk score from weighted rules and builds natural language explanation strings. |
| `backend/app/storage/` | **Data Persistence** | SQLAlchemy SQLite models (`Track`, `BreachEvent`, `Alert`) and session management. |
| `backend/app/api/ws.py` & `routes.py` | **API & Streaming** | WebSocket frame broadcast and REST endpoints for camera status, alert history, and config updates. |
| `backend/app/pipeline.py` | **Orchestration** | Async per-camera worker loop linking perception, tracking, spatial analytics, fusion, and dispatch. |
| `frontend/src/` | **Command Center UI** | React + Vite dashboard with dark navy theme, live annotated canvas feeds, alert inspector, and weight sliders. |
| `config/` | **Configuration** | `cameras.json` (camera definitions & polygon coordinates) and `fusion_weights.json` (risk weights). |

---

## Quick Start Guide

### Option 1: Run with Docker Compose (Recommended)

Make sure Docker and Docker Compose are installed, then run from the project root:

```bash
docker compose up --build
```

- **Frontend Command Center**: [http://localhost:3000](http://localhost:3000)
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Live WebSocket Stream**: `ws://localhost:8000/ws/live`

---

### Option 2: Run Locally (Without Docker)

#### 1. Backend Setup
```bash
# Navigate to backend and create virtualenv
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Pre-generate sample test videos
python scripts/generate_sample_videos.py

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
# Open a new terminal in frontend/
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) (or the port shown in your terminal) to view the Command Center.

---

## How to Drop in Your Own Videos or RTSP Streams

### 1. Using Custom `.mp4` Video Files
1. Copy your `.mp4` video files into `backend/sample_videos/`:
   - e.g. `backend/sample_videos/my_border_clip.mp4`
2. Open `config/cameras.json` and set the `"source"` field to the relative path:
   ```json
   {
     "id": "cam_01",
     "name": "Perimeter Sector Alpha",
     "source": "sample_videos/my_border_clip.mp4",
     "fps": 15,
     "fence": {
       "name": "Buffer Zone Virtual Fence",
       "polygon": [[100, 300], [540, 300], [540, 460], [100, 460]],
       "inbound_direction": "down"
     }
   }
   ```
3. Restart the server or container. The video will stream and loop continuously.

### 2. Using Live RTSP Camera Streams
To connect to an actual IP camera or RTSP stream, simply update `"source"` to the RTSP URL in `config/cameras.json`:
```json
"source": "rtsp://admin:password@192.168.1.120:554/h264Preview_01_main"
```

---

## Trust-Weighted Fusion Risk Engine

The fusion engine calculates a **0–100 composite risk score** based on configurable weighted factors defined in `config/fusion_weights.json`:

```json
{
  "weights": {
    "zone_breach_inbound": 40,
    "zone_breach_outbound": 15,
    "dwell_time_per_10s": 8,
    "group_size_per_person": 6,
    "night_time_multiplier": 1.3,
    "low_confidence_penalty": -15
  },
  "alert_threshold": 55
}
```

- **Inbound Fence Breach**: High base threat (+40 pts)
- **Outbound Crossing**: Moderate threat (+15 pts)
- **Dwell Time**: Incremental points for lingering in restricted zones (+8 pts per 10s)
- **Group Density**: Points added for each additional companion (+6 pts/person)
- **Low-Light / Night Multiplier**: 1.3x multiplier applied during night operations
- **Low Confidence Penalty**: -15 pts penalty if object detection confidence < 0.50
- **Live Tuning**: Weights and the 55-point alert threshold can be adjusted in real time from the **"FUSION WEIGHTS"** button on the Command Center HUD.

---

## Simulated vs. Real Deployment Comparison

| Component | Hackathon MVP (Simulated) | Real-World Operational Deployment |
| :--- | :--- | :--- |
| **Video Ingestion** | Local `.mp4` looped at 15 FPS / Synthetic fallback | Hardened RTSP/ONVIF streams from PTZ & Thermal FLIR cameras |
| **Edge Hardware** | CPU container / standard laptop GPU | NVIDIA Jetson AGX Orin / edge servers running TensorRT FP16 |
| **Perception Model** | YOLOv8 Nano (`yolov8n.pt`) via PyTorch | Custom-trained YOLOv8 / YOLOv9 on infrared & border surveillance datasets |
| **ANPR Engine** | EasyOCR on cropped vehicle bounding box | Specialized dual-stage plate locator + high-speed LPR engine (e.g. TensorRT LPRNet) |
| **Identity & Privacy** | Face detection boxes only (no biometric matching) | Opt-in facial recognition with cryptographic audit trails (FRS is strictly opt-in) |
| **Network & Comms** | Local WebSockets over HTTP/WS | Secure WebSockets (WSS), MQTT telemetry, and MIL-STD tactical mesh links |
| **Storage** | SQLite local file (`sentinel.db`) | Distributed PostgreSQL / TimescaleDB with encrypted S3/MinIO snapshot retention |

---

## Autonomous Design Decisions & Notes

1. **Synthetic Video Fallback**: Built a built-in generator that produces simulated CCTV footage with moving pedestrian silhouettes, vehicle shapes, license plates, and timestamps if no `.mp4` files exist. This guarantees immediate zero-friction demo execution.
2. **EasyOCR Lazy Loading & Caching**: EasyOCR model loading is deferred and cached per track ID to prevent frame drop latency during live video processing.
3. **Corner-Bracket Tactical UI Styling**: Camera bounding boxes use high-visibility tactical corner brackets rather than plain solid rectangles for a high-tech command-center aesthetic.
4. **WebSocket Frame Throttling**: Live annotated video is compressed to quality 65 JPEG and broadcast at target camera FPS (~15 FPS), delivering fluid real-time monitoring over standard WebSockets.

---

## License & Acknowledgments
Built for **Smart India Hackathon 2026 (Problem Statement 26187)**.
Technologies: Ultralytics YOLOv8, Supervision ByteTrack, Shapely, EasyOCR, FastAPI, React, Vite, SQLite.
