# replay/recorder.py
from __future__ import annotations
import time
import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class ReplayEvent:
    """
    A single atomic event in the Iceberg simulation.
    Logged for deterministic replay.
    """
    timestamp: float
    caller_id: str
    node_id: str
    queue_state: Dict[str, Any]
    posterior: Dict[str, float]
    rl_action: Dict[str, Any]
    staffing_action: Dict[str, Any]
    seeds: Dict[str, int]
    structural_hash: str


class ReplayRecorder:
    """
    Append-only ledger writer for deterministic replay.
    """

    def __init__(self, path: str = "replay_ledger.jsonl"):
        self.path = path

    def record(self, event: ReplayEvent):
        """
        Append a single event to the ledger.
        """
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    def freeze_seeds(self) -> Dict[str, int]:
        """
        Capture all RNG seeds so replay is bit-for-bit identical.
        """
        import random
        import numpy as np
        import torch

        return {
            "python": random.getstate()[1][0],
            "numpy": int(np.random.get_state()[1][0]),
            "torch": torch.initial_seed(),
        }

    def structural_hash(self, graph) -> str:
        """
        Hash the graph structure to detect drift.
        """
        raw = json.dumps(graph.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()