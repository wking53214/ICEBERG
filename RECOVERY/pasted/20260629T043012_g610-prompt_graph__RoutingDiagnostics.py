# graph/RoutingDiagnostics.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple

from policy.PolicyMarketplace import PolicyMarketplace
from graph.NodeRoutingRules import NodeRoutingRules


class RoutingDiagnostics:
    """
    Routing trace + explainability for Iceberg 3.x.

    Provides:
      - per-hop routing traces
      - policy decision introspection
      - weight breakdowns (intent/emotion/queue pressure)
      - deterministic explanations
    """

    def __init__(self, policy_marketplace: PolicyMarketplace, routing_rules: NodeRoutingRules):
        self.pm = policy_marketplace
        self.rules = routing_rules

    # ---------------------------------------------------------
    # SINGLE-HOP DIAGNOSTICS
    # ---------------------------------------------------------
    def diagnose_hop(
        self,
        *,
        current_node: str,
        neighbors: List[str],
        graph: Any,
        intent: str,
        emotion: str,
        caller_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Explain a single routing decision.
        """

        # Policy output
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
        candidate_neighbors = policy_out.get("next", neighbors)

        # Use NodeRoutingRules to get scores
        routed = self.rules.route(
            current_node=current_node,
            neighbors=candidate_neighbors,
            graph=graph,
            intent=intent,
            emotion=emotion,
            caller_context=caller_context,
        )

        return {
            "current_node": current_node,
            "neighbors": neighbors,
            "policy_candidates": candidate_neighbors,
            "scores": routed["scores"],
            "chosen_next": routed["next"],
        }

    # ---------------------------------------------------------
    # MULTI-HOP TRACE
    # ---------------------------------------------------------
    def trace_route(
        self,
        *,
        start_node: str,
        graph: Any,
        intent: str,
        emotion: str,
        caller_context: Dict[str, Any],
        max_hops: int = 10,
    ) -> Dict[str, Any]:
        """
        Trace routing decisions across multiple hops.
        """

        hops: List[Dict[str, Any]] = []
        current = start_node

        for _ in range(max_hops):
            neighbors = graph.neighbors.get(current, [])
            if not neighbors:
                break

            hop_diag = self.diagnose_hop(
                current_node=current,
                neighbors=neighbors,
                graph=graph,
                intent=intent,
                emotion=emotion,
                caller_context=caller_context,
            )
            hops.append(hop_diag)

            next_node = hop_diag["chosen_next"]
            if next_node == current:
                break
            current = next_node

        return {
            "start_node": start_node,
            "final_node": current,
            "intent": intent,
            "emotion": emotion,
            "hops": hops,
        }