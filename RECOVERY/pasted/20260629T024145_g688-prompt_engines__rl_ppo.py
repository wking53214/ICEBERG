# engines/rl_ppo.py
from __future__ import annotations
import torch
import torch.nn as nn
import torch.optim as optim
import random
from typing import Dict, Any, Tuple, List


# ---------------------------------------------------------
# PPO NETWORK
# ---------------------------------------------------------
class PPONetwork(nn.Module):
    def __init__(self, state_dim: int, action_dim: int):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
        )

        self.policy = nn.Linear(64, action_dim)
        self.value = nn.Linear(64, 1)

    def forward(self, x):
        h = self.shared(x)
        logits = self.policy(h)
        value = self.value(h)
        return logits, value


# ---------------------------------------------------------
# PPO ROUTER
# ---------------------------------------------------------
class PPORouter:
    """
    PPO-based routing engine for Iceberg 3.x.
    """

    def __init__(self, graph, neighbors):
        self.graph = graph
        self.neighbors = neighbors

        self.state_dim = 6          # intent, emotion, frustration, wait, trust, volatility
        self.action_dim = len(neighbors["root"])

        self.net = PPONetwork(self.state_dim, self.action_dim)
        self.optimizer = optim.Adam(self.net.parameters(), lr=3e-4)

        self.gamma = 0.99
        self.eps_clip = 0.2

    # ---------------------------------------------------------
    # STATE ENCODING
    # ---------------------------------------------------------
    def encode_state(self, caller) -> torch.Tensor:
        """
        Convert caller state into PPO input vector.
        """
        intent = caller.intent.value
        emotion = caller.emotion.value
        frustration = caller.dynamic.frustration
        wait = caller.dynamic.perceived_wait

        trust = caller.posterior.get("general", 0.25)
        volatility = 0.3

        return torch.tensor([
            intent,
            emotion,
            frustration,
            wait,
            trust,
            volatility,
        ], dtype=torch.float32)

    # ---------------------------------------------------------
    # ACTION SELECTION
    # ---------------------------------------------------------
    def choose_action(self, caller, node_id: str) -> Tuple[str, int, float, float]:
        """
        Choose routing action using PPO policy.
        Returns:
          next_node, action_idx, logp, value
        """
        state = self.encode_state(caller)
        logits, value = self.net(state)

        probs = torch.softmax(logits, dim=-1)
        dist = torch.distributions.Categorical(probs)

        idx = dist.sample().item()
        logp = dist.log_prob(torch.tensor(idx)).item()

        next_node = self.neighbors[node_id][idx]

        return next_node, idx, logp, value.item()

    # ---------------------------------------------------------
    # TRAINING STEP
    # ---------------------------------------------------------
    def train_step(self, batch: List[Dict[str, Any]]) -> float:
        """
        Perform one PPO update.
        Batch items:
          state, action_idx, old_logp, reward, value
        """
        states = torch.stack([b["state"] for b in batch])
        actions = torch.tensor([b["action_idx"] for b in batch])
        old_logps = torch.tensor([b["old_logp"] for b in batch])
        rewards = torch.tensor([b["reward"] for b in batch])
        values = torch.tensor([b["value"] for b in batch])

        # Advantage
        advantages = rewards - values

        logits, new_values = self.net(states)
        probs = torch.softmax(logits, dim=-1)
        dist = torch.distributions.Categorical(probs)

        new_logps = dist.log_prob(actions)

        ratio = torch.exp(new_logps - old_logps)

        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.eps_clip, 1 + self.eps_clip) * advantages

        loss = -torch.min(surr1, surr2).mean() + (new_values.squeeze() - rewards).pow(2).mean()

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()