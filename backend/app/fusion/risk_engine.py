"""
Trust-Weighted Fusion Risk Engine for Sentinel Grid.
Calculates transparent, explainable composite risk scores (0-100) per tracked target:
- Inbound Crossing: Critical / Very High Threat (85 - 100)
- Outbound / Return to Safe Side: Safe / Low Threat (15 - 30, logged silently to SQLite)
"""

import os
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from app.tracking.tracker import TrackState


@dataclass
class RiskAssessment:
    track_id: int
    risk_score: float
    is_alert: bool
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    explanation: str
    factor_breakdown: Dict[str, Any]
    timestamp: datetime


class RiskEngine:
    DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../config/fusion_weights.json"))

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.weights = {
            "zone_breach_inbound": 85.0,
            "zone_breach_outbound": 20.0,
            "dwell_time_per_10s": 10.0,
            "group_size_per_person": 8.0,
            "night_time_multiplier": 1.25,
            "low_confidence_penalty": -10.0
        }
        self.alert_threshold = 50.0
        self.load_config()

    def load_config(self):
        """Loads or reloads fusion weights from config file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.weights.update(data.get("weights", {}))
                    self.alert_threshold = float(data.get("alert_threshold", 50.0))
            except Exception as e:
                print(f"[RiskEngine] Error reading weights config: {e}. Using defaults.")

    def save_config(self, weights: Dict[str, float], alert_threshold: float):
        """Saves updated weights back to config file."""
        self.weights.update(weights)
        self.alert_threshold = float(alert_threshold)
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({
                    "weights": self.weights,
                    "alert_threshold": self.alert_threshold
                }, f, indent=2)
        except Exception as e:
            print(f"[RiskEngine] Failed to save config: {e}")

    def evaluate_track(
        self,
        track: TrackState,
        nearby_group_size: int = 1,
        is_night_time: bool = False,
        reference_time: Optional[datetime] = None
    ) -> RiskAssessment:
        """
        Calculates composite risk score (0-100) and natural language explanation.
        """
        now = reference_time or datetime.now()
        breakdown = {}
        base_score = 0.0

        # 1. Breach Factor (Directional distinction)
        breach_pts = 0.0
        breach_desc = "No fence breach"
        
        if track.is_in_zone or (track.is_breached and track.breach_direction == "inbound"):
            # INBOUND CROSSING -> CRITICAL / VERY HIGH
            breach_pts = self.weights.get("zone_breach_inbound", 85.0)
            breach_desc = "CRITICAL INBOUND BREACH: Intrusion past virtual perimeter"
        elif track.breach_direction == "outbound" and not track.is_in_zone:
            # OUTBOUND / RETREAT TO SAFE SIDE -> LOW / SAFE (Logged silently)
            breach_pts = self.weights.get("zone_breach_outbound", 20.0)
            breach_desc = "Target retreated back to safe perimeter side"
        elif track.is_breached:
            breach_pts = self.weights.get("zone_breach_inbound", 85.0)
            breach_desc = "Perimeter intrusion detected"

        base_score += breach_pts
        breakdown["zone_breach_points"] = round(breach_pts, 1)

        # 2. Dwell Time Factor (only applied if actively inside restricted zone)
        effective_dwell = track.zone_dwell_time if track.is_in_zone else 0.0
        dwell_intervals = min(4.0, effective_dwell / 5.0)
        dwell_pts = dwell_intervals * (self.weights.get("dwell_time_per_10s", 10.0) / 2.0)
        base_score += dwell_pts
        breakdown["dwell_time_points"] = round(dwell_pts, 1)
        breakdown["dwell_seconds"] = round(effective_dwell, 1)

        # 3. Group Size Factor
        group_count = max(1, nearby_group_size)
        group_pts = (group_count - 1) * self.weights.get("group_size_per_person", 8.0)
        base_score += group_pts
        breakdown["group_size"] = group_count
        breakdown["group_size_points"] = round(group_pts, 1)

        # 4. Low Confidence Penalty
        conf_pts = 0.0
        if track.confidence < 0.45:
            conf_pts = self.weights.get("low_confidence_penalty", -10.0)
            base_score += conf_pts
        breakdown["confidence"] = round(track.confidence, 2)
        breakdown["confidence_adjustment"] = round(conf_pts, 1)

        # 5. Night Time Multiplier (applied to inbound threats)
        night_mult = self.weights.get("night_time_multiplier", 1.25) if is_night_time and (track.is_in_zone or track.breach_direction == "inbound") else 1.0
        final_score = base_score * night_mult
        breakdown["night_multiplier"] = night_mult
        breakdown["is_night_time"] = is_night_time

        # 6. ANPR / Vehicle
        if track.plate_number:
            breakdown["plate_number"] = track.plate_number
            final_score += 5.0

        # Clamp composite risk score between 0 and 100
        final_score = max(0.0, min(100.0, final_score))
        breakdown["final_risk_score"] = round(final_score, 1)

        # Determine Severity Level
        if final_score >= 80.0:
            severity = "CRITICAL"
        elif final_score >= 55.0:
            severity = "HIGH"
        elif final_score >= 35.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Generate Narrative
        explanation_parts = []
        if track.is_in_zone or (track.is_breached and track.breach_direction == "inbound"):
            explanation_parts.append(f"{breach_desc}")
        elif track.breach_direction == "outbound" and not track.is_in_zone:
            explanation_parts.append("Target returned back across boundary to safe zone (Normal)")
        else:
            explanation_parts.append(f"Target movement detected ({track.class_name})")

        if group_count > 1:
            explanation_parts.append(f"group of {group_count} individuals")
        else:
            explanation_parts.append(f"single {track.class_name}")

        time_str = now.strftime("%H:%M hrs")
        explanation_parts.append(f"{time_str}")

        if effective_dwell >= 2.0:
            explanation_parts.append(f"{int(effective_dwell)}s dwell time in restricted sector")

        if track.plate_number:
            explanation_parts.append(f"Vehicle Plate [{track.plate_number}]")

        if is_night_time and (track.is_in_zone or track.breach_direction == "inbound"):
            explanation_parts.append("night-vision sector")

        explanation = ", ".join(explanation_parts) + "."
        is_alert = final_score >= self.alert_threshold

        return RiskAssessment(
            track_id=track.track_id,
            risk_score=round(final_score, 1),
            is_alert=is_alert,
            severity=severity,
            explanation=explanation,
            factor_breakdown=breakdown,
            timestamp=now
        )
