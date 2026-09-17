# replay/ReplayVerifier.py
from __future__ import annotations
import json
import hashlib
from typing import Dict, Any, List


class ReplayVerifier:
    """
    Validates deterministic replay integrity:
      - structural hash consistency
      - caller dynamic reconstruction
      - latent reconstruction
      - PPO action consistency
      - MARL joint-action consistency
      - staffing RL deltas
    """

    def __init__(self, graph, simulator):
        self.graph = graph
        self.simulator = simulator

    # ---------------------------------------------------------
    # STRUCTURAL HASH
    # ---------------------------------------------------------
    def compute_structural_hash(self) -> str:
        raw = json.dumps(self.graph.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def verify_structural_hash(self, expected: str) -> bool:
        return self.compute_structural_hash() == expected

    # ---------------------------------------------------------
    # LEDGER LOADING
    # ---------------------------------------------------------
    def load_ledger(self, path: str) -> List[Dict[str, Any]]:
        events = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                events.append(json.loads(line))
        return events

    # ---------------------------------------------------------
    # EVENT REPLAY
    # ---------------------------------------------------------
    def replay_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconstruct a single event using the simulator.
        """

        caller_data = event["caller"]
        from domain.Intent import Intent
        from domain.Emotion import Emotion
        from domain.CallerState import CallerState

        caller = CallerState(
            caller_id=caller_data["caller_id"],
            intent=Intent.from_str(caller_data["intent"]),
            emotion=Emotion.from_str(caller_data["emotion"]),
            posterior=caller_data["posterior"],
        )

        caller.dynamic.perceived_wait = caller_data["dynamic"]["perceived_wait"]
        caller.dynamic.frustration = caller_data["dynamic"]["frustration"]

        # Latent reconstruction
        self.simulator.latent.load_from_dict(event["latent"])

        # Replay the step
        reconstructed = self.simulator.step(caller, event["node"])
        return reconstructed

    # ---------------------------------------------------------
    # FULL VERIFICATION
    # ---------------------------------------------------------
    def verify(self, path: str) -> Dict[str, Any]:
        ledger = self.load_ledger(path)
        results = []

        for event in ledger:
            reconstructed = self.replay_event(event)

            structural_ok = self.verify_structural_hash(event["structural_hash"])

            dyn_ok = (
                abs(event["dynamic"]["perceived_wait"] -
                    reconstructed["snapshot"]["caller"]["dynamic"]["perceived_wait"]) < 1e-9
                and
                abs(event["dynamic"]["frustration"] -
                    reconstructed["snapshot"]["caller"]["dynamic"]["frustration"]) < 1e-9
            )

            latent_ok = (
                event["latent"] == reconstructed["latent"]
            )

            ppo_ok = (
                event["ppo"]["action_idx"] == reconstructed["ppo"]["action_idx"]
                and abs(event["ppo"]["logp"] - reconstructed["ppo"]["logp"]) < 1e-9
                and abs(event["ppo"]["value"] - reconstructed["ppo"]["value"]) < 1e-9
            )

            marl_ok = (
                event["marl"]["joint"] == reconstructed["marl"]["joint"]
            )

            staffing_ok = (
                event["staffing"] == reconstructed["staffing"]
            )

            results.append({
                "caller_id": event["caller_id"],
                "node": event["node_id"],
                "next_node": event["next_node"],
                "structural_hash": structural_ok,
                "dynamics": dyn_ok,
                "latent": latent_ok,
                "ppo": ppo_ok,
                "marl": marl_ok,
                "staffing": staffing_ok,
                "passed": all([structural_ok, dyn_ok, latent_ok, ppo_ok, marl_ok, staffing_ok]),
            })

        return {
            "total_events": len(results),
            "passed": sum(r["passed"] for r in results),
            "failed": len(results) - sum(r["passed"] for r in results),
            "details": results,
        }