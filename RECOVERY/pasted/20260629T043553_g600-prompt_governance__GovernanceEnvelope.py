# governance/GovernanceEnvelope.py
from __future__ import annotations
from typing import Dict, Any

from policy.PolicyMarketplace import PolicyMarketplace
from graph.GraphModel import GraphModel
from telemetry.Telemetry import Telemetry


class GovernanceEnvelope:
    """
    Governance layer for Iceberg 3.x.

    Provides:
      - structural-hash integrity enforcement
      - manifest version monotonicity
      - drift detection
      - extraction integrity
      - safety-gate policy enforcement
      - replay determinism guarantees
    """

    def __init__(
        self,
        baseline_graph: GraphModel,
        policy_marketplace: PolicyMarketplace,
        telemetry: Telemetry,
        version: int = 1,
    ):
        self.baseline_graph = baseline_graph
        self.baseline_hash = baseline_graph.structural_hash()
        self.version = version
        self.pm = policy_marketplace
        self.telemetry = telemetry

    # ---------------------------------------------------------
    # STRUCTURAL HASH CHECK
    # ---------------------------------------------------------
    def check_structural_integrity(self, graph: GraphModel) -> Dict[str, Any]:
        current_hash = graph.structural_hash()
        drift = current_hash != self.baseline_hash

        if drift:
            self.telemetry.log_drift(self.baseline_hash, current_hash)

        return {
            "baseline_hash": self.baseline_hash,
            "current_hash": current_hash,
            "drift": drift,
        }

    # ---------------------------------------------------------
    # VERSION CHECK
    # ---------------------------------------------------------
    def check_version(self, incoming_version: int) -> Dict[str, Any]:
        if incoming_version < self.version:
            return {
                "allowed": False,
                "reason": "Version regression",
                "current_version": self.version,
                "incoming_version": incoming_version,
            }

        return {
            "allowed": True,
            "current_version": self.version,
            "incoming_version": incoming_version,
        }

    # ---------------------------------------------------------
    # EXTRACTION POLICY
    # ---------------------------------------------------------
    def check_extraction(self, incoming_hash: str, incoming_version: int) -> Dict[str, Any]:
        ctx = {
            "incoming_hash": incoming_hash,
            "current_hash": self.baseline_hash,
            "incoming_version": incoming_version,
            "current_version": self.version,
        }

        out = self.pm.apply_or_default(
            "extraction_policy",
            ctx,
            default=lambda c: {"allowed": True},
        )

        return out

    # ---------------------------------------------------------
    # SAFETY GATES
    # ---------------------------------------------------------
    def check_safety_gates(self, graph: GraphModel) -> Dict[str, Any]:
        """
        Safety gates are policy-defined governance checks.
        """
        ctx = {
            "graph": graph.to_dict(),
            "structural_hash": graph.structural_hash(),
            "baseline_hash": self.baseline_hash,
        }

        out = self.pm.apply_or_default(
            "governance_policy",
            ctx,
            default=lambda c: {"allowed": True},
        )

        return out

    # ---------------------------------------------------------
    # APPLY GOVERNANCE
    # ---------------------------------------------------------
    def apply(self, graph: GraphModel, incoming_version: int) -> Dict[str, Any]:
        """
        Apply all governance checks.
        """

        structural = self.check_structural_integrity(graph)
        versioning = self.check_version(incoming_version)
        extraction = self.check_extraction(
            incoming_hash=graph.structural_hash(),
            incoming_version=incoming_version,
        )
        gates = self.check_safety_gates(graph)

        allowed = (
            not structural["drift"]
            and versioning["allowed"]
            and extraction.get("allowed", False)
            and gates.get("allowed", False)
        )

        if allowed:
            # Update baseline
            self.baseline_graph = graph
            self.baseline_hash = graph.structural_hash()
            self.version = incoming_version

        return {
            "allowed": allowed,
            "structural": structural,
            "versioning": versioning,
            "extraction": extraction,
            "gates": gates,
            "new_version": self.version,
        }

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        return {
            "baseline_hash": self.baseline_hash,
            "version": self.version,
        }