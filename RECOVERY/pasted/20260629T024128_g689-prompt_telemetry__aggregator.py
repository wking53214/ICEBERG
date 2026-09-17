# telemetry/aggregator.py
from __future__ import annotations
from typing import Dict, Any, List
import time
import threading


class TelemetryAggregator:
    """
    Lightweight in‑memory telemetry collector for Iceberg 3.x.
    Stores:
      - replay events
      - RL actions
      - queue snapshots
      - caller state snapshots
      - structural hash drift signals

    Thread‑safe, append‑only, JSON‑serializable.
    """

    def __init__(self, max_events: int = 5000):
        self.max_events = max_events
        self.events: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    # ---------------------------------------------------------
    # LOGGING
    # ---------------------------------------------------------
    def log_event(self, evt: Dict[str, Any]):
        """
        Append a telemetry event.
        """
        with self.lock:
            evt_record = {
                "timestamp": time.time(),
                "event": evt,
            }
            self.events.append(evt_record)

            # Trim buffer if needed
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]

    # ---------------------------------------------------------
    # SNAPSHOT
    # ---------------------------------------------------------
    def dump(self) -> Dict[str, Any]:
        """
        Return all telemetry events.
        """
        with self.lock:
            return {
                "count": len(self.events),
                "events": list(self.events),
            }

    # ---------------------------------------------------------
    # FILTERING
    # ---------------------------------------------------------
    def filter_by_caller(self, caller_id: str) -> List[Dict[str, Any]]:
        """
        Return all events for a specific caller.
        """
        with self.lock:
            return [
                e for e in self.events
                if e["event"].get("caller_id") == caller_id
            ]

    def filter_by_node(self, node_id: str) -> List[Dict[str,Any]]:
        """
        Return all events for a specific node.
        """
        with self.lock:
            return [
                e for e in self.events
                if e["event"].get("node_id") == node_id
            ]

    # ---------------------------------------------------------
    # CLEAR
    # ---------------------------------------------------------
    def clear(self):
        """
        Clear all telemetry events.
        """
        with self.lock:
            self.events = []