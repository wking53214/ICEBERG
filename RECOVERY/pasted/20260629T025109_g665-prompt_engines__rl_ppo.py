# engines/rl_ppo.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import numpy as np

from domain.CallerState import CallerState
from domain.Intent import Intent
from domain.Emotion import Emotion


@dataclass
class PPOConfig:
    lr: float = 3e-4
    gamma: float = 0.99
    eps_clip: float = 0.2
    hidden: int = 32


class PPORouter:
    """
    PPO-based routing engine for Iceberg 3.x.
    Consumes:
      - caller state (intent, emotion, dynamics)
      - current node_id
      - neighbor list from RoutingGraph

    Produces:
      - next_node
      - action index
      - log probability
      - value estimate
    """

    def __init__(self, graph, neighbors: Dict[str, List[str]], config: PPOConfig | None = None):
        self.graph = graph
        self.neighbors = neighbors
        self.cfg = config or PPOConfig()

        # Minimal placeholder "policy" and "value" nets:
        # In a real system, these would be torch models.
        self._policy_seed = 42
        self._value_seed = 1337

    # ---------------------------------------------------------
    # STATE ENCODING
    # ---------------------------------------------------------
    def encode_state(self, caller: CallerState, node_id: str) -> np.ndarray:
        """
        Encode caller + node into a fixed-size vector.
        Deterministic, replay-safe.
        """

        # Intent one-hot
        intents = Intent.list()
        intent_vec = np.zeros(len(intents))
        intent_idx = intents.index(caller.intent)
        intent_vec[intent_idx] = 1.0

        # Emotion one-hot
        emotions = Emotion.list()
        emotion_vec = np.zeros(len(emotions))
        emotion_idx = emotions.index(caller.emotion)
        emotion_vec[emotion_idx] = 1.0

        # Dynamics
        dyn = np.array([
            caller.dynamic.perceived_wait,
            caller.dynamic.frustration,
        ])

        # Node id hash (simple deterministic embedding)
        node_hash = (hash(node_id) % 997) / 997.0
        node_vec = np.array([node_hash])

        return np.concatenate([intent_vec, emotion_vec, dyn, node_vec])

    # ---------------------------------------------------------
    # POLICY / VALUE (PLACEHOLDER)
    # ---------------------------------------------------------
    def _policy_logits(self, state: np.ndarray, num_actions: int) -> np.ndarray:
        """
        Deterministic placeholder policy.
        Uses a fixed seed + linear transform for now.
        """
        rng = np.random.RandomState(self._policy_seed)
        W = rng.randn(num_actions, state.shape[0]) * 0.01
        logits = W @ state
        return logits

    def _value_estimate(self, state: np.ndarray) -> float:
        """
        Deterministic placeholder value function.
        """
        rng = np.random.RandomState(self._value_seed)
        w = rng.randn(state.shape[0]) * 0.01
        v = float(w @ state)
        return v

    # ---------------------------------------------------------
    # ACTION SELECTION
    # ---------------------------------------------------------
    def choose_action(
        self,
        caller: CallerState,
        node_id: str,
    ) -> Tuple[str, int, float, float]:
        """
        Choose next node via PPO policy.
        Returns:
          - next_node (str)
          - action_idx (int)
          - logp (float)
          - value (float)
        """

        # Neighbor actions
        actions = self.neighbors.get(node_id, [])
        if not actions:
            # No neighbors: stay in place
            return node_id, 0, 0.0, 0.0

        state = self.encode_state(caller, node_id)
        logits = self._policy_logits(state, num_actions=len(actions))

        # Softmax
        exps = np.exp(logits - np.max(logits))
        probs = exps / np.sum(exps)

        # Deterministic argmax selection for now
        action_idx = int(np.argmax(probs))
        next_node = actions[action_idx]

        logp = float(np.log(probs[action_idx] + 1e-8))
        value = self._value_estimate(state)

        return next_node, action_idx, logp, value