# governance/GovernanceEnvelope.py
from __future__ import annotations
import json
import hashlib
import time
from typing import Dict, Any


class GovernanceViolation(Exception):
    """Raised when structural drift or invariant violation occurs."""
    pass


class GovernanceEnvelope:
    """
    Governance layer for Iceberg 3.x.
    Enforces:
      - structural-hash invariants
      - deterministic replay compatibility
      - drift detection
      - governance telemetry
    """

    def __init__(self, graph, telemetry, strict: bool = True):
        self.graph = graph
        self.telemetry = telemetry
        self.strict = strict
        self._baseline_hash = self._compute_hash()

    # ---------------------------------------------------------
    # STRUCTURAL HASH
    # ---------------------------------------------------------
    def _compute_hash(self) -> str:
        raw = json.dumps(self.graph.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def check_hash(self):
        current = self._compute_hash()
        if current != self._baseline_hash:
            evt = {
                "type": "governance_drift",
                "timestamp": time.time(),
                "expected": self._baseline_hash,
                "actual": current,
            }
            self.telemetry.record(evt)

            if self.strict:
                raise GovernanceViolation(
                    f"Structural drift detected — expected {self._baseline_hash}, got {current}"
                )
            return False
        return True

    # ---------------------------------------------------------
    # WRAP SIMULATOR STEP
    # ---------------------------------------------------------
    def wrap_step(self, simulator, caller, node_id: str) -> Dict[str, Any]:
        """
        Governance-wrapped simulator step.
        Ensures structural integrity before and after execution.
        """

        # Pre-step governance check
        self.check_hash()

        out = simulator.step(caller, node_id)

        # Post-step governance check
        self.check_hash()

        # Emit governance telemetry
        self.telemetry.record({
            "type": "governance_step",
            "caller_id": caller.caller_id,
            "node": node_id,
            "next_node": out["next_node"],
            "latent": out["latent"],
            "timestamp": time.time(),
        })

        return out

    # ---------------------------------------------------------
    # WRAP REPLAY RECORDING
    # ---------------------------------------------------------
    def wrap_replay_record(self, recorder, **kwargs):
        """
        Governance-wrapped replay recording.
        Ensures structural integrity before writing ledger entries.
        """

        self.check_hash()
        evt = recorder.record(**kwargs)
        self.check_hash()

        self.telemetry.record({
            "type": "governance_replay_record",
            "caller_id": kwargs.get("caller").caller_id,
            "node": kwargs.get("node_id"),
            "timestamp": time.time(),
        })

        return evt

    # ---------------------------------------------------------
    # WRAP CLUSTER EXECUTION
    # ---------------------------------------------------------
    def wrap_cluster_batch(self, cluster_runner, batch, steps: int):
        """
        Governance-wrapped parallel batch execution.
        """

        self.check_hash()
        out = cluster_runner.run_batch(batch, steps)
        self.check_hash()

        self.telemetry.record({
            "type": "governance_cluster_batch",
            "batch_size": len(batch),
            "timestamp": time.time(),
        })

        return out

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------
    def baseline_hash(self) -> str:
        return self._baseline_hash

    def current_hash(self) -> str:
        return self._compute_hash()

    def drift_report(self) -> Dict[str, Any]:
        current = self._compute_hash()
        return {
            "expected": self._baseline_hash,
            "current": current,
            "drift": current != self._baseline_hash,
        }