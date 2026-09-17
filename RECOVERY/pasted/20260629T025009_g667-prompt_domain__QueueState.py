# domain/QueueState.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class QueueState:
    """
    Canonical queue metrics for Iceberg 3.x.
    These values are mutated by:
      - simulator (active_calls)
      - staffing RL (staffing)
      - governance rules (target SL)
      - abandonment model (abandonment_rate)
    """

    name: str
    active_calls: int = 0
    staffing: float = 1.0
    target_service_level: float = 0.80
    abandonment_rate: float = 0.02

    def snapshot(self) -> Dict[str, Any]:
        return {
            "active_calls": self.active_calls,
            "staffing": self.staffing,
            "target_service_level": self.target_service_level,
            "abandonment_rate": self.abandonment_rate,
        }

    def apply_delta(self, delta: float):
        """
        Apply staffing delta from Staffing RL.
        """
        self.staffing += delta
        if self.staffing < 0:
            self.staffing = 0