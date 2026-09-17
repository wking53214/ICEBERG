# latent/LatentPayload.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any

from domain.CallerState import DynamicState


@dataclass
class LatentPayload:
    """
    Canonical latent state for Iceberg 3.x.
    This is the hidden caller-state vector used by:
      - MARL agents
      - PPO router
      - Staffing RL
      - Bayesian inference engine
      - Replay system
    """

    # Trust in system (0–1)
    trust: float = 0.5

    # Volatility / emotional instability (0–1)
    volatility: float = 0.3

    # Long-term frustration memory (0–1)
    frustration_memory: float = 0.0

    # Drift accumulator for governance
    drift: float = 0.0

    # ---------------------------------------------------------
    # UPDATE LOGIC
    # ---------------------------------------------------------
    def update_after_step(self, dynamic: DynamicState):
        """
        Update latent state based on caller dynamics.
        Deterministic, replay-safe.
        """

        # Frustration memory accumulates slowly
        self.frustration_memory += 0.01 * dynamic.frustration
        self.frustration_memory = min(self.frustration_memory, 1.0)

        # Volatility increases with frustration
        self.volatility += 0.005 * dynamic.frustration
        self.volatility = min(self.volatility, 1.0)

        # Trust decreases if frustration is high
        self.trust -= 0.003 * dynamic.frustration
        self.trust = max(self.trust, 0.0)

        # Drift accumulates for governance
        self.drift += 0.001 * dynamic.frustration

    # ---------------------------------------------------------
    # SERIALIZATION
    # ---------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def load_from_dict(self, data: Dict[str, Any]):
        self.trust = data.get("trust", self.trust)
        self.volatility = data.get("volatility", self.volatility)
        self.frustration_memory = data.get("frustration_memory", self.frustration_memory)
        self.drift = data.get("drift", self.drift)