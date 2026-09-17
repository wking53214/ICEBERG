# replay/replay_runner.py
from __future__ import annotations
import json
import torch
import random
import numpy as np
from typing import Dict, Any, List


class ReplayRunner:
    """
    Deterministic replay engine for Iceberg 3.x.
    Replays events from the ledger and reconstructs caller trajectories.
    """

    def __init__(self, simulator, graph, latent, queues, ledger, recorder, snapshot_mgr):
        self.sim = simulator
        self.graph = graph
        self.latent = latent
        self.queues = queues
        self.ledger = ledger
        self.recorder = recorder
        self.snapshot_mgr = snapshot_mgr

    # ---------------------------------------------------------
    # RNG RESTORATION
    # ---------------------------------------------------------
    def restore_seeds(self, seeds: Dict[str, int]):
        """
        Restore Python, NumPy, and Torch RNG states.
        """
        random.seed(seeds["python"])
        np.random.seed(seeds["numpy"])
        torch.manual_seed(seeds["torch"])

    # ---------------------------------------------------------
    # REPLAY EXECUTION
    # ---------------------------------------------------------
    def replay(self, start_snapshot: str = None) -> List[Dict[str, Any]]:
        """
        Replay the entire ledger from a snapshot (optional).
        Returns a list of reconstructed events.
        """

        # Load snapshot if provided
        if start_snapshot:
            snap = self.snapshot_mgr.load_snapshot(start_snapshot)
            self._restore_snapshot(snap)

        events = self.ledger.read_all()
        reconstructed = []

        for evt in events:
            # Restore RNG state for this event
            self.restore_seeds(evt["seeds"])

            # Reconstruct caller state
            caller = self.sim.reconstruct_caller(evt["caller_id"], evt["posterior"])

            # Reconstruct queue state
            self._restore_queue_state(evt["queue_state"])

            # Apply RL action
            self._apply_rl_action(caller, evt["rl_action"])

            # Apply staffing action
            self._apply_staffing(evt["staffing_action"])

            # Run one simulation step
            out = self.sim.step(caller, evt["node_id"])

            reconstructed.append({
                "caller_id": evt["caller_id"],
                "node_id": evt["node_id"],
                "output": out,
                "posterior": evt["posterior"],
                "rl_action": evt["rl_action"],
                "staffing_action": evt["staffing_action"],
                "structural_hash": evt["structural_hash"],
            })

        return reconstructed

    # ---------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------
    def _restore_snapshot(self, snap: Dict[str, Any]):
        """
        Restore queues, caller states, latent payload, structural hash.
        """
        # Restore queues
        for qname, qstate in snap["queues"].items():
            q = self.queues[qname]
            q.active_calls = qstate["active_calls"]
            q.staffing = qstate["staffing"]
            q.target_service_level = qstate["target_service_level"]
            q.abandonment_rate = qstate["abandonment_rate"]

        # Restore latent payload
        self.latent.load_from_dict(snap["latent"])

        # Restore structural hash
        self.graph.structural_hash = snap["structural_hash"]

    def _restore_queue_state(self, state: Dict[str, Any]):
        for qname, qstate in state.items():
            q = self.queues[qname]
            q.active_calls = qstate["active_calls"]
            q.staffing = qstate["staffing"]
            q.target_service_level = qstate["target_service_level"]
            q.abandonment_rate = qstate["abandonment_rate"]

    def _apply_rl_action(self, caller, action: Dict[str, Any]):
        """
        Apply routing or other RL actions.
        """
        if "routing" in action:
            caller.next_node = action["routing"]

    def _apply_staffing(self, action: Dict[str, Any]):
        """
        Apply staffing deltas.
        """
        for qname, delta in action.items():
            self.queues[qname].staffing += delta