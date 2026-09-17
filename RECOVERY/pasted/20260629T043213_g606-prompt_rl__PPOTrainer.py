# rl/PPOTrainer.py
from __future__ import annotations
from typing import Dict, Any, List, Callable

from policy.PolicyMarketplace import PolicyMarketplace


class PPOTrainer:
    """
    Single-Agent PPO trainer for Iceberg 3.x.

    Assumes agent implements:
      - act(state) -> action
      - update(trajectory) -> None

    Integrates:
      - simulator for environment dynamics
      - reward_policy for shaping
      - telemetry for logging
    """

    def __init__(
        self,
        simulator,
        policy_marketplace: PolicyMarketplace,
        telemetry,
        agent: Any,
    ):
        self.simulator = simulator
        self.pm = policy_marketplace
        self.telemetry = telemetry
        self.agent = agent

    # ---------------------------------------------------------
    # STATE BUILDING
    # ---------------------------------------------------------
    def _build_state(self, caller: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "intent": caller.get("intent"),
            "emotion": caller.get("emotion"),
            "duration": caller.get("duration"),
        }

    # ---------------------------------------------------------
    # REWARD SHAPING
    # ---------------------------------------------------------
    def _shape_reward(self, context: Dict[str, Any]) -> float:
        out = self.pm.apply_or_default(
            "reward_policy",
            context,
            default=lambda ctx: {"reward": 0.0},
        )
        return out.get("reward", 0.0)

    # ---------------------------------------------------------
    # RUN EPISODE
    # ---------------------------------------------------------
    def run_episode(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run a single PPO episode over a batch of callers.
        """
        trajectory: List[Dict[str, Any]] = []
        total_reward = 0.0

        for caller in batch:
            state = self._build_state(caller)

            # Agent acts
            action = self.agent.act(state)

            # Environment step
            sim_out = self.simulator.step(caller, action)

            # Reward shaping
            reward_context = {
                "queue_length": sim_out.get("queue_length", 0),
                "emotion": state["emotion"],
                "resolved": sim_out.get("resolved", False),
            }
            reward = self._shape_reward(reward_context)
            total_reward += reward

            # Record transition
            trajectory.append({
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": sim_out.get("next_state", state),
            })

        # Update agent with full episode trajectory
        if trajectory:
            self.agent.update(trajectory)

        # Telemetry
        self.telemetry.log_ppo_episode({
            "total_reward": total_reward,
            "trajectory": trajectory,
        })

        return {
            "total_reward": total_reward,
            "trajectory": trajectory,
        }

    # ---------------------------------------------------------
    # TRAIN LOOP
    # ---------------------------------------------------------
    def train(self, episodes: int, batch_fn: Callable[[], List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Train for a number of episodes.

        batch_fn: callable that returns a batch of callers per episode.
        """
        history: List[Dict[str, Any]] = []

        for ep in range(episodes):
            batch = batch_fn()
            result = self.run_episode(batch)
            history.append(result)

        return {
            "episodes": episodes,
            "history": history,
        }