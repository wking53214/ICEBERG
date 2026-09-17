# engines/rl_marl.py
from __future__ import annotations
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, Tuple
import random


class MARLAgent(nn.Module):
    """
    A simple agent with its own policy network.
    Each agent outputs a small action vector.
    """

    def __init__(self, input_dim: int, hidden: int, output_dim: int):
        super().__init__()
        self.policy = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, output_dim),
        )

    def forward(self, x):
        return self.policy(x)


class IcebergMARL:
    """
    Multi-Agent RL engine for Iceberg 3.x.
    Produces a joint action vector from multiple cooperating agents.
    """

    def __init__(self, graph, queues, latent, priors, device="cpu"):
        self.graph = graph
        self.queues = queues
        self.latent = latent
        self.priors = priors

        self.device = torch.device(device)

        # State vector: intent, emotion, perceived_wait, frustration
        self.state_dim = 4
        self.hidden = 32

        # Each agent outputs a small vector (4 dims)
        self.agent_output_dim = 4

        # Number of agents in the MARL system
        self.num_agents = 4

        self.agents = nn.ModuleList([
            MARLAgent(self.state_dim, self.hidden, self.agent_output_dim).to(self.device)
            for _ in range(self.num_agents)
        ])

        self.optimizer = optim.Adam(self.parameters(), lr=3e-4)

    def parameters(self):
        params = []
        for agent in self.agents:
            params.extend(list(agent.parameters()))
        return params

    def encode_state(self, caller) -> torch.Tensor:
        vec = torch.tensor([
            float(caller.intent.value),
            float(caller.emotion.value),
            float(caller.dynamic.perceived_wait),
            float(caller.dynamic.frustration),
        ], dtype=torch.float32, device=self.device)
        return vec

    def joint_action(self, caller, node_id: str) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Returns:
        - joint_action_vector (concatenated agent outputs)
        - individual agent outputs (dict)
        """
        state = self.encode_state(caller)

        outputs = {}
        vectors = []

        for idx, agent in enumerate(self.agents):
            out = agent(state)
            outputs[f"agent_{idx}"] = out
            vectors.append(out)

        # Concatenate into a single joint vector
        joint = torch.cat(vectors, dim=0)

        return joint, outputs

    def train_step(self, batch):
        """
        Batch contains:
        - state
        - joint_action
        - reward
        """
        states = torch.stack([b["state"] for b in batch]).to(self.device)
        rewards = torch.tensor([b["reward"] for b in batch], device=self.device)

        # Forward pass for each agent
        losses = []
        for agent in self.agents:
            logits = agent(states)
            # Simple MSE loss against reward (placeholder)
            loss = (logits.mean(dim=1) - rewards).pow(2).mean()
            losses.append(loss)

        total_loss = sum(losses)

        self.optimizer.zero_grad()
        total_loss.backward()
        self.optimizer.step()

        return float(total_loss.item())