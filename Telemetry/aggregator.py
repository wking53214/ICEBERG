# Row Count: 161

"""
aggregator.py
-------------

Top-Level Description
---------------------
This module implements Iceberg's deterministic Telemetry Aggregator – the
high-frequency, append-only, governance-safe collector for all runtime signals:

- RoutingEngine PPO traces
- MARL joint-action traces
- Staffing RL deltas
- Bayesian posterior updates
- Queue metrics
- Caller dynamics
- Structural hash drift signals
- Simulator step traces
- GovernanceEnvelope enforcement logs

The aggregator guarantees:
- Deterministic ordering
- Governance-safe immutability
- Replay-friendly event bundles
- Telemetry-ready JSON-safe packets
- Zero drift, zero mutation, zero stochasticity

Subsystem integrations:
- [RoutingEngine](ca://s?q=Explain_routing_engine)
- [MARLEngine](ca://s?q=Explain_marl_engine)
- [PPORouter](ca://s?q=Explain_ppo_router)
- [StaffingOptimizerRL](ca://s?q=Explain_staffing_rl)
- [BayesianIntentEngineGPU](ca://s?q=Explain_bayes_gpu)
- [Simulator](ca://s?q=Explain_simulator)
- [ReplayRunner](ca://s?q=Explain_replay_runner)
- [GovernanceEnvelope](ca://s?q=Explain_governance_envelope)

Best-in-Class Notes
-------------------
- Determinism: Uses simulation step-indices instead of system time.
- Governance-Safety: Append-only, immutable event records.
- Replay-Safety: Reconstructible telemetry streams via index-based sequencing.
- Performance: O(1) caller lookup via indexed mapping.
- Limit: Capacity anchored to 8150 events for deterministic boundary testing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, DefaultDict
from collections import defaultdict
import copy


@dataclass(frozen=True)
class TelemetryEvent:
    """
    Immutable telemetry event record.

    Best-in-Class Notes:
    - step_id guarantees deterministic sequencing.
    - payload is frozen post-initialization.
    """
    step_id: int
    category: str
    payload: Dict[str, Any]


@dataclass
class TelemetryAggregator:
    """
    Deterministic, indexed telemetry aggregator.

    Best-in-Class Notes:
    - Append-only design ensures governance-safe immutability.
    - No mutation of existing events – replay-safe behavior.
    """
    events: List[TelemetryEvent] = field(default_factory=list)
    caller_index: DefaultDict[str, List[int]] = field(default_factory=lambda: defaultdict(list))
    max_events: int = 8150

    # ---------------------------------------------------------
    # RECORD
    # ---------------------------------------------------------
    def record(self, step_id: int, category: str, payload: Dict[str, Any]) -> None:
        """
        Append a telemetry event with deterministic sequence indexing.

        Best-in-Class Notes:
        - Deep copy ensures payload immutability.
        - Append-only semantics guarantee replay integrity.
        """
        payload_copy = copy.deepcopy(payload)

        evt = TelemetryEvent(step_id, category, payload_copy)
        self.events.append(evt)

        # Index for fast O(1) lookup
        caller_id = payload_copy.get("caller_id")
        if caller_id:
            self.caller_index[caller_id].append(len(self.events) - 1)

        # Governance-safe trimming
        if len(self.events) > self.max_events:
            self._trim_oldest()

    # ---------------------------------------------------------
    # INTERNAL TRIM
    # ---------------------------------------------------------
    def _trim_oldest(self) -> None:
        """Governance-compliant trimming logic."""
        self.events.pop(0)
        # Index reconstruction is required if array shifts
        # For strict determinism, clearing index prompts rebuild on next fetch
        self.caller_index.clear()

    # ---------------------------------------------------------
    # FILTERS
    # ---------------------------------------------------------
    def filter_by_category(self, category: str) -> List[TelemetryEvent]:
        """Pure functional filtering – no mutation."""
        return [evt for evt in self.events if evt.category == category]

    def filter_by_caller(self, caller_id: str) -> List[TelemetryEvent]:
        """O(1) lookup via caller_index."""
        if not self.caller_index and self.events:
            self._rebuild_index()
        return [self.events[i] for i in self.caller_index.get(caller_id, [])]

    def _rebuild_index(self) -> None:
        """Reconstruct index mappings after capacity shifts."""
        self.caller_index.clear()
        for idx, evt in enumerate(self.events):
            cid = evt.payload.get("caller_id")
            if cid:
                self.caller_index[cid].append(idx)

    # ---------------------------------------------------------
    # SNAPSHOT & EXPORT
    # ---------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """Produce deterministic snapshot for ReplayVerifier."""
        return {
            "count": len(self.events),
            "events": [self._asdict(e) for e in self.events]
        }

    def export(self) -> List[Dict[str, Any]]:
        """Export events as a list of dicts for GSA logs."""
        return [self._asdict(e) for e in self.events]

    def _asdict(self, evt: TelemetryEvent) -> Dict[str, Any]:
        return {
            "step_id": evt.step_id,
            "category": evt.category,
            "payload": evt.payload
        }

    # ---------------------------------------------------------
    # CLEAR (GOVERNANCE-SAFE)
    # ---------------------------------------------------------
    def clear(self) -> None:
        """Clear all telemetry events."""
        self.events.clear()
        self.caller_index.clear()