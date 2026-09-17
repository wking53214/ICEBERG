# engines/staffing_rl.py
from __future__ import annotations
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any


class StaffingPolicy(nn.Module):
    """
    Simple continuous-control policy for staffing adjustments.
    """

    def __init__(self, input_dim: int, hidden: int, output_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class StaffingOptimizerRL:
    """
    RL engine that proposes staffing adjustments for queues.
    """

    def __init__(self, graph, queues, latent, priors, device: str = "cpu"):
        self.graph = graph
        self.queues = queues
        self.latent = latent
        self.priors = priors

        self.device = torch.device(device)

        # State: for each queue, we encode a few metrics
        # active_calls, staffing, target_service_level, abandonment_rate
        self.features_per_queue = 4
        self.num_queues = len(self.queues)
        self.state_dim = self.features_per_queue * self.num_queues

        # One action per queue: staffing delta
        self.action_dim = self.num_queues

        self.policy = StaffingPolicy(self.state_dim, 32, self.action_dim).to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=3e-4)

    def encode_state(self) -> torch.Tensor:
        """
        Build a flat state vector from all queues.
        """
        vals = []
        for qname, q in self.queues.items():
            vals.extend([
                float(q.active_calls),
                float(q.staffing),
                float(q.target_service_level),
                float(q.abandonment_rate),
            ])
        return torch.tensor(vals, dtype=torch.float32, device=self.device)

    def propose_staffing(self) -> Dict[str, float]:
        """
        Returns a dict of {queue_name: staffing_delta}.
        """
        state = self.encode_state()
        deltas = self.policy(state)

        result = {}
        for idx, (qname, _) in enumerate(self.queues.items()):
            result[qname] = float(deltas[idx].item())
        return result

    def train_step(self, batch):
        """
        Batch contains:
        - state
        - deltas
        - reward
        """
        states = torch.stack([b["state"] for b in batch]).to(self.device)
        rewards = torch.tensor([b["reward"] for b in batch], device=self.device)

        preds = self.policy(states)
        # Simple loss: encourage higher reward when magnitude of deltas is appropriate
        loss = (preds.mean(dim=1) - rewards).pow(2).mean()

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return float(loss.item())