"""
WebSocket Connection Manager and Broadcaster for live camera frames and security alerts.
"""

import json
import asyncio
from typing import List, Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect


class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accepts and registers incoming client WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        print(f"[WebSocket] Client connected. Total active: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Unregisters disconnected client."""
        async with self._lock:
            self.active_connections.discard(websocket)
        print(f"[WebSocket] Client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast_json(self, data: Dict[str, Any]):
        """Broadcasts JSON payload to all connected clients."""
        if not self.active_connections:
            return

        message = json.dumps(data)
        dead_connections = set()

        async with self._lock:
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.add(connection)

        if dead_connections:
            async with self._lock:
                for dead in dead_connections:
                    self.active_connections.discard(dead)

    async def broadcast_frame(self, camera_id: str, frame_base64: str, fps: float, active_tracks: int):
        """Sends a live annotated video frame update."""
        payload = {
            "type": "frame",
            "camera_id": camera_id,
            "image": frame_base64,
            "fps": round(fps, 1),
            "active_tracks": active_tracks,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast_json(payload)

    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Sends a high-priority security alert."""
        payload = {
            "type": "alert",
            "data": alert_data
        }
        await self.broadcast_json(payload)


ws_manager = WebSocketManager()
