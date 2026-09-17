# replay/ReplayRunner.py
from __future__ import annotations
import json
from typing import Dict, Any, List

from replay.SnapshotManager import SnapshotManager
from replay.ReplayVerifier import ReplayVerifier
from domain.CallerState import CallerState
from domain.Intent import Intent
from domain.Emotion import Emotion


class ReplayRunner:
    """
    Full ledger replay reconstruction engine for Iceberg 3.x.
    Uses:
      - simulator
      - graph
      - SnapshotManager
      - ReplayVerifier
    """

    def __init__(self, graph, simulator, snapshot_dir: str = "snapshots"):
        self.graph = graph
        self.simulator = simulator
        self.snapshots = SnapshotManager(directory=snapshot_dir)
        self.verifier = ReplayVerifier(graph, simulator)

    # ---------------------------------------------------------
    # LEDGER LOADING
    # ---------------------------------------------------------
    def load_ledger(self, path: str) -> List[Dict[str, Any]]:
        events = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                events.append(json.loads(line))
        return events

    # ---------------------------------------------------------
    # RECONSTRUCT CALLER FROM EVENT
    # ---------------------------------------------------------
    def _caller_from_event(self, event: Dict[str, Any]) -> CallerState:
        c = event["caller"]

        caller = CallerState(
            caller_id=c["caller_id"],
            intent=Intent.from_str(c["intent"]),
            emotion=Emotion.from_str(c["emotion"]),
            posterior=c["posterior"],
        )

        caller.dynamic.perceived_wait = c["dynamic"]["perceived_wait"]
        caller.dynamic.frustration = c["dynamic"]["frustration"]
        caller.next_node = c["next_node"]

        return caller

    # ---------------------------------------------------------
    # RUN REPLAY
    # ---------------------------------------------------------
    def run(self, path: str, snapshot_name: str | None = None) -> Dict[str, Any]:
        """
        Replays the entire ledger through the simulator.
        Optionally saves a final snapshot.
        """

        ledger = self.load_ledger(path)
        reconstructed_events: List[Dict[str, Any]] = []

        for event in ledger:
            caller = self._caller_from_event(event)

            # Restore latent state for this event
            self.simulator.latent.load_from_dict(event["latent"])

            # Replay one step
            out = self.simulator.step(caller, event["node"])
            reconstructed_events.append(out)

        # Optional snapshot of final state
        final_snapshot = None
        if snapshot_name and reconstructed_events:
            last = reconstructed_events[-1]
            caller_snap = last["snapshot"]["caller"]
            from domain.CallerState import CallerState as CS

            final_caller = CS(
                caller_id=caller_snap["caller_id"],
                intent=Intent.from_str(caller_snap["intent"]),
                emotion=Emotion.from_str(caller_snap["emotion"]),
                posterior=caller_snap["posterior"],
            )
            final_caller.dynamic.perceived_wait = caller_snap["dynamic"]["perceived_wait"]
            final_caller.dynamic.frustration = caller_snap["dynamic"]["frustration"]
            final_caller.next_node = caller_snap["next_node"]

            structural_hash = self.verifier.compute_structural_hash()

            final_snapshot = self.snapshots.save(
                name=snapshot_name,
                caller=final_caller,
                node_id=last["node"],
                latent=self.simulator.latent,
                queues=self.graph.queues,
                structural_hash=structural_hash,
            )

        # Verification summary
        verification = self.verifier.verify(path)

        return {
            "events_replayed": len(reconstructed_events),
            "verification": verification,
            "final_snapshot": final_snapshot,
        }