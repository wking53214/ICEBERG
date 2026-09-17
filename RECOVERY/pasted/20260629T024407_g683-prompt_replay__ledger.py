# replay/ledger.py
from __future__ import annotations
import json
import os
from typing import Dict, Any, List


class ReplayLedger:
    """
    Append-only ledger for Iceberg 3.x replay events.
    Stores each event as a JSON line.
    """

    def __init__(self, path: str = "replay_ledger.jsonl"):
        self.path = path
        # Ensure file exists
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                pass

    def append(self, event: Dict[str, Any]):
        """
        Append a single event to the ledger.
        """
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def read_all(self) -> List[Dict[str, Any]]:
        """
        Read all events from the ledger.
        """
        events = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def tail(self, n: int) -> List[Dict[str, Any]]:
        """
        Return the last n events.
        """
        events = self.read_all()
        return events[-n:] if n <= len(events) else events

    def clear(self):
        """
        Clear the ledger (rarely used; mostly for testing).
        """
        with open(self.path, "w", encoding="utf-8") as f:
            pass

    def count(self) -> int:
        """
        Number of events in the ledger.
        """
        with open(self.path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)