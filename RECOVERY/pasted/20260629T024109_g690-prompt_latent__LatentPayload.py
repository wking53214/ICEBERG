# latent/LatentPayload.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any
import hashlib
import json


@dataclass
class LatentPayload:
    """
    Canonical latent payload for Iceberg 3.x.
    These variables are NOT directly observable by the IVR.
    They drive:
      - Bayesian inference
      - PPO routing
      - MARL joint policies
      - emotional drift
      - queue abandonment dynamics
    """

    # Core latent dimensions
    capability_score: float = 0.5          # caller's ability to navigate menus
    patience: float = 0.5                  # tolerance for wait time
    volatility: float = 0.3                # likelihood of sudden frustration spikes
    memory_flag: float = 0.0               # remembers previous IVR interactions
    trust_scalar: float = 0.5              # trust in the IVR system

    # Emotional priors
    baseline_frustration: float = 0.1
    escalation_rate: float = 0.05

    # Routing priors
    menu_compliance: float = 0.7           # probability caller follows menu instructions
    navigation_depth_prior: float = 0.4    # how deep they’re willing to navigate

    # Fraud / risk priors
    fraud_risk: float = 0.1                # latent fraud probability

    # ---------------------------------------------------------
    # SERIALIZATION
    # ---------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def load_from_dict(self, data: Dict[str, Any]):
        for k, v in data.items():
            setattr(self, k, v)

    # ---------------------------------------------------------
    # STRUCTURAL HASH
    # ---------------------------------------------------------
    def structural_hash(self) -> str:
        """
        Hash the latent payload for drift detection.
        """
        raw = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ---------------------------------------------------------
    # UPDATE RULES
    # ---------------------------------------------------------
    def update_after_step(self, caller_dynamic):
        """
        Update latent variables after each simulation step.
        This keeps the latent world model evolving.
        """

        # Frustration increases based on escalation rate
        caller_dynamic.frustration += self.escalation_rate * (1.0 - self.patience)

        # Trust decreases if frustration grows
        self.trust_scalar -= 0.01 * caller_dynamic.frustration
        if self.trust_scalar < 0:
            self.trust_scalar = 0

        # Volatility increases if caller is impatient
        self.volatility += 0.005 * (1.0 - self.patience)
        if self.volatility > 1.0:
            self.volatility = 1.0

        # Memory flag increases slightly each step
        self.memory_flag = min(1.0, self.memory_flag + 0.01)