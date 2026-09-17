# replay/ReplayRunner.py
from __future__ import annotations
from typing import Dict, Any, List

from replay.ReplayVerifier import ReplayVerifier
from replay.SnapshotManager import SnapshotManager
from telemetry.Telemetry import Telemetry


class ReplayRunner:
    """
    Deterministic replay engine for Iceberg 3.x.

    Reconstructs:
      - caller state
      - queue state
      - routing decisions
      - latent payloads
      - structural-hash integrity
      - snapshots for governance
    """

    def __init__(
        self,
        simulator,
        snapshot_manager: SnapshotManager,
        verifier: ReplayVerifier,
        telemetry: Telemetry,
    ):
        self.simulator = simulator
        self.snapshots = snapshot_manager
        self.verifier = verifier
        self.telemetry = telemetry

    # ---------------------------------------------------------
    # LOAD LEDGER
    # ---------------------------------------------------------
    def load_ledger(self, ledger: List[Dict[str, Any]]):
        """
        Ledger is a list of deterministic events:
          - caller state
          - queue state
          - routing decisions
          - RNG seeds
          - structural hashes
        """
        self.ledger = ledger

    # ---------------------------------------------------------
    # REPLAY EVENT
    # ---------------------------------------------------------
    def _replay_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replay a single event through the simulator.
        """
        caller = event.get("caller")
        action = event.get("action")
        sim_out = self.simulator.step(caller, action)

        return {
            "event": event,
            "sim_out": sim_out,
        }

    # ---------------------------------------------------------
    # FULL REPLAY
    # ---------------------------------------------------------
    def replay(self) -> Dict[str, Any]:
        """
        Replay the entire ledger deterministically.
        """
        results = []
        for event in self.ledger:
            out = self._replay_event(event)
            results.append(out)

        # Structural hash verification
        verification = self.verifier.verify(self.ledger, results)

        # Snapshot for governance + dashboard
        snapshot = self.snapshots.create_snapshot(results)
        self.telemetry.snapshot_replay(snapshot, snapshot.get("structural_hash"))

        return {
            "results": results,
            "verification": verification,
            "snapshot": snapshot,
        }

    # ---------------------------------------------------------
    # REPLAY + VERIFY + SNAPSHOT
    # ---------------------------------------------------------
    def replay_and_verify(self) -> Dict[str, Any]:
        """
        Convenience wrapper: replay → verify → snapshot.
        """
        return self.replay()