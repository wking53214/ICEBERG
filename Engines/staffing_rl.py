# Row Count: 47

"""
staffing_rl.py
--------------

Deterministic, queue-level staffing delta engine.

REWRITTEN 2026-07-01, same reasoning as rl_ppo.py -- superseded per-caller
StaffingOptimizerRL (required graph/queues/latent/priors at construction).
New version: config-only construction, deterministic delta per queue driven
by that queue's own load, clipped to delta_limit.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass
class StaffingRLEngine:
    lr: float
    delta_limit: float

    def compute_deltas(self, queues: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Deterministic staffing delta per queue: load above 0.5 -> positive
        delta (add staffing), below -> negative (reduce), clipped to
        delta_limit. No randomness, no cross-queue dependency.
        """
        deltas = {}
        for name, q in queues.items():
            load = float(q.get("load", 0.0))
            raw = (load - 0.5) * 1.0
            deltas[name] = max(-self.delta_limit, min(self.delta_limit, raw))
        return deltas
