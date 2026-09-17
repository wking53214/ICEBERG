# api/http_api.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

from governance.GovernanceEnvelope import GovernanceEnvelope
from cluster.ClusterRunner import ClusterRunner
from replay.ReplayRunner import ReplayRunner
from replay.SnapshotManager import SnapshotManager
from telemetry.TelemetryAggregator import TelemetryAggregator


class StepRequest(BaseModel):
    caller_id: str
    intent: str
    emotion: str
    node: str


class BatchItem(BaseModel):
    intent: int
    emotion: int
    start_node: str


class BatchRequest(BaseModel):
    steps: int
    batch: List[BatchItem]


class SnapshotRequest(BaseModel):
    name: str
    caller_id: str
    node: str


class ReplayRequest(BaseModel):
    ledger: str
    snapshot: str | None = None


class VerifyRequest(BaseModel):
    ledger: str


class SnapshotVerifyRequest(BaseModel):
    name: str


def build_api(graph, simulator, ppo, marl, staffing, replay_recorder):
    app = FastAPI(title="Iceberg 3.x API")

    telemetry = TelemetryAggregator()
    governance = GovernanceEnvelope(graph, telemetry)
    cluster = ClusterRunner(simulator, ppo, marl, staffing, telemetry, replay_recorder)
    replay_runner = ReplayRunner(graph, simulator)
    snapshots = SnapshotManager()

    # ---------------------------------------------------------
    # SIMULATION STEP
    # ---------------------------------------------------------
    @app.post("/step")
    def step(req: StepRequest):
        from domain.CallerState import CallerState
        from domain.Intent import Intent
        from domain.Emotion import Emotion

        caller = CallerState(
            caller_id=req.caller_id,
            intent=Intent.from_str(req.intent),
            emotion=Emotion.from_str(req.emotion),
            posterior={"p": 1.0},
        )

        try:
            out = governance.wrap_step(simulator, caller, req.node)
            return out
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ---------------------------------------------------------
    # CLUSTER BATCH
    # ---------------------------------------------------------
    @app.post("/cluster/run")
    def cluster_run(req: BatchRequest):
        batch = [
            {
                "intent": item.intent,
                "emotion": item.emotion,
                "start_node": item.start_node,
            }
            for item in req.batch
        ]

        try:
            out = governance.wrap_cluster_batch(cluster, batch, req.steps)
            return out
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ---------------------------------------------------------
    # TELEMETRY
    # ---------------------------------------------------------
    @app.get("/telemetry")
    def get_telemetry():
        return telemetry.snapshot()

    # ---------------------------------------------------------
    # SNAPSHOT SAVE
    # ---------------------------------------------------------
    @app.post("/snapshot/save")
    def snapshot_save(req: SnapshotRequest):
        from domain.CallerState import CallerState
        from domain.Intent import Intent
        from domain.Emotion import Emotion

        caller = CallerState(
            caller_id=req.caller_id,
            intent=Intent.from_str("billing"),  # placeholder
            emotion=Emotion.from_str("neutral"),
            posterior={"p": 1.0},
        )

        structural_hash = governance.current_hash()

        snap = snapshots.save(
            name=req.name,
            caller=caller,
            node_id=req.node,
            latent=simulator.latent,
            queues=graph.queues,
            structural_hash=structural_hash,
        )
        return snap

    # ---------------------------------------------------------
    # SNAPSHOT LOAD
    # ---------------------------------------------------------
    @app.get("/snapshot/load/{name}")
    def snapshot_load(name: str):
        try:
            return snapshots.load(name)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Snapshot not found")

    # ---------------------------------------------------------
    # SNAPSHOT VERIFY
    # ---------------------------------------------------------
    @app.post("/snapshot/verify")
    def snapshot_verify(req: SnapshotVerifyRequest):
        snap = snapshots.load(req.name)
        return snapshots.verify(snap, graph)

    # ---------------------------------------------------------
    # REPLAY RUN
    # ---------------------------------------------------------
    @app.post("/replay/run")
    def replay_run(req: ReplayRequest):
        try:
            return replay_runner.run(req.ledger, req.snapshot)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ---------------------------------------------------------
    # REPLAY VERIFY
    # ---------------------------------------------------------
    @app.post("/replay/verify")
    def replay_verify(req: VerifyRequest):
        try:
            return replay_runner.verifier.verify(req.ledger)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app