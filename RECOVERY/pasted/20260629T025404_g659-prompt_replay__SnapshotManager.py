# replay/SnapshotManager.py
from __future__ import annotations
import json
import os
from typing import Dict, Any

from domain.CallerState import CallerState
from domain.Intent import Intent
from domain.Emotion import Emotion
from latent.LatentPayload import LatentPayload
from domain.QueueState import QueueState


class SnapshotManager:
    """
    Deterministic snapshot manager for Iceberg 3.x.
    Saves and loads:
      - caller state
      - latent state
      - queue states
      - current node
      - structural hash
    """

    def __init__(self, directory: str = "snapshots"):
        self.directory = directory
        os.makedirs(self.directory, exist_ok=True)

    # ---------------------------------------------------------
    # PATH
    # ---------------------------------------------------------
    def _path(self, name: str) -> str:
        return os.path.join(self.directory, f"{name}.json")

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------
    def save(
        self,
        name: str,
        caller: CallerState,
        node_id: str,
        latent: LatentPayload,
        queues: Dict[str, QueueState],
        structural_hash: str,
    ):
        data = {
            "caller": caller.snapshot(),
            "node": node_id,
            "latent": latent.to_dict(),
            "queues": {
                qname: q.snapshot()
                for qname, q in queues.items()
            },
            "structural_hash": structural_hash,
        }

        with open(self._path(name), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return data

    # ---------------------------------------------------------
    # LOAD
    # ---------------------------------------------------------
    def load(self, name: str) -> Dict[str, Any]:
        path = self._path(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Snapshot '{name}' not found")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---------------------------------------------------------
    # RECONSTRUCT CALLER
    # ---------------------------------------------------------
    def reconstruct_caller(self, snap: Dict[str, Any]) -> CallerState:
        c = snap["caller"]

        caller = CallerState(
            caller_id=c["caller_id"],
            intent=Intent.from_str(c["intent"]),
            emotion=Emotion.from_str(c["emotion"]),
            posterior=c["posterior"],
        )

        caller.dynamic.perceived_wait = c["dynamic"]["perceived_wait"]
        caller.dynamic.frustration = c["dynamic"]["frustration"]
        caller.next_node = c["next_node"]

        return caller

    # ---------------------------------------------------------
    # RECONSTRUCT LATENT
    # ---------------------------------------------------------
    def reconstruct_latent(self, snap: Dict[str, Any]) -> LatentPayload:
        lat = LatentPayload()
        lat.load_from_dict(snap["latent"])
        return lat

    # ---------------------------------------------------------
    # RECONSTRUCT QUEUES
    # ---------------------------------------------------------
    def reconstruct_queues(self, snap: Dict[str, Any]) -> Dict[str, QueueState]:
        out = {}
        for name, qdata in snap["queues"].items():
            q = QueueState(name=name)
            q.active_calls = qdata["active_calls"]
            q.staffing = qdata["staffing"]
            q.target_service_level = qdata["target_service_level"]
            q.abandonment_rate = qdata["abandonment_rate"]
            out[name] = q
        return out

    # ---------------------------------------------------------
    # VERIFY SNAPSHOT INTEGRITY
    # ---------------------------------------------------------
    def verify(self, snap: Dict[str, Any], graph) -> Dict[str, Any]:
        """
        Validate structural hash + basic fields.
        """

        raw = json.dumps(graph.to_dict(), sort_keys=True)
        current_hash = __import__("hashlib").sha256(raw.encode("utf-8")).hexdigest()

        return {
            "structural_hash_match": current_hash == snap["structural_hash"],
            "expected_hash": snap["structural_hash"],
            "current_hash": current_hash,
            "node": snap["node"],
            "caller_id": snap["caller"]["caller_id"],
        }