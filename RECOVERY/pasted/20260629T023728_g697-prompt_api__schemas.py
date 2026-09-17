# api/schemas.py
from __future__ import annotations
from pydantic import BaseModel
from typing import Dict, Any, Optional


# ---------------------------------------------------------
# SIMULATION REQUESTS
# ---------------------------------------------------------
class SimRequest(BaseModel):
    caller_id: str
    intent: int
    emotion: int
    start_node: str


class SimResponse(BaseModel):
    caller_id: str
    next_node: str
    output: Dict[str, Any]
    posterior: Dict[str, float]
    rl_action: Dict[str, Any]
    staffing_action: Dict[str, float]


# ---------------------------------------------------------
# TRAINING REQUESTS
# ---------------------------------------------------------
class TrainRequest(BaseModel):
    episodes: int


class TrainResponse(BaseModel):
    loss: float


# ---------------------------------------------------------
# REPLAY REQUESTS
# ---------------------------------------------------------
class ReplayRequest(BaseModel):
    snapshot: Optional[str] = None


class ReplayResponse(BaseModel):
    events: list


# ---------------------------------------------------------
# SNAPSHOT MODELS
# ---------------------------------------------------------
class SnapshotSaveResponse(BaseModel):
    saved: str


class SnapshotListResponse(BaseModel):
    snapshots: list


# ---------------------------------------------------------
# TELEMETRY MODELS
# ---------------------------------------------------------
class TelemetryResponse(BaseModel):
    events: list