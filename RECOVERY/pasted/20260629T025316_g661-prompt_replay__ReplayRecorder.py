# replay/ReplayRecorder.py
from __future__ import annotations
import json
import time
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
    next_node: str
    dynamic: Dict[str, Any]
    latent: Dict[str, Any]
    ppo: Dict[str, Any]
    marl: Dict[str, Any]
    staffing: Dict[str, float]
    structural_hash: str


class ReplayRecorder:
    """
    Append-only ledger writer for deterministic replay.
    """

    def __init__(self, path: str = "replay_ledger.jsonl"):
        self.path = path

    # ---------------------------------------------------------
    # STRUCTURAL HASH
    # ---------------------------------------------------------
    def structural_hash(self, graph) -> str:
        """
        Hash the graph structure to detect drift.
        """
        raw = json.dumps(graph.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ---------------------------------------------------------
    # RECORD EVENT
    # ---------------------------------------------------------
    def record(
        self,
        caller,
        node_id: str,
        next_node: str,
        latent: Dict[str, Any],
        ppo: Dict[str, Any],
        marl: Dict[str, Any],
        staffing: Dict[str, float],
        graph,
    ):
        """
        Append a single event to the ledger.
        Deterministic, replay-safe.
        """

        event = ReplayEvent(
            timestamp=time.time(),
            caller_id=caller.caller_id,
            node_id=node_id,
            next_node=next_node,
            dynamic={
                "perceived_wait": caller.dynamic.perceived_wait,
                "frustration": caller.dynamic.frustration,
            },
            latent=latent,
            ppo=ppo,
            marl=marl,
            staffing=staffing,
            structural_hash=self.structural_hash(graph),
        )

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")

        return asdict(event)