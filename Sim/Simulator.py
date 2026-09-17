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
- PPOEngine / MARLEngine (Engines/): the actual ML layer, operates ONLY on
  aggregated queue load, never on an individual caller. Not called from
  here. This is the queue-level "transmission" layer from William's
  transmission/differential discussion -- genuinely separate from per-caller
  traversal, not injected into it.

StaffingRLEngine removed 2026-07-02 (not demoted, not stubbed -- deleted).
Iceberg's objective ends at the ACD door: it finds and reduces pre-ACD
friction, it does not measure its own success (that's containment,
measured externally via inbound-vs-offered call ratios) and it does not
make staffing decisions. Staffing math requires AHT, shrinkage, and
answered-vs-offered data -- none of which Iceberg can ever observe, since
none of it exists before a caller crosses into the ACD. Not a scope
preference; epistemically impossible from where this system sits.

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
    - No trained/learned ML in the per-step path -- that's a separate,
      queue-level layer (see module docstring). Clarified 2026-07-01: this
      does NOT mean the step is behavior-free -- LatentPayload's deterministic
      frustration/trust rules still run every step. "No ML" means no policy
      inference happens here, not "nothing behavioral happens here."
    - max_steps is now enforced PER CALLER (fixed 2026-07-01), using
      caller.latent.step_index, which already existed as a per-caller counter
      -- it just wasn't connected to this limit. Verified safe against the
      full test suite: no single caller is ever stepped more than 8 times
      anywhere in the tests, all with max_steps=10. A SIMULATOR-wide counter
      would still be wrong (test_multiple_callers_deterministic steps 3
      different callers 5 times each = 15 total calls through one instance),
      which is why this couldn't just be the old global counter re-added.
    """
    graph: Any
    telemetry: Any
    max_steps: int = 815

    def __post_init__(self):
        """
        Fixed 2026-07-01: light shape validation at construction instead of a
        confusing AttributeError deep inside traversal. RoutingGraph.validate()
        already checks neighbor-reference integrity at build_graph() time --
        this is a cheaper, separate check that graph itself looks like a
        RoutingGraph at all, in case one is ever constructed by hand and
        passed in directly.
        """
        if not hasattr(self.graph, "nodes"):
            raise ValueError("Simulator.graph must expose a .nodes mapping (got: %r)" % type(self.graph))

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

        Fixed 2026-07-01: enforces max_steps per caller (see class docstring)
        and returns a richer result -- moved/content_hash/structural_hash
        added, caller_id/next_node kept exactly as before, so this is
        additive, not a breaking change to anything reading the return value.
        Deliberately two separate, explicitly-labeled hash keys rather than
        one ambiguous "hash" -- collapsing them back into one would reopen
        the exact "does hash-changed mean real-state-changed" ambiguity
        content_hash/structural_hash were built to resolve this morning.
        """
        if caller.latent is not None and caller.latent.step_index >= self.max_steps:
            raise RuntimeError(
                f"GSA Violation: caller {caller.caller_id} exceeded max_steps ({self.max_steps})."
            )

        current = caller.route[-1] if caller.route else "root"
        next_node = self._next_node(caller)
        moved = next_node != current

        if moved:
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

        result = {"caller_id": caller.caller_id, "next_node": next_node, "moved": moved}
        if caller.latent is not None:
            result["content_hash"] = caller.latent.content_hash()
            result["structural_hash"] = caller.latent.structural_hash()
        return result

    def update_queue(self, queue: "QueueState", delta: int = 1) -> "QueueState":
        """
        Deterministic queue transition, records a full-state snapshot for replay.

        Fixed 2026-07-01: delta is now an optional parameter (default 1,
        identical to the previous hardcoded behavior -- backward compatible
        with every existing call site) instead of always incrementing by
        exactly one. Lets a caller represent a call LEAVING a queue (delta=-1)
        without a second method. Does NOT connect this to any staffing
        engine's output -- StaffingRLEngine was removed 2026-07-02, staffing
        decisions live past the ACD door, outside Iceberg's scope entirely.
        """
        queue.update_active_calls(delta)
        if self.telemetry is not None:
            self.telemetry.record("queue_update", {
                "name": queue.name,
                "state": queue.to_dict(),
            })
        return queue
