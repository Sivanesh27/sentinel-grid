"""
SQLAlchemy models for Sentinel Grid surveillance database.
Stores tracks, virtual fence breach events, alerts, and telemetry logs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    track_id = Column(Integer, index=True)
    camera_id = Column(String(64), index=True)
    class_name = Column(String(32), index=True)
    confidence = Column(Float, default=0.0)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_dwell_time = Column(Float, default=0.0)
    max_risk_score = Column(Float, default=0.0)
    plate_number = Column(String(32), nullable=True)
    is_breached = Column(Boolean, default=False)
    inbound_breach = Column(Boolean, default=False)


class BreachEvent(Base):
    __tablename__ = "breach_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String(64), index=True)
    track_id = Column(Integer, index=True)
    fence_name = Column(String(128))
    direction = Column(String(32), default="inbound")  # inbound / outbound
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    position_x = Column(Float)
    position_y = Column(Float)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(String(64), unique=True, index=True)
    camera_id = Column(String(64), index=True)
    track_id = Column(Integer, index=True)
    class_name = Column(String(32), default="person")
    risk_score = Column(Float, index=True)
    severity = Column(String(32), index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    explanation = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    snapshot_base64 = Column(Text, nullable=True)
    details_json = Column(Text, nullable=True)
    acknowledged = Column(Boolean, default=False)
