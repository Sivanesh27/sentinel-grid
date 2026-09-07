"""
End-to-End API and Pipeline Integration Tests for Sentinel Grid.
Tests camera management, night mode, dynamic drag-and-drop fence updates, config, and alerts.
"""

import os
import sys
import time
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app


def test_api_endpoints_with_lifespan():
    with TestClient(app) as client:
        # 1. Root (Serves Frontend SPA HTML or JSON info)
        root_res = client.get("/")
        assert root_res.status_code == 200
        assert "html" in root_res.headers.get("content-type", "") or "Sentinel Grid" in root_res.text

        # 2. Health (Poll briefly for background pipeline startup)
        health_data = {}
        for _ in range(25):
            health_res = client.get("/api/health")
            assert health_res.status_code == 200
            health_data = health_res.json()
            if health_data.get("active_cameras", 0) >= 1:
                break
            time.sleep(0.1)

        assert health_data["status"] == "online"
        assert health_data["active_cameras"] >= 1

        # 3. Cameras
        cam_res = client.get("/api/cameras")
        assert cam_res.status_code == 200
        cameras = cam_res.json()
        assert len(cameras) >= 1
        cam_id = cameras[0]["id"]

        # 4. Night Mode Toggle
        toggle_res = client.post(f"/api/cameras/{cam_id}/night_mode", json={"enabled": True})
        assert toggle_res.status_code == 200
        assert toggle_res.json()["night_mode"] is True

        toggle_off = client.post(f"/api/cameras/{cam_id}/night_mode", json={"enabled": False})
        assert toggle_off.status_code == 200
        assert toggle_off.json()["night_mode"] is False

        # 5. Live Virtual Fence Drag & Drop Update API
        new_poly = [[110, 310], [530, 310], [530, 450], [110, 450]]
        fence_res = client.post(f"/api/cameras/{cam_id}/fence", json={
            "polygon": new_poly,
            "name": "Custom Dragged Fence",
            "inbound_direction": "down"
        })
        assert fence_res.status_code == 200
        fence_data = fence_res.json()
        assert fence_data["status"] == "success"
        assert fence_data["fence"]["name"] == "Custom Dragged Fence"
        assert len(fence_data["fence"]["polygon"]) == 4

        # 6. Config get and update
        config_res = client.get("/api/config")
        assert config_res.status_code == 200
        config_data = config_res.json()
        assert "weights" in config_data
        assert "alert_threshold" in config_data

        update_res = client.post("/api/config", json={
            "weights": config_data["weights"],
            "alert_threshold": 50.0
        })
        assert update_res.status_code == 200
        assert update_res.json()["alert_threshold"] == 50.0

        # 7. Alerts & Tracks query
        alerts_res = client.get("/api/alerts?limit=10")
        assert alerts_res.status_code == 200
        assert isinstance(alerts_res.json(), list)

        tracks_res = client.get("/api/tracks?limit=10")
        assert tracks_res.status_code == 200
        assert isinstance(tracks_res.json(), list)
