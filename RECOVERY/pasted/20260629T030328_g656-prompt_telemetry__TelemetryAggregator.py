# telemetry/TelemetryAggregator.py
from __future__ import annotations
import time
import threading
from typing import Dict, Any, List


class TelemetryAggregator:
    """
    High-frequency, thread-safe telemetry collector for Iceberg 3.x.
    Stores:
      - caller dynamics
      - latent state
      - PPO traces
      - MARL joint actions
      - staffing RL deltas
      - queue metrics
      - structural hash drift signals

    Append-only, JSON-safe, deterministic.
    """

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    # ---------------------------------------------------------
    # RECORD
    # ---------------------------------------------------------
    def record(self, evt: Dict[str, Any]):
        """
        Append a telemetry event.
        """
        with self.lock:
            entry = {
                "timestamp": time.time(),
                "event": evt,
            }
            self.events.append(entry)

            # Trim buffer
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]

    # ---------------------------------------------------------
    # SNAPSHOT
    # ---------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """
        Return all telemetry events.
        """
        with self.lock:
            return {
                "count": len(self.events),
                "events": list(self.events),
            }

    # ---------------------------------------------------------
    # FILTERS
    # ---------------------------------------------------------
    def filter_by_caller(self, caller_id: str) -> List[Dict[str, Any]]:
        with self.lock:
            return [
                e for e in self.events
                if e["event"].get("caller_id") == caller_id
            ]

    def filter_by_node(self, node_id: str) -> List[Dict[str, Any]]:
        with self.lock:
            return [
                e for e in self.events
                if e["event"].get("node") == node_id
            ]

    def filter_by_queue(self, queue_name: str) -> List[Dict[str, Any]]:
        with self.lock:
            return [
                e for e in self.events
                if e["event"].get("queue") == queue_name
            ]

    # ---------------------------------------------------------
    # CLEAR
    # ---------------------------------------------------------
    def clear(self):
        with self.lock:
            self.events = []