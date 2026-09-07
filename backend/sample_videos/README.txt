========================================================================
SENTINEL GRID — SAMPLE VIDEOS REPOSITORY
========================================================================

Place any standard .mp4 video files in this folder to simulate live CCTV camera feeds.

Default Video Filenames (referenced in config/cameras.json):
1. perimeter_cam_01.mp4  -> Perimeter Sector Alpha (Border fence line)
2. checkpoint_cam_02.mp4 -> Checkpoint Bravo (Vehicle/Gate inspection line)

Synthetic Fallback:
If you run Sentinel Grid without providing your own video files, the system 
automatically generates high-quality synthetic CCTV feeds (with moving pedestrians, 
vehicles, night-vision overlays, and virtual fence intersections) so the full 
pipeline is immediately testable and runnable!

Supported Formats:
- Codec: H.264 / AVC or MPEG-4
- Container: .mp4, .avi, .mkv
- Frame rate: 15 to 30 FPS recommended
- Resolution: 640x480, 1280x720, or 1920x1080

To use real RTSP streams:
Edit config/cameras.json and set the "source" field to your RTSP URL, e.g.:
"source": "rtsp://admin:password@192.168.1.100:554/stream1"
========================================================================
