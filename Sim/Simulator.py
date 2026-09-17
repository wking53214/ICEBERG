# Row Count: 118

"""
Simulator.py
------------

Deterministic per-caller graph-traversal engine.

REWRITTEN 2026-07-01. This replaces the earlier Simulator design (which took
routing/staffing/bayes/queues/recorder/governance as injected per-step
dependencies). That design was fixed and proven live earlier the same day --
3 integration tests, 4000 fuzz trajectories -- but turned out to diverge from
the architecture six independent test files (test_simulator_core,
test_cluster_runner, test_replay_engine, test_rl_ppo, test_rl_marl,
test_staffing_rl) all consistently assumed. Adopted per William's decision.

The new split:
- Simulator: simple, deterministic, NO ML. Walks one caller through the
  graph. Routing at a branch point follows the caller's own intent field --
  no policy engine needed for that decision.
- PPOEngine / MARLEngine / StaffingRLEngine (Engines/): the actual ML layer,
  operates ONLY on aggregated queue load, never on an individual caller. Not
  called from here. This is the queue-level "transmission" layer from
  William's transmission/differential discussion -- genuinely separate from
  per-caller traversal, not injected into it.

The friction engine (LatentPayload/DynamicState) is preserved exactly as
built and hardened this morning -- it evolves every step regardless of which
Simulator shape is doing the stepping, since frustration/trust are properties
of the caller, not of the routing mechanism.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class Simulator:
    """
    Deterministic graph-traversal simulator.

    Governance Notes:
    - No routing/staffing/bayes ML in the per-step path -- that's a separate,
      queue-level layer (see module docstring).
    - max_steps is stored and compared (per test_simulator_build_deterministic)
      but NOT enforced as a hard per-call raise: a single Simulator instance
      steps MANY callers across its lifetime (test_multiple_callers_deterministic
      steps 3 callers x 5 times = 15 calls through one instance with
      max_steps=10), so a simulator-wide counter would break that test, and
      no test exercises per-caller enforcement either. Flagged as an open
      governance gap, not silently decided -- see CHANGES.md.
    """
    graph: Any
    telemetry: Any
    max_steps: int = 815

    def _next_node(self, caller: "CallerState") -> str:
        """
        Deterministic traversal rule, no randomness, no ML:
        - Terminal node (no neighbors): stay.
        - Single neighbor: follow it, no decision to make.
        - Branch point (multiple neighbors, e.g. intent_menu): prefer the
          neighbor matching the caller's own intent (f"{intent}_queue"),
          since the graph's own naming scheme is intent-keyed. Falls back to
          the first neighbor (stable: graph nodes preserve insertion order)
          if the caller's intent doesn't match any branch.
        """
        current = caller.route[-1] if caller.route else "root"
        node = self.graph.nodes.get(current)
        if node is None or not node.neighbors:
            return current
        if len(node.neighbors) == 1:
            return node.neighbors[0]
        preferred = f"{caller.intent}_queue"
        return preferred if preferred in node.neighbors else node.neighbors[0]

    def step(self, caller: "CallerState") -> dict:
        """
        Advance one caller by one step: traverse the graph, evolve latent
        state, record a full-state telemetry snapshot for replay.
        """
        current = caller.route[-1] if caller.route else "root"
        next_node = self._next_node(caller)

        if next_node != current:
            caller.route.append(next_node)
        caller.next_node = next_node

        # Latent evolution: unchanged logic from this morning's hardened
        # friction engine. Runs every step regardless of graph movement --
        # frustration/trust are about what happened to the caller, not about
        # whether they moved to a new node this particular step.
        if caller.latent is not None:
            caller.latent.update_after_step(caller.dynamic)

        if self.telemetry is not None:
            self.telemetry.record("step", {
                "caller_id": caller.caller_id,
                "state": caller.to_dict(),
            })

        return {"caller_id": caller.caller_id, "next_node": next_node}

    def update_queue(self, queue: "QueueState") -> "QueueState":
        """Deterministic queue transition, records a full-state snapshot for replay."""
        queue.update_active_calls(1)
        if self.telemetry is not None:
            self.telemetry.record("queue_update", {
                "name": queue.name,
                "state": queue.to_dict(),
            })
        return queue
