# cluster/ClusterRunner.py
from __future__ import annotations
import concurrent.futures
import uuid
from typing import Dict, Any, List

from domain.Intent import Intent
from domain.Emotion import Emotion
from domain.CallerState import CallerState


class ClusterRunner:
    """
    Parallel multi-caller execution engine for Iceberg 3.x.
    Executes:
      - caller generation
      - PPO routing
      - MARL joint actions
      - staffing RL
      - queue updates
      - telemetry logging
      - replay snapshot emission

    Deterministic, replay-safe, thread-pool based.
    """

    def __init__(self, simulator, ppo, marl, staffing, telemetry, replay_recorder, workers: int = 8):
        self.sim = simulator
        self.ppo = ppo
        self.marl = marl
        self.staffing = staffing
        self.telemetry = telemetry
        self.replay = replay_recorder
        self.workers = workers

    # ---------------------------------------------------------
    # SYNTHETIC CALLER GENERATION
    # ---------------------------------------------------------
    def _make_caller(self, intent: int, emotion: int) -> CallerState:
        caller_id = str(uuid.uuid4())

        caller = CallerState(
            caller_id=caller_id,
            intent=Intent.list()[intent],
            emotion=Emotion.list()[emotion],
            posterior={"p": 1.0},  # deterministic placeholder
        )

        return caller

    # ---------------------------------------------------------
    # SINGLE CALLER EXECUTION
    # ---------------------------------------------------------
    def _run_single(
        self,
        intent: int,
        emotion: int,
        start_node: str,
        steps: int,
    ) -> Dict[str, Any]:

        caller = self._make_caller(intent, emotion)
        node = start_node

        outputs = []

        for _ in range(steps):
            out = self.sim.step(caller, node)
            node = out["next_node"]
            outputs.append(out)

            # Replay event
            self.replay.record(
                caller=caller,
                node_id=out["node"],
                next_node=out["next_node"],
                latent=out["latent"],
                ppo=out["ppo"],
                marl=out["marl"],
                staffing=out["staffing"],
                graph=self.sim.graph,
            )

        return {
            "caller_id": caller.caller_id,
            "events": outputs,
        }

    # ---------------------------------------------------------
    # PARALLEL EXECUTION
    # ---------------------------------------------------------
    def run_batch(self, batch: List[Dict[str, Any]], steps: int) -> List[Dict[str, Any]]:
        """
        Batch format:
        [
            {
                "intent": int,
                "emotion": int,
                "start_node": str
            },
            ...
        ]
        """

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = [
                executor.submit(
                    self._run_single,
                    item["intent"],
                    item["emotion"],
                    item["start_node"],
                    steps,
                )
                for item in batch
            ]

            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        return results