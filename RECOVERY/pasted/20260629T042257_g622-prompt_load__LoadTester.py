# load/LoadTester.py
from __future__ import annotations
import random
import time
from typing import Dict, Any, List

from domain.Intent import Intent
from domain.Emotion import Emotion


class LoadTester:
    """
    Synthetic load generator for Iceberg 3.x.

    Generates:
      - randomized callers
      - randomized intents/emotions
      - burst loads
      - saturation loads
      - adversarial loads
      - governance drift pressure
      - replay determinism pressure
    """

    def __init__(self, simulator, cluster_runner, telemetry):
        self.simulator = simulator
        self.cluster = cluster_runner
        self.telemetry = telemetry

    # ---------------------------------------------------------
    # RANDOM CALLER GENERATION
    # ---------------------------------------------------------
    def _random_caller(self) -> Dict[str, Any]:
        return {
            "caller_id": f"c{random.randint(1000, 9999)}",
            "intent": random.choice(Intent.list()).name.lower(),
            "emotion": random.choice(Emotion.list()).name.lower(),
            "duration": random.uniform(5, 120),  # seconds
        }

    # ---------------------------------------------------------
    # BATCH GENERATION
    # ---------------------------------------------------------
    def generate_batch(self, n: int) -> List[Dict[str, Any]]:
        return [self._random_caller() for _ in range(n)]

    # ---------------------------------------------------------
    # BURST LOAD
    # ---------------------------------------------------------
    def burst(self, n: int) -> Dict[str, Any]:
        """
        Generate a sudden burst of callers.
        """
        batch = self.generate_batch(n)
        return self.cluster.run_batch(batch)

    # ---------------------------------------------------------
    # SATURATION LOAD
    # ---------------------------------------------------------
    def saturation(self, n: int, rounds: int) -> Dict[str, Any]:
        """
        Generate sustained high load.
        """
        results = []
        for _ in range(rounds):
            batch = self.generate_batch(n)
            out = self.cluster.run_batch(batch)
            results.append(out)
        return {"rounds": results}

    # ---------------------------------------------------------
    # ADVERSARIAL LOAD
    # ---------------------------------------------------------
    def adversarial(self, n: int) -> Dict[str, Any]:
        """
        Generate callers with extreme emotions + durations.
        """
        batch = []
        for _ in range(n):
            batch.append({
                "caller_id": f"a{random.randint(1000, 9999)}",
                "intent": random.choice(Intent.list()).name.lower(),
                "emotion": Emotion.ANGRY.name.lower(),
                "duration": random.uniform(120, 300),
            })
        return self.cluster.run_batch(batch)

    # ---------------------------------------------------------
    # GOVERNANCE DRIFT PRESSURE
    # ---------------------------------------------------------
    def governance_pressure(self, n: int) -> Dict[str, Any]:
        """
        Generate callers designed to push routing edges
        and latent drift.
        """
        batch = []
        for _ in range(n):
            batch.append({
                "caller_id": f"g{random.randint(1000, 9999)}",
                "intent": Intent.FRAUD.name.lower(),
                "emotion": Emotion.FRUSTRATED.name.lower(),
                "duration": random.uniform(30, 180),
            })
        return self.cluster.run_batch(batch)

    # ---------------------------------------------------------
    # FULL TEST SUITE
    # ---------------------------------------------------------
    def run_suite(self) -> Dict[str, Any]:
        """
        Run all load tests.
        """
        return {
            "burst": self.burst(50),
            "saturation": self.saturation(20, 10),
            "adversarial": self.adversarial(30),
            "governance_pressure": self.governance_pressure(40),
            "telemetry_snapshot": self.telemetry.snapshot(),
        }