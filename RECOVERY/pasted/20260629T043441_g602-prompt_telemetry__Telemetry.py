# telemetry/Telemetry.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
import time

from telemetry.TelemetryAggregator import TelemetryAggregator


class Telemetry:
    """
    Full telemetry engine for Iceberg 3.x.

    Provides:
      - event logging
      - replay snapshots
      - MARL + PPO episode logs
      - governance drift logs
      - structural-hash snapshots
      - queue metrics
      - caller traces
      - dashboard-ready exports
    """

    def __init__(self, max_events: int = 50000):
        self.agg = TelemetryAggregator(max_events=max_events)
        self._last_replay_snapshot: Optional[Dict[str, Any]] = None

    # ---------------------------------------------------------
    # BASIC EVENT LOGGING
    # ---------------------------------------------------------
    def log(self, event_type: str, payload: Dict[str, Any]):
        self.agg.record({
            "type": event_type,
            "payload": payload,
        })

    # ---------------------------------------------------------
    # ROUTING EVENTS
    # ---------------------------------------------------------
    def log_routing(self, caller_id: str, current: str, next_node: str, scores: Dict[str, float]):
        self.log("routing", {
            "caller_id": caller_id,
            "current": current,
            "next": next_node,
            "scores": scores,
        })

    # ---------------------------------------------------------
    # QUEUE METRICS
    # ---------------------------------------------------------
    def log_queue(self, queue_name: str, load: int):
        self.log("queue_metric", {
            "queue": queue_name,
            "load": load,
        })

    # ---------------------------------------------------------
    # PPO EPISODE LOGGING
    # ---------------------------------------------------------
    def log_ppo_episode(self, data: Dict[str, Any]):
        self.log("ppo_episode", data)

    # ---------------------------------------------------------
    # MARL EPISODE LOGGING
    # ---------------------------------------------------------
    def log_marl_episode(self, data: Dict[str, Any]):
        self.log("marl_episode", data)

    # ---------------------------------------------------------
    # GOVERNANCE DRIFT LOGGING
    # ---------------------------------------------------------
    def log_drift(self, baseline_hash: str, current_hash: str):
        self.log("drift", {
            "baseline_hash": baseline_hash,
            "current_hash": current_hash,
            "drift": baseline_hash != current_hash,
        })

    # ---------------------------------------------------------
    # REPLAY SNAPSHOT
    # ---------------------------------------------------------
    def snapshot_replay(self, graph_dict: Dict[str, Any], structural_hash: str):
        snap = {
            "timestamp": time.time(),
            "graph": graph_dict,
            "structural_hash": structural_hash,
        }
        self._last_replay_snapshot = snap
        self.log("replay_snapshot", snap)

    def last_replay(self) -> Optional[Dict[str, Any]]:
        return self._last_replay_snapshot

    # ---------------------------------------------------------
    # EXPORT
    # ---------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        return self.agg.snapshot()

    def filter_by_caller(self, caller_id: str) -> List[Dict[str, Any]]:
        return self.agg.filter_by_caller(caller_id)

    def filter_by_queue(self, queue_name: str) -> List[Dict[str, Any]]:
        return self.agg.filter_by_queue(queue_name)

    def filter_by_node(self, node_id: str) -> List[Dict[str, Any]]:
        return self.agg.filter_by_node(node_id)