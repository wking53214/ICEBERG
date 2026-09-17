# engines/rl_ppo.py
from __future__ import annotations
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple, Dict, Any
import random


class PolicyNet(nn.Module):
    def __init__(self, input_dim: int, hidden: int, output_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class ValueNet(nn.Module):
    def __init__(self, input_dim: int, hidden: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, x):
        return self.net(x)


class PPORouter:
    """
    PPO-based routing engine for Iceberg 3.x.
    Chooses next node based on caller state + graph neighbors.
    """

    def __init__(self, graph, action_space_fn, device="cpu"):
        self.graph = graph
        self.action_space_fn = action_space_fn
        self.device = torch.device(device)

        # Simple state vector: intent, emotion, perceived_wait, frustration
        self.state_dim = 4
        self.hidden = 32
        self.max_actions = 16  # padded action space

        self.policy = PolicyNet(self.state_dim, self.hidden, self.max_actions).to(self.device)
        self.value = ValueNet(self.state_dim, self.hidden).to(self.device)

        self.optimizer = optim.Adam(
            list(self.policy.parameters()) + list(self.value.parameters()),
            lr=3e-4
        )

    def encode_state(self, caller) -> torch.Tensor:
        vec = torch.tensor([
            float(caller.intent.value),
            float(caller.emotion.value),
            float(caller.dynamic.perceived_wait),
            float(caller.dynamic.frustration),
        ], dtype=torch.float32, device=self.device)
        return vec

    def choose_action(self, caller, node_id: str) -> Tuple[str, int, float, float]:
        """
        Returns:
        - chosen_node
        - action_index
        - log_prob
        - value_estimate
        """
        neighbors = self.action_space_fn(node_id)
        if not neighbors:
            return node_id, 0, 0.0, 0.0

        state = self.encode_state(caller)
        logits = self.policy(state)
        probs = torch.softmax(logits[:len(neighbors)], dim=0)

        idx = torch.multinomial(probs, 1).item()
        chosen = neighbors[idx]

        logp = torch.log(probs[idx])
        value = self.value(state).item()

        return chosen, idx, float(logp), float(value)

    def train_step(self, batch: List[Dict[str, Any]]):
        """
        Batch contains:
        - state
        - action_idx
        - old_logp
        - reward
        - value
        """
        states = torch.stack([b["state"] for b in batch]).to(self.device)
        actions = torch.tensor([b["action_idx"] for b in batch], device=self.device)
        old_logp = torch.tensor([b["old_logp"] for b in batch], device=self.device)
        rewards = torch.tensor([b["reward"] for b in batch], device=self.device)
        values = torch.tensor([b["value"] for b in batch], device=self.device)

        # Advantage
        adv = rewards - values

        # New log probs
        logits = self.policy(states)
        probs = torch.softmax(logits, dim=1)
        new_logp = torch.log(probs[range(len(actions)), actions])

        ratio = torch.exp(new_logp - old_logp)
        clipped = torch.clamp(ratio, 0.8, 1.2) * adv

        policy_loss = -torch.min(ratio * adv, clipped).mean()
        value_loss = (self.value(states).squeeze() - rewards).pow(2).mean()

        loss = policy_loss + 0.5 * value_loss

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return float(loss.item())