# simulator/cluster_runner.py
from __future__ import annotations
import threading
import random
from typing import List, Dict, Any, Callable

from domain.CallerState import CallerState
from domain.Intent import Intent
from domain.Emotion import Emotion


class ClusterRunner:
    """
    Runs many callers through the Iceberg simulator in parallel.
    Useful for:
      - stress testing
      - governance scenario runs
      - RL training data generation
      - replay ledger population
    """

    def __init__(self, graph, simulator, telemetry, num_workers: int = 8):
        self.graph = graph
        self.simulator = simulator
        self.telemetry = telemetry
        self.num_workers = num_workers

    # ---------------------------------------------------------
    # CALLER FACTORY
    # ---------------------------------------------------------
    def make_caller(self, caller_id: str) -> CallerState:
        """
        Create a synthetic caller with random intent/emotion.
        """
        intents = list(Intent)
        emotions = list(Emotion)

        intent = random.choice(intents)
        emotion = random.choice(emotions)

        posterior = {
            "billing": 0.25,
            "tech": 0.25,
            "fraud": 0.25,
            "general": 0.25,
        }

        return CallerState(
            caller_id=caller_id,
            intent=intent,
            emotion=emotion,
            posterior=posterior,
        )

    # ---------------------------------------------------------
    # WORKER LOOP
    # ---------------------------------------------------------
    def _worker(self, caller_ids: List[str], steps: int, start_node: str):
        for cid in caller_ids:
            caller = self.make_caller(cid)
            node_id = start_node

            for _ in range(steps):
                out = self.simulator.step(caller, node_id)
                node_id = out["next_node"]

    # ---------------------------------------------------------
    # CLUSTER RUN
    # ---------------------------------------------------------
    def run_cluster(self, num_callers: int, steps: int = 10, start_node: str = "root"):
        """
        Run num_callers through the simulator in parallel.
        """
        # Partition caller IDs across workers
        caller_ids = [f"caller_{i}" for i in range(num_callers)]
        chunks: List[List[str]] = []
        chunk_size = max(1, len(caller_ids) // self.num_workers)

        for i in range(0, len(caller_ids), chunk_size):
            chunks.append(caller_ids[i:i + chunk_size])

        threads: List[threading.Thread] = []

        for chunk in chunks:
            t = threading.Thread(target=self._worker, args=(chunk, steps, start_node))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # Return telemetry summary
        dump = self.telemetry.dump()
        return {
            "total_callers": num_callers,
            "steps_per_caller": steps,
            "telemetry_count": dump["count"],
        }