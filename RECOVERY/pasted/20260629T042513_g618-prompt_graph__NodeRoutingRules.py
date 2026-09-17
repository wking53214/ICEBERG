# graph/NodeRoutingRules.py
from __future__ import annotations
from typing import Dict, Any, List

from domain.Intent import Intent
from domain.Emotion import Emotion
from policy.PolicyMarketplace import PolicyMarketplace


class NodeRoutingRules:
    """
    Advanced routing logic for Iceberg 3.x.

    Provides:
      - intent-weighted routing
      - emotion-weighted routing
      - queue-pressure routing
      - multi-policy blending
      - deterministic next-node selection
    """

    def __init__(self, policy_marketplace: PolicyMarketplace):
        self.pm = policy_marketplace

    # ---------------------------------------------------------
    # INTENT WEIGHTING
    # ---------------------------------------------------------
    def _intent_weight(self, node_meta: Dict[str, Any], intent: str) -> float:
        weights = node_meta.get("intent_weights", {})
        return weights.get(intent, 1.0)

    # ---------------------------------------------------------
    # EMOTION WEIGHTING
    # ---------------------------------------------------------
    def _emotion_weight(self, node_meta: Dict[str, Any], emotion: str) -> float:
        weights = node_meta.get("emotion_weights", {})
        return weights.get(emotion, 1.0)

    # ---------------------------------------------------------
    # QUEUE PRESSURE
    # ---------------------------------------------------------
    def _queue_pressure(self, queue_meta: Dict[str, Any]) -> float:
        load = queue_meta.get("load", 0)
        return max(0.1, 1.0 / (1.0 + load))

    # ---------------------------------------------------------
    # COMBINE WEIGHTS
    # ---------------------------------------------------------
    def _combine(self, intent_w: float, emotion_w: float, pressure_w: float) -> float:
        return intent_w * emotion_w * pressure_w

    # ---------------------------------------------------------
    # ROUTE
    # ---------------------------------------------------------
    def route(
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
        Determine next node using:
          - node metadata
          - queue metadata
          - intent/emotion weights
          - queue pressure
          - policy marketplace
        """

        # Policy override (if any)
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

        # Weight each candidate
        scored = []
        for n in candidate_neighbors:
            node_meta = graph.nodes[n].meta
            queue_name = graph.nodes[n].queue
            queue_meta = graph.queues.get(queue_name, {})

            intent_w = self._intent_weight(node_meta, intent)
            emotion_w = self._emotion_weight(node_meta, emotion)
            pressure_w = self._queue_pressure(queue_meta)

            score = self._combine(intent_w, emotion_w, pressure_w)
            scored.append((n, score))

        # Deterministic selection: highest score wins
        scored.sort(key=lambda x: x[1], reverse=True)
        next_node = scored[0][0] if scored else current_node

        return {
            "current": current_node,
            "next": next_node,
            "scores": {n: s for n, s in scored},
        }