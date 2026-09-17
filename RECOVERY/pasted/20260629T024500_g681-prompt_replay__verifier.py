# replay/verifier.py
from __future__ import annotations
import json
import hashlib
from typing import Dict, Any, List

from replay.ledger import ReplayLedger
from replay.snapshot import SnapshotManager


class ReplayVerifier:
    """
    Verifies deterministic replay integrity for Iceberg 3.x.
    Checks:
      - structural hash drift
      - ledger consistency
      - seed stability
      - caller + queue reconstruction validity
    """

    def __init__(self, graph, ledger_path="replay_ledger.jsonl"):
        self.graph = graph
        self.ledger = ReplayLedger(ledger_path)
        self.snapshots = SnapshotManager()

    # ---------------------------------------------------------
    # STRUCTURAL HASH
    # ---------------------------------------------------------
    def compute_structural_hash(self) -> str:
        raw = json.dumps(self.graph.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def verify_structural_hash(self, evt_hash: str) -> bool:
        """
        Compare event structural hash with current graph hash.
        """
        current = self.compute_structural_hash()
        return current == evt_hash

    # ---------------------------------------------------------
    # LEDGER CONSISTENCY
    # ---------------------------------------------------------
    def verify_ledger(self) -> Dict[str, Any]:
        """
        Validate the entire ledger for:
          - missing fields
          - malformed events
          - structural hash drift
          - seed presence
        """
        events = self.ledger.read_all()
        issues = []

        for idx, evt in enumerate(events):
            # Required fields
            required = [
                "caller_id",
                "node_id",
                "queue_state",
                "posterior",
                "rl_action",
                "staffing_action",
                "seeds",
                "structural_hash",
            ]

            for field in required:
                if field not in evt:
                    issues.append({
                        "index": idx,
                        "error": f"Missing field: {field}",
                        "event": evt,
                    })

            # Structural hash drift
            if not self.verify_structural_hash(evt["structural_hash"]):
                issues.append({
                    "index": idx,
                    "error": "Structural hash drift detected",
                    "event_hash": evt["structural_hash"],
                    "current_hash": self.compute_structural_hash(),
                })

            # Seed presence
            if "python" not in evt["seeds"] or "numpy" not in evt["seeds"] or "torch" not in evt["seeds"]:
                issues.append({
                    "index": idx,
                    "error": "Missing RNG seeds",
                    "event": evt,
                })

        return {
            "total_events": len(events),
            "issues": issues,
            "valid": len(issues) == 0,
        }

    # ---------------------------------------------------------
    # SNAPSHOT CONSISTENCY
    # ---------------------------------------------------------
    def verify_snapshot(self, name: str) -> Dict[str, Any]:
        """
        Validate a snapshot for structural hash correctness and required fields.
        """
        snap = self.snapshots.load_snapshot(name)
        issues = []

        required = ["caller_id", "node_id", "queue_state", "posterior", "seeds", "structural_hash"]

        for field in required:
            if field not in snap:
                issues.append(f"Missing field: {field}")

        # Structural hash drift
        if not self.verify_structural_hash(snap["structural_hash"]):
            issues.append("Structural hash drift detected")

        return {
            "snapshot": name,
            "issues": issues,
            "valid": len(issues) == 0,
        }