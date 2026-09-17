# replay/verifier.py
from __future__ import annotations
import hashlib
import json
from typing import Dict, Any, List


class ReplayVerifier:
    """
    Validates deterministic replay integrity:
      - structural hash consistency
      - posterior drift
      - queue state consistency
      - RL action reproducibility
    """

    def __init__(self, graph, queues):
        self.graph = graph
        self.queues = queues

    # ---------------------------------------------------------
    # STRUCTURAL HASH CHECK
    # ---------------------------------------------------------
    def compute_structural_hash(self) -> str:
        """
        Hash the graph structure to detect drift.
        """
        raw = json.dumps(self.graph.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def verify_structural_hash(self, expected: str) -> bool:
        """
        Compare expected hash with current graph hash.
        """
        return self.compute_structural_hash() == expected

    # ---------------------------------------------------------
    # POSTERIOR DRIFT CHECK
    # ---------------------------------------------------------
    def verify_posterior(self, expected: Dict[str, float], actual: Dict[str, float]) -> bool:
        """
        Posterior must match exactly for deterministic replay.
        """
        if expected.keys() != actual.keys():
            return False

        for k in expected:
            if abs(expected[k] - actual[k]) > 1e-9:
                return False

        return True

    # ---------------------------------------------------------
    # QUEUE STATE CHECK
    # ---------------------------------------------------------
    def verify_queue_state(self, expected: Dict[str, Any]) -> bool:
        """
        Validate queue metrics (staffing, active calls, SL targets, abandonment).
        """
        for qname, qstate in expected.items():
            q = self.queues[qname]

            if q.active_calls != qstate["active_calls"]:
                return False
            if q.staffing != qstate["staffing"]:
                return False
            if q.target_service_level != qstate["target_service_level"]:
                return False
            if q.abandonment_rate != qstate["abandonment_rate"]:
                return False

        return True

    # ---------------------------------------------------------
    # RL ACTION CHECK
    # ---------------------------------------------------------
    def verify_rl_action(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """
        RL actions must match exactly for deterministic replay.
        """
        return expected == actual

    # ---------------------------------------------------------
    # STAFFING ACTION CHECK
    # ---------------------------------------------------------
    def verify_staffing_action(self, expected: Dict[str, float], actual: Dict[str, float]) -> bool:
        """
        Staffing deltas must match exactly.
        """
        if expected.keys() != actual.keys():
            return False

        for k in expected:
            if abs(expected[k] - actual[k]) > 1e-9:
                return False

        return True

    # ---------------------------------------------------------
    # FULL EVENT VERIFICATION
    # ---------------------------------------------------------
    def verify_event(self, event: Dict[str, Any], reconstructed: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate all components of a replayed event.
        Returns a dict of boolean checks.
        """

        return {
            "structural_hash": self.verify_structural_hash(event["structural_hash"]),
            "posterior": self.verify_posterior(event["posterior"], reconstructed["posterior"]),
            "queue_state": self.verify_queue_state(event["queue_state"]),
            "rl_action": self.verify_rl_action(event["rl_action"], reconstructed["rl_action"]),
            "staffing_action": self.verify_staffing_action(event["staffing_action"], reconstructed["staffing_action"]),
        }