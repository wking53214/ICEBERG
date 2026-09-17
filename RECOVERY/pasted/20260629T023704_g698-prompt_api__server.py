# api/server.py
from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

# Engines
from engines.rl_ppo import PPORouter
from engines.rl_marl import IcebergMARL
from engines.staffing_rl import StaffingOptimizerRL
from engines.bayes_gpu import BayesianIntentEngineGPU

# Simulator
from sim.simulator import IcebergSimulator

# Replay
from replay.recorder import ReplayRecorder, ReplayEvent
from replay.ledger import ReplayLedger
from replay.snapshot import SnapshotManager
from replay.replay_runner import ReplayRunner
from replay.verifier import ReplayVerifier

# Telemetry
from telemetry.aggregator import TelemetryAggregator

# Domain
from domain.Intent import Intent
from domain.Emotion import Emotion

# Graph + Latent
from model.build_graph import build_graph
from latent.LatentPayload import LatentPayload


app = FastAPI(title="Iceberg 3.x API")


# ---------------------------------------------------------
# INITIALIZATION
# ---------------------------------------------------------
graph = build_graph()
latent = LatentPayload()
queues = graph.init_queues()

ppo = PPORouter(graph, graph.neighbors)
marl = IcebergMARL(graph, queues, latent, priors={})
staffing = StaffingOptimizerRL(graph, queues, latent, priors={})
bayes = BayesianIntentEngineGPU()

sim = IcebergSimulator(graph, queues, latent)

recorder = ReplayRecorder()
ledger = ReplayLedger()
snapshots = SnapshotManager()
verifier = ReplayVerifier(graph, queues)
replay_runner = ReplayRunner(sim, graph, latent, queues, ledger, recorder, snapshots)

telemetry = TelemetryAggregator()


# ---------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------
class SimRequest(BaseModel):
    caller_id: str
    intent: int
    emotion: int
    start_node: str


class TrainRequest(BaseModel):
    episodes: int


class ReplayRequest(BaseModel):
    snapshot: str | None = None


# ---------------------------------------------------------
# SIMULATION ENDPOINT
# ---------------------------------------------------------
@app.post("/api/v1/simulate/call")
def simulate_call(req: SimRequest):
    caller = sim.create_caller(
        caller_id=req.caller_id,
        intent=Intent(req.intent),
        emotion=Emotion(req.emotion),
    )

    # Bayesian update
    posterior = bayes.observe_single(
        posterior=caller.posterior,
        likelihoods=caller.likelihoods(),
        intents=list(caller.posterior.keys()),
    )

    caller.posterior = posterior

    # PPO routing
    next_node, idx, logp, value = ppo.choose_action(caller, req.start_node)
    rl_action = {"routing": next_node}

    # Staffing RL
    staffing_action = staffing.propose_staffing()

    # Run simulation step
    output = sim.step(caller, next_node)

    # Record event
    evt = ReplayEvent(
        timestamp=sim.timestamp(),
        caller_id=req.caller_id,
        node_id=next_node,
        queue_state=sim.queue_snapshot(),
        posterior=posterior,
        rl_action=rl_action,
        staffing_action=staffing_action,
        seeds=recorder.freeze_seeds(),
        structural_hash=recorder.structural_hash(graph),
    )
    recorder.record(evt)
    ledger.append(evt.__dict__)

    telemetry.log_event(evt.__dict__)

    return {
        "caller_id": req.caller_id,
        "next_node": next_node,
        "output": output,
        "posterior": posterior,
        "rl_action": rl_action,
        "staffing_action": staffing_action,
    }


# ---------------------------------------------------------
# TRAINING ENDPOINTS
# ---------------------------------------------------------
@app.post("/api/v1/train/router")
def train_router(req: TrainRequest):
    loss = 0.0
    for _ in range(req.episodes):
        batch = sim.generate_training_batch(ppo)
        loss = ppo.train_step(batch)
    return {"loss": loss}


@app.post("/api/v1/train/marl")
def train_marl(req: TrainRequest):
    loss = 0.0
    for _ in range(req.episodes):
        batch = sim.generate_marl_batch(marl)
        loss = marl.train_step(batch)
    return {"loss": loss}


@app.post("/api/v1/train/staffing")
def train_staffing(req: TrainRequest):
    loss = 0.0
    for _ in range(req.episodes):
        batch = sim.generate_staffing_batch(staffing)
        loss = staffing.train_step(batch)
    return {"loss": loss}


# ---------------------------------------------------------
# REPLAY ENDPOINT
# ---------------------------------------------------------
@app.post("/api/v1/replay")
def replay(req: ReplayRequest):
    events = replay_runner.replay(req.snapshot)
    return {"events": events}


# ---------------------------------------------------------
# SNAPSHOT ENDPOINTS
# ---------------------------------------------------------
@app.get("/api/v1/snapshots")
def list_snapshots():
    return {"snapshots": snapshots.list_snapshots()}


@app.post("/api/v1/snapshots/save/{name}")
def save_snapshot(name: str):
    data = {
        "queues": sim.queue_snapshot(),
        "latent": latent.to_dict(),
        "structural_hash": recorder.structural_hash(graph),
    }
    snapshots.save_snapshot(name, data)
    return {"saved": name}


# ---------------------------------------------------------
# TELEMETRY ENDPOINT
# ---------------------------------------------------------
@app.get("/api/v1/telemetry")
def get_telemetry():
    return telemetry.dump()