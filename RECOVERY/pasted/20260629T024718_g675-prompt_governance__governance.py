# governance/governance.py
from __future__ import annotations
import json
import hashlib
from typing import Dict, Any

from replay.verifier import ReplayVerifier


class GovernanceEnvelope:
    """
    Governance layer for Iceberg 3.x.
    Enforces:
      - structural hash integrity
      - manifest invariants
      - replay consistency
      - safety gates
    """

    def __init__(self, graph, config):
        self.graph = graph
        self.config = config
        self.verifier = ReplayVerifier(graph)

        # Manifest invariants (extend as needed)
        self.invariants = {
            "root_exists": self._inv_root_exists,
            "queues_defined": self._inv_queues_defined,
            "neighbors_consistent": self._inv_neighbors_consistent,
        }

    # ---------------------------------------------------------
    # STRUCTURAL HASH
    # ---------------------------------------------------------
    def structural_hash(self) -> str:
        raw = json.dumps(self.graph.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ---------------------------------------------------------
    # INVARIANTS
    # ---------------------------------------------------------
    def _inv_root_exists(self) -> bool:
        return "root" in self.graph.nodes

    def _inv_queues_defined(self) -> bool:
        return len(self.graph.queues) > 0

    def _inv_neighbors_consistent(self) -> bool:
        for nid, nbrs in self.graph.neighbors.items():
            for n in nbrs:
                if n not in self.graph.nodes:
                    return False
        return True

    def check_invariants(self) -> Dict[str, bool]:
        """
        Evaluate all governance invariants.
        """
        return {name: fn() for name, fn in self.invariants.items()}

    # ---------------------------------------------------------
    # GOVERNANCE GATES
    # ---------------------------------------------------------
    def governance_gate(self) -> Dict[str, Any]:
        """
        Run all governance checks and return a consolidated report.
        """
        inv = self.check_invariants()
        structural = self.structural_hash()

        return {
            "invariants": inv,
            "structural_hash": structural,
            "valid": all(inv.values()),
        }

    # ---------------------------------------------------------
    # REPLAY CONSISTENCY
    # ---------------------------------------------------------
    def verify_replay(self) -> Dict[str, Any]:
        """
        Run full replay ledger verification.
        """
        return self.verifier.verify_ledger()

    def verify_snapshot(self, name: str) -> Dict[str, Any]:
        """
        Validate a specific snapshot.
        """
        return self.verifier.verify_snapshot(name)

    # ---------------------------------------------------------
    # ENFORCEMENT
    # ---------------------------------------------------------
    def enforce(self):
        """
        Enforce governance rules.
        If invariants fail, raise an exception.
        """
        report = self.governance_gate()
        if not report["valid"]:
            raise RuntimeError(f"Governance violation: {report}")
        return report