# api/http_api.py
from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

from config import IcebergConfig
from governance.governance import GovernanceEnvelope
from simulator.simulator import IcebergSimulator
from simulator.cluster_runner import ClusterRunner
from telemetry.aggregator import TelemetryAggregator
from model.build_graph import build_graph

from domain.CallerState import CallerState
from domain.Intent import Intent
from domain.Emotion import Emotion


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------
class SimulateRequest(BaseModel):
    caller_id: str
    intent: str
    emotion: str
    node_id: str = "root"


class ClusterRequest(BaseModel):
    callers: int = 50
    steps: int = 12
    start_node: str = "root"


# ---------------------------------------------------------
# Bootstrap Iceberg
# ---------------------------------------------------------
cfg = IcebergConfig()

graph = build_graph()
telemetry = TelemetryAggregator(max_events=cfg.governance.max_telemetry_events)

# RL engines
ppo_router = None
marl_engine = None
staffing_rl = None

# Simulator + cluster
simulator = None
cluster = None

# Governance
gov = GovernanceEnvelope(graph, cfg.governance)


def initialize_engines():
    global ppo_router, marl_engine, staffing_rl, simulator, cluster

    from engines.rl_ppo import PPORouter
    from engines.rl_marl import IcebergMARL
    from engines.staffing_rl import StaffingOptimizerRL

    ppo_router = PPORouter(graph, graph.neighbors)
    marl_engine = IcebergMARL(graph, graph.queues, latent=None, priors=None)
    staffing_rl = StaffingOptimizerRL(graph, graph.queues, latent=None, priors=None)

    simulator = IcebergSimulator(
        graph=graph,
        ppo_router=ppo_router,
        marl_engine=marl_engine,
        staffing_rl=staffing_rl,
        telemetry=telemetry,
    )

    cluster = ClusterRunner(
        graph=graph,
        simulator=simulator,
        telemetry=telemetry,
        num_workers=cfg.cluster.num_workers,
    )


initialize_engines()


# ---------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------
app = FastAPI(title="Iceberg 3.x API", version="3.0")


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
@app.get("/governance")
def governance_gate():
    return gov.governance_gate()


@app.post("/simulate")
def simulate(req: SimulateRequest):
    intent = Intent[req.intent]
    emotion = Emotion[req.emotion]

    caller = CallerState(
        caller_id=req.caller_id,
        intent=intent,
        emotion=emotion,
        posterior={
            "billing": 0.25,
            "tech": 0.25,
            "fraud": 0.25,
            "general": 0.25,
        },
    )

    out = simulator.step(caller, req.node_id)
    return out


@app.post("/cluster")
def run_cluster(req: ClusterRequest):
    return cluster.run_cluster(
        num_callers=req.callers,
        steps=req.steps,
        start_node=req.start_node,
    )


@app.get("/telemetry")
def get_telemetry():
    return telemetry.dump()


@app.get("/replay/verify")
def verify_replay():
    return gov.verify_replay()


@app.get("/snapshot/{name}")
def verify_snapshot(name: str):
    return gov.verify_snapshot(name)