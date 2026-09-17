# Row Count: 61

"""
rl_ppo.py
---------

Deterministic, queue-level PPO policy engine.

REWRITTEN 2026-07-01, adopting the architecture test_rl_ppo.py already
specified. Superseded: the earlier PPORouter, which operated per-caller
(choose_action(caller, node)) -- that was the "differential" layer, now
correctly separated into Simulator's own deterministic graph traversal
(see Sim/Simulator.py). This engine only ever sees AGGREGATE queue load,
never an individual caller -- the "transmission" layer from the
transmission/differential discussion. Not called by Simulator.step().

Governance Notes:
- lr/gamma/eps_clip are config only, stored, not "trained" -- this is
  deterministic policy INFERENCE over fixed, seeded weights, same honest
  distinction Opus's review flagged for the pre-fork version.
- Weights are a pure function of sorted(queue names) -- NOT Python's
  built-in hash(), which is randomized per interpreter session and would
  break cross-session replay (the exact landmine flagged earlier today).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import numpy as np


@dataclass
class PPOEngine:
    lr: float
    gamma: float
    eps_clip: float
    seed: int = 815

    def _weights(self, names: list) -> np.ndarray:
        # Deterministic across sessions: seeded RandomState + sorted() order,
        # never Python's hash().
        rng = np.random.RandomState(self.seed)
        return rng.randn(len(names))

    def compute_action(self, queues: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Deterministic action distribution over queues, driven by relative load.
        Higher load -> higher logit -> higher probability of being selected
        for redirected traffic.
        """
        names = sorted(queues.keys())
        loads = np.array([float(queues[n].get("load", 0.0)) for n in names])
        base = self._weights(names)

        logits = base * 0.01 + loads  # small deterministic prior + dominant load signal
        exp = np.exp(logits - np.max(logits))  # numerically stable softmax
        probs = exp / exp.sum()

        return {"probs": {n: float(p) for n, p in zip(names, probs)}}
