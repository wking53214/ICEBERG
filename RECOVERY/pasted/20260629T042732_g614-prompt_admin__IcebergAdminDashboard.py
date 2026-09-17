# admin/IcebergAdminDashboard.py
from __future__ import annotations
from typing import Dict, Any

from graph.GraphAnalytics import GraphAnalytics
from policy.PolicyMarketplace import PolicyMarketplace


class IcebergAdminDashboard:
    """
    Administrative dashboard for Iceberg 3.x.

    Provides:
      - live metrics
      - queue pressure charts
      - routing diagnostics
      - structural-hash drift indicators
      - replay snapshots
      - load-test controls
      - graph analytics panels
      - governance status
    """

    def __init__(
        self,
        simulator,
        cluster_runner,
        telemetry,
        graph,
        governance,
        load_tester,
        policy_marketplace: PolicyMarketplace,
    ):
        self.simulator = simulator
        self.cluster = cluster_runner
        self.telemetry = telemetry
        self.graph = graph
        self.governance = governance
        self.load = load_tester
        self.pm = policy_marketplace
        self.analytics = GraphAnalytics(graph)

    # ---------------------------------------------------------
    # LIVE METRICS
    # ---------------------------------------------------------
    def live_metrics(self) -> Dict[str, Any]:
        return {
            "queue_pressure": self.analytics.queue_pressure(),
            "degree_distribution": self.analytics.degree_distribution(),
            "telemetry_snapshot": self.telemetry.snapshot(),
        }

    # ---------------------------------------------------------
    # ROUTING DIAGNOSTICS
    # ---------------------------------------------------------
    def routing_diagnostics(self, caller_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Show routing decisions for a given caller.
        """
        intent = caller_context.get("intent")
        emotion = caller_context.get("emotion")
        current_node = caller_context.get("current_node")
        neighbors = self.graph.neighbors.get(current_node, [])

        # Use routing policy directly
        policy_out = self.pm.apply_or_default(
            "routing_policy",
            {
                "intent": intent,
                "emotion": emotion,
                "neighbors": neighbors,
                "caller_context": caller_context,
            },
            default=lambda ctx: {"next": neighbors},
        )

        return {
            "current_node": current_node,
            "neighbors": neighbors,
            "policy_next": policy_out.get("next", neighbors),
        }

    # ---------------------------------------------------------
    # STRUCTURAL HASH DRIFT
    # ---------------------------------------------------------
    def drift_status(self, baseline_hash: str) -> Dict[str, Any]:
        return self.analytics.detect_drift(baseline_hash)

    # ---------------------------------------------------------
    # REPLAY SNAPSHOT
    # ---------------------------------------------------------
    def replay_snapshot(self) -> Dict[str, Any]:
        """
        Return last replay snapshot from telemetry.
        """
        return self.telemetry.last_replay()

    # ---------------------------------------------------------
    # LOAD TEST CONTROLS
    # ---------------------------------------------------------
    def run_load_suite(self) -> Dict[str, Any]:
        return self.load.run_suite()

    # ---------------------------------------------------------
    # FULL DASHBOARD REPORT
    # ---------------------------------------------------------
    def report(self) -> Dict[str, Any]:
        return {
            "live_metrics": self.live_metrics(),
            "graph_analytics": self.analytics.report(),
            "governance_status": self.governance.status(),
            "structural_hash": self.analytics.structural_hash(),
            "telemetry": self.telemetry.snapshot(),
        }