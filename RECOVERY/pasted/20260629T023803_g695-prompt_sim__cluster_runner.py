# sim/cluster_runner.py
from __future__ import annotations
import concurrent.futures
from typing import Dict, Any, List


class ClusterRunner:
    """
    Lightweight parallel simulation runner for Iceberg 3.x.
    Uses Python's ThreadPoolExecutor for simplicity.
    Can be swapped for Ray/Dask/K8s jobs later.
    """

    def __init__(self, simulator, ppo, marl, staffing, workers: int = 4):
        self.sim = simulator
        self.ppo = ppo
        self.marl = marl
        self.staffing = staffing
        self.workers = workers

    # ---------------------------------------------------------
    # INTERNAL WORKER
    # ---------------------------------------------------------
    def _run_single(self, caller_id: str, intent: int, emotion: int, start_node: str) -> Dict[str, Any]:
        """
        Execute a single simulation in a worker thread.
        """
        caller = self.sim.create_caller(
            caller_id=caller_id,
            intent=self.sim.graph.intent_enum(intent),
            emotion=self.sim.graph.emotion_enum(emotion),
        )

        # PPO routing
        next_node, idx, logp, value = self.ppo.choose_action(caller, start_node)
        rl_action = {"routing": next_node}

        # Staffing RL
        staffing_action = self.staffing.propose_staffing()

        # MARL joint action (optional)
        joint_action, _ = self.marl.joint_action(caller, start_node)

        # Simulation step
        output = self.sim.step(caller, next_node)

        return {
            "caller_id": caller_id,
            "next_node": next_node,
            "output": output,
            "rl_action": rl_action,
            "staffing_action": staffing_action,
            "marl_joint": joint_action.tolist(),
        }

    # ---------------------------------------------------------
    # PARALLEL EXECUTION
    # ---------------------------------------------------------
    def run_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run a batch of simulation requests in parallel.
        Each item in batch:
          {
            "caller_id": str,
            "intent": int,
            "emotion": int,
            "start_node": str
          }
        """
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = [
                executor.submit(
                    self._run_single,
                    item["caller_id"],
                    item["intent"],
                    item["emotion"],
                    item["start_node"],
                )
                for item in batch
            ]

            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        return results