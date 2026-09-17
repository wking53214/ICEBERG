# engines/rl_marl.py
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Tuple

from domain.CallerState import CallerState
from latent.LatentPayload import LatentPayload


@dataclass
class MARLConfig:
    agents: int = 4
    hidden: int = 32
    lr: float = 3e-4


class IcebergMARL:
    """
    Multi-Agent Reinforcement Learning engine for Iceberg 3.x.
    Produces:
      - joint action vector (R^N)
      - per-agent action vectors
    Deterministic, replay-safe placeholder implementation.
    """

    def __init__(self, graph, queues, latent=None, priors=None, config: MARLConfig | None = None):
        self.graph = graph
        self.queues = queues
        self.latent = latent or LatentPayload()
        self.priors = priors or {}
        self.cfg = config or MARLConfig()

        # Deterministic seeds for replay stability
        self._agent_seed = 9001
        self._joint_seed = 13371337

    # ---------------------------------------------------------
    # STATE ENCODING
    # ---------------------------------------------------------
    def encode_state(self, caller: CallerState, node_id: str) -> np.ndarray:
        """
        Encode caller + latent + node into a fixed-size vector.
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

        node_hash = (hash(node_id) % 997) / 997.0
        node_vec = np.array([node_hash])

        return np.concatenate([dyn, lat, node_vec])

    # ---------------------------------------------------------
    # AGENT ACTIONS
    # ---------------------------------------------------------
    def _agent_action(self, state: np.ndarray, agent_idx: int) -> np.ndarray:
        """
        Deterministic per-agent action vector.
        """
        rng = np.random.RandomState(self._agent_seed + agent_idx)
        W = rng.randn(self.cfg.hidden, state.shape[0]) * 0.01
        return W @ state

    # ---------------------------------------------------------
    # JOINT ACTION
    # ---------------------------------------------------------
    def _joint_action(self, agent_outputs: Dict[int, np.ndarray]) -> np.ndarray:
        """
        Deterministic joint action aggregator.
        """
        rng = np.random.RandomState(self._joint_seed)
        # Weighted sum of agent outputs
        weights = rng.rand(self.cfg.agents)
        weights = weights / np.sum(weights)

        stacked = np.stack([agent_outputs[i] for i in range(self.cfg.agents)], axis=0)
        joint = weights @ stacked
        return joint

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------
    def joint_action(self, caller: CallerState, node_id: str) -> Tuple[np.ndarray, Dict[int, np.ndarray]]:
        """
        Produce:
          - joint action vector
          - per-agent action vectors
        """

        state = self.encode_state(caller, node_id)

        agents = {
            i: self._agent_action(state, i)
            for i in range(self.cfg.agents)
        }

        joint = self._joint_action(agents)

        return joint, agents