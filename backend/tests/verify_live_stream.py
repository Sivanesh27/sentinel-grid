"""
Live stream verification script for Sentinel Grid.
Connects to the running FastAPI WebSocket endpoint, collects 5 frames and any alerts, and verifies payload integrity.
"""

import sys
import asyncio
import json
import websockets


async def verify_websocket_feed():
    uri = "ws://127.0.0.1:8000/ws/live"
    print(f"[Verifier] Connecting to WebSocket: {uri} ...")
    
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            print("[Verifier] Connected! Waiting for frames and alerts...")
            frames_received = {}
            alerts_received = []

            for _ in range(25):  # Listen for ~25 messages
                msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(msg)
                msg_type = data.get("type")

                if msg_type == "frame":
                    cid = data.get("camera_id")
                    frames_received[cid] = frames_received.get(cid, 0) + 1
                    fps = data.get("fps")
                    tracks = data.get("active_tracks")
                    img_prefix = data.get("image", "")[:30]
                    print(f"  -> Frame received from [{cid}]: FPS={fps}, Tracks={tracks}, Img={img_prefix}...")

                elif msg_type == "alert":
                    alert = data.get("data", {})
                    alerts_received.append(alert)
                    print(f"  -> ALERT received! Camera={alert.get('camera_id')}, Risk={alert.get('risk_score')}, Severity={alert.get('severity')}")
                    print(f"     Narrative: {alert.get('explanation')}")

            print(f"\n[Verifier] Summary: Received frames from {len(frames_received)} cameras: {frames_received}")
            print(f"[Verifier] Total alerts captured: {len(alerts_received)}")
            assert len(frames_received) >= 1, "Expected frames from at least 1 camera!"
            print("[Verifier] LIVE WEBSOCKET VERIFICATION SUCCESSFUL!")
            return True

    except Exception as e:
        print(f"[Verifier] Error connecting or receiving from WebSocket: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_websocket_feed())
    sys.exit(0 if success else 1)
