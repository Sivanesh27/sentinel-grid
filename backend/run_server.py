"""
Direct Python entry point for running Sentinel Grid backend on cloud platforms (Render, Railway, Fly.io, etc.).
Reads the PORT environment variable injected by the cloud host and starts Uvicorn.
"""

import os
import uvicorn

if __name__ == "__main__":
    # Render and Railway inject PORT dynamically (default: 10000 on Render)
    port_env = os.environ.get("PORT", "10000")
    try:
        port = int(port_env)
    except ValueError:
        port = 10000

    print(f"============================================================")
    print(f"  SENTINEL GRID PROD SERVER STARTING ON 0.0.0.0:{port}")
    print(f"============================================================")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        timeout_keep_alive=65
    )
