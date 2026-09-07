"""
Virtual Fence and Zone Breach Detection module using Shapely.
Analyzes trajectory intersections with user-defined polygon zones and calculates
breach status, inbound (critical) vs outbound (safe return) crossing direction, and zone dwell times.
"""

from typing import List, Tuple, Dict, Optional
import numpy as np
from shapely.geometry import Point, Polygon
from app.tracking.tracker import TrackState


class PolygonFence:
    def __init__(self, name: str, polygon_points: List[List[float]], inbound_direction: str = "down"):
        """
        Initializes virtual fence polygon.
        polygon_points: list of [x, y] coordinates defining the polygon perimeter.
        inbound_direction: 'down', 'up', 'left', 'right' or general heading.
        """
        self.name = name
        self.inbound_direction = inbound_direction.lower()
        self.points: List[Tuple[float, float]] = []
        self.polygon: Optional[Polygon] = None
        self.set_polygon(polygon_points)
        
        # Track entry timestamps per track ID: {track_id: entry_timestamp}
        self.zone_entries: Dict[int, float] = {}

    def set_polygon(self, polygon_points: List[List[float]], name: Optional[str] = None, inbound_direction: Optional[str] = None):
        """Updates polygon coordinates dynamically in real-time."""
        self.points = [tuple(p) for p in polygon_points]
        if len(self.points) < 3:
            raise ValueError(f"Polygon must have at least 3 points, got {len(self.points)}")
        self.polygon = Polygon(self.points)
        if name:
            self.name = name
        if inbound_direction:
            self.inbound_direction = inbound_direction.lower()

    def check_track(self, track: TrackState, current_time: float) -> Tuple[bool, str, bool]:
        """
        Evaluates a track's spatial relationship to the polygon fence.
        Returns:
            (is_breach, direction, is_inside)
            - is_breach: True if currently inside restricted zone or active breach
            - direction: "inbound" (crossing into restricted zone) or "outbound" (retreated back to safe side)
            - is_inside: True if current position is within polygon
        """
        curr_point = Point(track.bottom_center[0], track.bottom_center[1])
        centroid_point = Point(track.centroid[0], track.centroid[1])
        
        # Target is inside if either ground contact point (feet/wheels) or centroid is in polygon
        is_currently_inside = (
            self.polygon.contains(curr_point) or 
            self.polygon.touches(curr_point) or
            self.polygon.contains(centroid_point)
        )

        direction = track.breach_direction

        # Handle State Transitions
        if is_currently_inside:
            if not track.is_in_zone:
                # Newly crossed into restricted sector
                self.zone_entries[track.track_id] = current_time
                track.is_in_zone = True
                track.is_breached = True
                direction = "inbound"
                track.breach_direction = "inbound"
            
            entry_time = self.zone_entries.get(track.track_id, current_time)
            track.zone_dwell_time = max(0.1, current_time - entry_time)
            is_breach = True
        else:
            if track.is_in_zone:
                # Target just moved back out across the fence to the safe side
                track.is_in_zone = False
                direction = "outbound"
                track.breach_direction = "outbound"
                if track.track_id in self.zone_entries:
                    del self.zone_entries[track.track_id]
            
            # If target has exited to safe side, breach is deactivated
            is_breach = False

        # If trajectory exists, double-check motion vector
        if len(track.trajectory) >= 2:
            past_points = [(p[0], p[1]) for p in track.trajectory[-8:]]
            first_p = past_points[0]
            last_p = past_points[-1]
            dx = last_p[0] - first_p[0]
            dy = last_p[1] - first_p[1]

            start_point = Point(first_p[0], first_p[1])
            start_inside = self.polygon.contains(start_point)

            if not start_inside and is_currently_inside:
                direction = "inbound"
                track.breach_direction = "inbound"
                is_breach = True
            elif start_inside and not is_currently_inside:
                direction = "outbound"
                track.breach_direction = "outbound"
                is_breach = False

        return is_breach, direction, is_currently_inside

    def _determine_direction(self, dx: float, dy: float, default: str = "inbound") -> str:
        """Determines if motion vector corresponds to inbound or outbound breach."""
        if self.inbound_direction == "down":
            return "inbound" if dy >= 0 else "outbound"
        elif self.inbound_direction == "up":
            return "inbound" if dy <= 0 else "outbound"
        elif self.inbound_direction == "right":
            return "inbound" if dx >= 0 else "outbound"
        elif self.inbound_direction == "left":
            return "inbound" if dx <= 0 else "outbound"
        return default
