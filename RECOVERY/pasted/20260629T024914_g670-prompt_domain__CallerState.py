# domain/CallerState.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any

from domain.Intent import Intent
from domain.Emotion import Emotion


@dataclass
class DynamicState:
    """
    Dynamic caller metrics updated every simulation step.
    These feed into MARL + PPO state vectors.
    """
    perceived_wait: float = 0.0
    frustration: float = 0.0


@dataclass
class CallerState:
    """
    Canonical caller state for Iceberg 3.x.
    """

    caller_id: str
    intent: Intent
    emotion: Emotion
    posterior: Dict[str, float]

    # Dynamic state (updated each step)
    dynamic: DynamicState = field(default_factory=DynamicState)

    # Routing
    next_node: str | None = None

    # Likelihood model (placeholder)
    def likelihoods(self) -> Dict[str, float]:
        """
        Likelihoods for BayesianIntentEngineGPU.
        In a real system, this would come from ASR/NLU signals.
        """
        return {
            "billing": 0.25,
            "tech": 0.25,
            "fraud": 0.25,
            "general": 0.25,
        }

    def snapshot(self) -> Dict[str, Any]:
        """
        Snapshot used by replay + snapshot manager.
        """
        return {
            "caller_id": self.caller_id,
            "intent": self.intent.value,
            "emotion": self.emotion.value,
            "posterior": self.posterior,
            "dynamic": {
                "perceived_wait": self.dynamic.perceived_wait,
                "frustration": self.dynamic.frustration,
            },
            "next_node": self.next_node,
        }