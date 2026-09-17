# sim/simulator.py
from __future__ import annotations
import time
import random
import torch
from typing import Dict, Any, List

from domain.Intent import Intent
from domain.Emotion import Emotion
from domain.CallerState import CallerState


class IcebergSimulator:
    """
    Core simulation engine for Iceberg 3.x.
    Handles:
      - caller creation
      - node transitions
      - queue updates
      - RL training batch generation
      - deterministic replay reconstruction
    """

    def __init__(self, graph, queues, latent):
        self.graph = graph
        self.queues = queues
        self.latent = latent

    # ---------------------------------------------------------
    # TIME
    # ---------------------------------------------------------
    def timestamp(self) -> float:
        return time.time()

    # ---------------------------------------------------------
    # CALLER CREATION
    # ---------------------------------------------------------
    def create_caller(self, caller_id: str, intent: Intent, emotion: Emotion) -> CallerState:
        caller = CallerState(
            caller_id=caller_id,
            intent=intent,
            emotion=emotion,
            posterior=self._init_posterior(),
        )
        return caller

    def reconstruct_caller(self, caller_id: str, posterior: Dict[str, float]) -> CallerState:
        """
        Used during deterministic replay.
        """
        caller = CallerState(
            caller_id=caller_id,
            intent=Intent(0),
            emotion=Emotion(0),
            posterior=posterior,
        )
        return caller

    def _init_posterior(self) -> Dict[str, float]:
        intents = ["billing", "tech", "fraud", "general"]
        return {i: 1.0 / len(intents) for i in intents}

    # ---------------------------------------------------------
    # QUEUE SNAPSHOT
    # ---------------------------------------------------------
    def queue_snapshot(self) -> Dict[str, Any]:
        snap = {}
        for qname, q in self.queues.items():
            snap[qname] = {
                "active_calls": q.active_calls,
                "staffing": q.staffing,
                "target_service_level": q.target_service_level,
                "abandonment_rate": q.abandonment_rate,
            }
        return snap

    # ---------------------------------------------------------
    # SIMULATION STEP
    # ---------------------------------------------------------
    def step(self, caller: CallerState, node_id: str) -> Dict[str, Any]:
        """
        Execute one node transition.
        """
        node = self.graph.nodes[node_id]

        # Update queue metrics
        if node.queue:
            q = self.queues[node.queue]
            q.active_calls += 1

        # Node logic
        output = {
            "node": node_id,
            "message": node.message,
            "actions": node.actions,
        }

        # Update caller dynamic state
        caller.dynamic.perceived_wait += random.uniform(0.1, 0.5)
        caller.dynamic.frustration += random.uniform(0.01, 0.05)

        return output

    # ---------------------------------------------------------
    # TRAINING BATCHES
    # ---------------------------------------------------------
    def generate_training_batch(self, ppo) -> List[Dict[str, Any]]:
        """
        Generate PPO training batch.
        """
        batch = []
        for _ in range(8):
            caller = self.create_caller(
                caller_id=f"train_{random.randint(1,99999)}",
                intent=Intent(0),
                emotion=Emotion(0),
            )
            state = ppo.encode_state(caller)
            node = "root"
            next_node, idx, logp, value = ppo.choose_action(caller, node)

            reward = random.uniform(-1, 1)

            batch.append({
                "state": state,
                "action_idx": idx,
                "old_logp": logp,
                "reward": reward,
                "value": value,
            })
        return batch

    def generate_marl_batch(self, marl) -> List[Dict[str, Any]]:
        batch = []
        for _ in range(8):
            caller = self.create_caller(
                caller_id=f"marl_{random.randint(1,99999)}",
                intent=Intent(0),
                emotion=Emotion(0),
            )
            state = marl.encode_state(caller)
            joint, _ = marl.joint_action(caller, "root")
            reward = random.uniform(-1, 1)

            batch.append({
                "state": state,
                "joint_action": joint,
                "reward": reward,
            })
        return batch

    def generate_staffing_batch(self, staffing) -> List[Dict[str, Any]]:
        batch = []
        for _ in range(8):
            state = staffing.encode_state()
            deltas = staffing.propose_staffing()
            reward = random.uniform(-1, 1)

            batch.append({
                "state": state,
                "deltas": deltas,
                "reward": reward,
            })
        return batch