# rl/MARLTrainer.py
from __future__ import annotations
from typing import Dict, Any, List

from domain.Intent import Intent
from domain.Emotion import Emotion
from policy.PolicyMarketplace import PolicyMarketplace


class MARLTrainer:
    """
    Multi-Agent RL trainer for Iceberg 3.x.

    Provides:
      - multiple agents (per-queue / per-intent / per-role)
      - shared or independent policies
      - reward shaping via reward_policy
      - episodic training
      - telemetry logging
    """

    def __init__(
        self,
        simulator,
        policy_marketplace: PolicyMarketplace,
        telemetry,
        agents: Dict[str, Any],
    ):
        """
        agents: mapping of agent_id -> agent_object
        Each agent_object must implement:
          - act(state) -> action
          - update(trajectory) -> None
        """
        self.simulator = simulator
        self.pm = policy_marketplace
        self.telemetry = telemetry
        self.agents = agents

    # ---------------------------------------------------------
    # BUILD STATE
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
        Run a single multi-agent episode over a batch of callers.
        """
        trajectories: Dict[str, List[Dict[str, Any]]] = {aid: [] for aid in self.agents.keys()}
        total_reward = 0.0

        for caller in batch:
            state = self._build_state(caller)

            # Choose agent (simple example: by intent)
            intent = state["intent"]
            if intent == Intent.BILLING.name.lower():
                agent_id = "billing_agent"
            elif intent == Intent.TECH.name.lower():
                agent_id = "tech_agent"
            elif intent == Intent.FRAUD.name.lower():
                agent_id = "fraud_agent"
            else:
                agent_id = "general_agent"

            agent = self.agents.get(agent_id)
            if agent is None:
                continue

            # Agent acts
            action = agent.act(state)

            # Simulator step
            sim_out = self.simulator.step(caller, action)

            # Reward shaping
            reward_context = {
                "queue_length": sim_out.get("queue_length", 0),
                "emotion": state["emotion"],
                "resolved": sim_out.get("resolved", False),
            }
            reward = self._shape_reward(reward_context)
            total_reward += reward

            # Record trajectory
            trajectories[agent_id].append({
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": sim_out.get("next_state", state),
            })

        # Update agents
        for aid, traj in trajectories.items():
            if traj:
                self.agents[aid].update(traj)

        # Telemetry
        self.telemetry.log_marl_episode({
            "total_reward": total_reward,
            "trajectories": trajectories,
        })

        return {
            "total_reward": total_reward,
            "trajectories": trajectories,
        }

    # ---------------------------------------------------------
    # TRAIN LOOP
    # ---------------------------------------------------------
    def train(self, episodes: int, batch_fn) -> Dict[str, Any]:
        """
        Train for a number of episodes.

        batch_fn: callable that returns a batch of callers per episode.
        """
        history = []

        for ep in range(episodes):
            batch = batch_fn()
            result = self.run_episode(batch)
            history.append(result)

        return {
            "episodes": episodes,
            "history": history,
        }