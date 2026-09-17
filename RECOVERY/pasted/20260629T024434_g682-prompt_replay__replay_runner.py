# replay/replay_runner.py
from __future__ import annotations
import json
import random
import numpy as np
import torch
from typing import Dict, Any, List

from replay.ledger import ReplayLedger
from replay.snapshot import SnapshotManager
from domain.CallerState import CallerState, DynamicState
from latent.LatentPayload import LatentPayload


class ReplayRunner:
    """
    Deterministic replay engine for Iceberg 3.x.
    Reconstructs full simulations from the ledger.
    """

    def __init__(self, graph, simulator, ledger_path="replay_ledger.jsonl"):
        self.graph = graph
        self.simulator = simulator
        self.ledger = ReplayLedger(ledger_path)
        self.snapshots = SnapshotManager()

    # ---------------------------------------------------------
    # RNG RESTORATION
    # ---------------------------------------------------------
    def restore_seeds(self, seeds: Dict[str, int]):
        """
        Restore Python, NumPy, and Torch RNG seeds.
        """
        random.seed(seeds["python"])
        np.random.seed(seeds["numpy"])
        torch.manual_seed(seeds["torch"])

    # ---------------------------------------------------------
    # CALLER RECONSTRUCTION
    # ---------------------------------------------------------
    def reconstruct_caller(self, evt: Dict[str, Any]) -> CallerState:
        """
        Rebuild caller state from event snapshot.
        """
        caller_id = evt["caller_id"]
        posterior = evt["posterior"]

        # Intent + emotion come from posterior keys or event metadata
        intent_val = max(posterior, key=posterior.get)
        emotion_val = 0  # default; emotion drift is handled by latent

        caller = CallerState(
            caller_id=caller_id,
            intent=self.simulator.graph.intent_enum(intent_val),
            emotion=self.simulator.graph.emotion_enum(emotion_val),
            posterior=posterior,
        )

        # Restore dynamic state
        caller.dynamic = DynamicState(
            perceived_wait=evt["queue_state"].get("perceived_wait", 0.0),
            frustration=evt["queue_state"].get("frustration", 0.0),
        )

        return caller

    # ---------------------------------------------------------
    # QUEUE RECONSTRUCTION
    # ---------------------------------------------------------
    def reconstruct_queues(self, evt: Dict[str, Any]):
        """
        Restore queue metrics from event snapshot.
        """
        for qname, qstate in evt["queue_state"].items():
            if qname in self.graph.queues:
                q = self.graph.queues[qname]
                q.active_calls = qstate.get("active_calls", q.active_calls)
                q.staffing = qstate.get("staffing", q.staffing)
                q.target_service_level = qstate.get("target_service_level", q.target_service_level)
                q.abandonment_rate = qstate.get("abandonment_rate", q.abandonment_rate)

    # ---------------------------------------------------------
    # LATENT RECONSTRUCTION
    # ---------------------------------------------------------
    def reconstruct_latent(self, evt: Dict[str, Any]) -> LatentPayload:
        latent = LatentPayload()
        if "latent" in evt:
            latent.load_from_dict(evt["latent"])
        return latent

    # ---------------------------------------------------------
    # FULL REPLAY
    # ---------------------------------------------------------
    def replay(self) -> List[Dict[str, Any]]:
        """
        Replay the entire ledger deterministically.
        Returns list of reconstructed simulation steps.
        """
        events = self.ledger.read_all()
        reconstructed = []

        for evt in events:
            # Restore RNG seeds
            self.restore_seeds(evt["seeds"])

            # Rebuild caller
            caller = self.reconstruct_caller(evt)

            # Rebuild queues
            self.reconstruct_queues(evt)

            # Rebuild latent payload
            latent = self.reconstruct_latent(evt)

            # Run the simulator step deterministically
            output = self.simulator.step(caller, evt["node_id"])

            reconstructed.append({
                "caller_id": caller.caller_id,
                "node_id": evt["node_id"],
                "output": output,
                "rl_action": evt["rl_action"],
                "staffing_action": evt["staffing_action"],
                "latent": latent.to_dict(),
                "structural_hash": evt["structural_hash"],
            })

        return reconstructed

    # ---------------------------------------------------------
    # SNAPSHOT REPLAY
    # ---------------------------------------------------------
    def replay_from_snapshot(self, name: str) -> Dict[str, Any]:
        """
        Replay starting from a saved snapshot.
        """
        snap = self.snapshots.load_snapshot(name)

        # Restore seeds
        self.restore_seeds(snap["seeds"])

        # Rebuild caller
        caller = self.reconstruct_caller(snap)

        # Rebuild queues
        self.reconstruct_queues(snap)

        # Rebuild latent
        latent = self.reconstruct_latent(snap)

        # Run one deterministic step
        output = self.simulator.step(caller, snap["node_id"])

        return {
            "caller_id": caller.caller_id,
            "node_id": snap["node_id"],
            "output": output,
            "latent": latent.to_dict(),
            "structural_hash": snap["structural_hash"],
        }