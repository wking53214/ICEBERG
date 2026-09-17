# Row Count: 66

"""
rl_marl.py
----------

Deterministic, queue-level multi-agent policy engine.

REWRITTEN 2026-07-01, same reasoning as rl_ppo.py -- superseded per-caller
MARLEngine (choose_actions(agents, node_id), required graph/neighbors at
construction). New version: config-only construction, operates purely on
aggregate queue load, one independent probability distribution per agent.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import numpy as np


@dataclass
class MARLEngine:
    lr: float
    hidden: int
    agents: int
    seed: int = 815

    def _weights(self, agent_idx: int, n_names: int) -> np.ndarray:
        # Deterministic per-agent: seed offset by agent index, not hash().
        rng = np.random.RandomState(self.seed + agent_idx)
        return rng.randn(n_names)

    def compute_joint_action(self, queues: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Independent deterministic action distribution per agent, over queues."""
        names = sorted(queues.keys())
        loads = np.array([float(queues[n].get("load", 0.0)) for n in names])

        actions = {}
        for i in range(self.agents):
            base = self._weights(i, len(names))
            logits = base * 0.01 + loads
            exp = np.exp(logits - np.max(logits))
            probs = exp / exp.sum()
            actions[f"agent_{i}"] = {"probs": {n: float(p) for n, p in zip(names, probs)}}

        return {"actions": actions}
