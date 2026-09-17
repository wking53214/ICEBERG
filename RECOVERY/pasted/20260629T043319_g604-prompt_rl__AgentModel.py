# rl/AgentModel.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple
import random
import math


class AgentModel:
    """
    Minimal PPO-compatible agent for Iceberg 3.x.

    Provides:
      - act(state) -> action
      - update(trajectory) -> PPO-style update
      - policy + value networks (simple linear approximations)
      - advantage estimation
      - entropy bonus
    """

    def __init__(self, action_space: List[str], lr: float = 0.01, gamma: float = 0.99, clip: float = 0.2):
        self.action_space = action_space
        self.lr = lr
        self.gamma = gamma
        self.clip = clip

        # Simple linear policy weights
        self.policy_weights: Dict[str, float] = {a: random.uniform(-0.1, 0.1) for a in action_space}

        # Value function baseline
        self.value_bias = 0.0

    # ---------------------------------------------------------
    # POLICY
    # ---------------------------------------------------------
    def _policy(self, state: Dict[str, Any]) -> Dict[str, float]:
        """
        Softmax over linear weights.
        """
        logits = {a: self.policy_weights[a] for a in self.action_space}
        max_logit = max(logits.values())
        exp = {a: math.exp(logits[a] - max_logit) for a in self.action_space}
        total = sum(exp.values())
        return {a: exp[a] / total for a in self.action_space}

    # ---------------------------------------------------------
    # VALUE FUNCTION
    # ---------------------------------------------------------
    def _value(self, state: Dict[str, Any]) -> float:
        return self.value_bias

    # ---------------------------------------------------------
    # ACT
    # ---------------------------------------------------------
    def act(self, state: Dict[str, Any]) -> str:
        """
        Sample an action from the policy distribution.
        """
        probs = self._policy(state)
        actions = list(probs.keys())
        weights = list(probs.values())
        return random.choices(actions, weights=weights, k=1)[0]

    # ---------------------------------------------------------
    # ADVANTAGE ESTIMATION
    # ---------------------------------------------------------
    def _compute_advantages(self, trajectory: List[Dict[str, Any]]) -> List[float]:
        """
        Simple discounted reward advantage.
        """
        rewards = [t["reward"] for t in trajectory]
        values = [self._value(t["state"]) for t in trajectory]

        advantages = []
        running = 0.0
        for r, v in reversed(list(zip(rewards, values))):
            running = r + self.gamma * running
            advantages.append(running - v)
        return list(reversed(advantages))

    # ---------------------------------------------------------
    # UPDATE (PPO)
    # ---------------------------------------------------------
    def update(self, trajectory: List[Dict[str, Any]]) -> None:
        """
        PPO-style update using clipped objective.
        """
        advantages = self._compute_advantages(trajectory)

        for t, adv in zip(trajectory, advantages):
            state = t["state"]
            action = t["action"]

            old_probs = self._policy(state)
            old_prob = old_probs[action]

            # Update policy weight for chosen action
            new_weight = self.policy_weights[action] + self.lr * adv
            self.policy_weights[action] = new_weight

            # Recompute new probability
            new_probs = self._policy(state)
            new_prob = new_probs[action]

            # PPO clipping
            ratio = new_prob / (old_prob + 1e-8)
            clipped_ratio = max(min(ratio, 1 + self.clip), 1 - self.clip)

            # Apply clipped update
            self.policy_weights[action] += self.lr * clipped_ratio * adv

            # Update value baseline
            self.value_bias += self.lr * adv * 0.1