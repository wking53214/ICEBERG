# engines/staffing_rl.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

import numpy as np

from domain.CallerState import CallerState
from latent.LatentPayload import LatentPayload
from domain.QueueState import QueueState


@dataclass
class StaffingConfig:
    lr: float = 3e-4
    delta_limit: float = 0.5  # +/- FTE per step
    hidden: int = 16


class StaffingOptimizerRL:
    """
    RL-based staffing optimizer for Iceberg 3.x.
    Produces deterministic staffing deltas per queue.
    """

    def __init__(self, graph, queues: Dict[str, QueueState], latent=None, priors=None, config: StaffingConfig | None = None):
        self.graph = graph
        self.queues = queues
        self.latent = latent or LatentPayload()
        self.priors = priors or {}
        self.cfg = config or StaffingConfig()

        self._seed = 4242

    # ---------------------------------------------------------
    # STATE ENCODING
    # ---------------------------------------------------------
    def encode_state(self, caller: CallerState) -> np.ndarray:
        """
        Encode caller + latent + aggregate queue metrics.
        Deterministic, replay-safe.
        """

        dyn = np.array([
            caller.dynamic.perceived_wait,
            caller.dynamic.frustration,
        ])

        lat = np.array([
            self.latent.trust,
            self.latent.volatility,
            self.latent.frustration_memory,
            self.latent.drift,
        ])

        # Aggregate queue metrics (simple averages)
        if self.queues:
            staffing = np.mean([q.staffing for q in self.queues.values()])
            sl = np.mean([q.target_service_level for q in self.queues.values()])
            abandon = np.mean([q.abandonment_rate for q in self.queues.values()])
        else:
            staffing = 0.0
            sl = 0.0
            abandon = 0.0

        q_vec = np.array([staffing, sl, abandon])

        return np.concatenate([dyn, lat, q_vec])

    # ---------------------------------------------------------
    # DELTA GENERATION
    # ---------------------------------------------------------
    def _raw_deltas(self, state: np.ndarray, num_queues: int) -> np.ndarray:
        """
        Deterministic raw staffing deltas.
        """
        rng = np.random.RandomState(self._seed)
        W = rng.randn(num_queues, state.shape[0]) * 0.01
        deltas = W @ state
        return deltas

    def _clip_deltas(self, deltas: np.ndarray) -> np.ndarray:
        """
        Clip deltas to +/- delta_limit.
        """
        return np.clip(deltas, -self.cfg.delta_limit, self.cfg.delta_limit)

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------
    def propose_staffing(self, caller: CallerState) -> Dict[str, float]:
        """
        Propose staffing deltas per queue.
        Returns a dict: {queue_name: delta}
        """

        state = self.encode_state(caller)
        names = list(self.queues.keys())
        if not names:
            return {}

        raw = self._raw_deltas(state, num_queues=len(names))
        clipped = self._clip_deltas(raw)

        return {
            name: float(delta)
            for name, delta in zip(names, clipped)
        }

    def apply_staffing(self, caller: CallerState) -> Dict[str, float]:
        """
        Apply proposed staffing deltas directly to queues.
        Returns the applied deltas.
        """

        deltas = self.propose_staffing(caller)
        for name, delta in deltas.items():
            q = self.queues.get(name)
            if q is not None:
                q.apply_delta(delta)
        return deltas