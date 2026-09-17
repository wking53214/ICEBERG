# engines/staffing_rl.py
from __future__ import annotations
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, List


class StaffingNetwork(nn.Module):
    """
    Simple feedforward network that outputs staffing deltas
    for each queue.
    """

    def __init__(self, state_dim: int, num_queues: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, num_queues),
        )

    def forward(self, x):
        return self.net(x)


class StaffingOptimizerRL:
    """
    RL-based staffing optimizer for Iceberg 3.x.
    Produces per-queue staffing deltas.
    """

    def __init__(self, graph, queues, latent, priors, device: str = "cpu"):
        self.graph = graph
        self.queues = queues
        self.latent = latent
        self.priors = priors

        self.device = torch.device(device)

        self.queue_names = list(self.queues.keys())
        self.num_queues = len(self.queue_names)

        # State: avg_active_calls, avg_sl, avg_abandon, latent_trust, latent_volatility
        self.state_dim = 5

        self.net = StaffingNetwork(self.state_dim, self.num_queues).to(self.device)
        self.optimizer = optim.Adam(self.net.parameters(), lr=3e-4)

    # ---------------------------------------------------------
    # STATE ENCODING
    # ---------------------------------------------------------
    def encode_state(self) -> torch.Tensor:
        """
        Encode global queue + latent state into a vector.
        """
        if self.num_queues == 0:
            return torch.zeros(self.state_dim, dtype=torch.float32, device=self.device)

        active_calls = [q.active_calls for q in self.queues.values()]
        sls = [q.target_service_level for q in self.queues.values()]
        abandons = [q.abandonment_rate for q in self.queues.values()]

        avg_active = sum(active_calls) / len(active_calls)
        avg_sl = sum(sls) / len(sls)
        avg_abandon = sum(abandons) / len(abandons)

        trust = self.latent.trust_scalar
        volatility = self.latent.volatility

        vec = torch.tensor(
            [avg_active, avg_sl, avg_abandon, trust, volatility],
            dtype=torch.float32,
            device=self.device,
        )
        return vec

    # ---------------------------------------------------------
    # ACTION PROPOSAL
    # ---------------------------------------------------------
    def propose_staffing(self) -> Dict[str, float]:
        """
        Propose staffing deltas for each queue.
        """
        state = self.encode_state()
        deltas = self.net(state)

        # Convert to small deltas
        deltas = torch.tanh(deltas) * 0.5  # +/- 0.5 FTE

        result: Dict[str, float] = {}
        for i, qname in enumerate(self.queue_names):
            result[qname] = float(deltas[i].item())

        return result

    # ---------------------------------------------------------
    # TRAINING STEP
    # ---------------------------------------------------------
    def train_step(self, batch: List[Dict[str, Any]]) -> float:
        """
        Batch items:
          - state
          - deltas
          - reward
        """
        states = torch.stack([b["state"] for b in batch]).to(self.device)
        rewards = torch.tensor([b["reward"] for b in batch], device=self.device)

        preds = self.net(states)
        # Simple baseline: mean of predicted deltas should correlate with reward
        pred_mean = preds.mean(dim=1)

        loss = (pred_mean - rewards).pow(2).mean()

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return float(loss.item())