# engines/bayes_gpu.py
from __future__ import annotations
from typing import Dict, List
import torch


class BayesianIntentEngineGPU:
    """
    Simple GPU-accelerated Bayesian updater for intent posteriors.
    """

    def __init__(self, device: str = "cuda"):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")

    def _to_tensor(self, posterior: Dict, intents: List) -> torch.Tensor:
        vals = [posterior[i] for i in intents]
        return torch.tensor(vals, dtype=torch.float32, device=self.device)

    def _normalize(self, t: torch.Tensor) -> torch.Tensor:
        s = torch.sum(t)
        if s.item() == 0.0:
            return torch.ones_like(t) / t.numel()
        return t / s

    def observe_single(
        self,
        posterior: Dict,
        likelihoods: Dict,
        intents: List,
    ) -> Dict:
        """
        Single-step Bayesian update:
        posterior_new ∝ likelihood * posterior_old
        """
        p = self._to_tensor(posterior, intents)
        l = self._to_tensor(likelihoods, intents)
        unnorm = p * l
        norm = self._normalize(unnorm)

        return {i: float(v) for i, v in zip(intents, norm.tolist())}

    def observe_sequence(
        self,
        posterior: Dict,
        sequence_likelihoods: List[Dict],
        intents: List,
    ) -> Dict:
        """
        Apply multiple likelihood updates in sequence on GPU.
        """
        p = self._to_tensor(posterior, intents)

        for lk in sequence_likelihoods:
            l = self._to_tensor(lk, intents)
            p = self._normalize(p * l)

        return {i: float(v) for i, v in zip(intents, p.tolist())}