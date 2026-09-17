# replay/snapshot.py
from __future__ import annotations
import json
import os
from typing import Dict, Any


class SnapshotManager:
    """
    Saves and loads simulation snapshots for deterministic replay.
    Snapshots contain:
      - caller state
      - queue states
      - latent payload (optional)
      - structural hash
    """

    def __init__(self, directory: str = "snapshots"):
        self.directory = directory
        os.makedirs(self.directory, exist_ok=True)

    def save_snapshot(self, name: str, data: Dict[str, Any]):
        """
        Save a snapshot as JSON.
        """
        path = os.path.join(self.directory, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_snapshot(self, name: str) -> Dict[str, Any]:
        """
        Load a snapshot by name.
        """
        path = os.path.join(self.directory, f"{name}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Snapshot '{name}' not found")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_snapshots(self):
        """
        Return all snapshot names.
        """
        files = os.listdir(self.directory)
        return [f.replace(".json", "") for f in files if f.endswith(".json")]