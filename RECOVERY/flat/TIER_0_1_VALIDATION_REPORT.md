# Tier 0-1 Volume Validation — Independent Verification Package

**Purpose of this document:** everything needed for a second reviewer (human
or AI) to independently re-run, extend, or attack this validation, rather
than take the results below on faith. Every number in this document was
produced by running the code in this repository seconds before being
written down, then re-run a second time from a clean process to confirm
reproducibility. Both scripts are included in full at `Validation/` in this
repository, not just excerpted here.

**Scope claim, stated precisely so it isn't overread:** this validates that
Tiers 0 (`LatentPayload`/`DynamicState`) and 1 (`Simulator`/`CallerState`/
`QueueState`/`TelemetryKernel`/`ReplayEngine`/`Build_Graph`) hold their
stated invariants under high-volume, randomized, population-style load. It
does **not** validate the calibration of any tunable constant against real
call data (those remain explicitly unvalidated, see `LatentPayload.py`'s own
comments), and it does not touch Tier 2 (the queue-level ML engines) at all.

---

## 1. Methodology

Two separate runs, same population model, different depth:

- **Run A (Tier 0 isolated):** drives `LatentPayload.update_after_step()`
  directly against synthetic `DynamicState` sequences. No graph, no
  Simulator, no telemetry. Tests the friction engine in complete isolation.
- **Run B (Tier 0-1 combined):** routes the same style of population through
  the real `Simulator`, real `Build_Graph.build_graph()`, real
  `TelemetryKernel`, with a sampled full replay-reconstruction check via the
  real `ReplayEngine`. Tests whether Tier 1 preserves everything Tier 0
  guarantees once real graph traversal and telemetry recording are in the
  loop.

Both runs: **250,000 independent synthetic calls, fixed seed (42),
`numpy.random.RandomState`**. Fixed seed means every number in this document
is exactly reproducible, not a report of a run that happened once and can't
be checked again.

### Five randomized variables (chosen to represent a population, not
adversarial extremes -- extremes were already covered by earlier
Hypothesis-based fuzz testing, see `Tests/test_latent_fuzz.py`):

| Variable | Range | Meaning |
|---|---|---|
| `call_length` | 1-15 (int) | Number of `step()` invocations for this caller |
| `friction_rate` | 0.0-0.5 | Per-step probability of a misroute event |
| `wait_overrun_rate` | 0.0-0.5 | Per-step probability actual wait exceeds expected |
| `expected_wait_seconds` | 10.0-120.0 | This caller's baseline expected wait |
| `resolution_rate` | 0.0-0.5 | Per-step probability this step counts as resolved |

**One honest methodology correction worth disclosing:** the first version of
this test modeled resolution as a single event on a call's *last* step only.
That was wrong -- real resolution can happen at any point, including
multiple times in one call. `resolution_rate` was corrected to an
independent per-step roll, identical in structure to `friction_rate`, before
either of the runs below. The corrected version is what's reported here.

In Run B, caller `intent` is additionally randomized across all 7 real graph
branches (`billing`, `tech`, `cancel`, `upgrade`, `complaint`, `sales`,
`general`) -- not counted as one of "the 5," since it's a routing input, not
a behavioral variable.

---

## 2. Full code — Run A (Tier 0 isolated)

Also present, unmodified, at `Validation/tier0_stress_test.py` in this repo.

```python
import sys, time
sys.path.insert(0, "Latent")
sys.path.insert(0, "Domain")
import numpy as np
from LatentPayload import LatentPayload
from CallerState import DynamicState

N_CALLS = 250_000
rng = np.random.RandomState(42)

call_lengths       = rng.randint(1, 16, size=N_CALLS)
friction_rates      = rng.uniform(0.0, 0.5, size=N_CALLS)
wait_overrun_rates  = rng.uniform(0.0, 0.5, size=N_CALLS)
expected_waits      = rng.uniform(10.0, 120.0, size=N_CALLS)
resolution_rates    = rng.uniform(0.0, 0.5, size=N_CALLS)

violations = {
    "trust_bounds": 0, "volatility_bounds": 0, "memory_ceiling": 0,
    "memory_monotonic": 0, "friction_count_bounds": 0, "perceived_wait_bounds": 0,
}
final_trust, final_frust, final_memory, final_volatility, final_friction_count = ([] for _ in range(5))
max_consecutive_resolved, peak_trust_seen = [], []

t0 = time.time()
for i in range(N_CALLS):
    lp = LatentPayload()
    cd = DynamicState()
    steps = call_lengths[i]
    frate, wrate, ewait, rrate = friction_rates[i], wait_overrun_rates[i], expected_waits[i], resolution_rates[i]
    prev_memory = 0.0
    consec = max_consec = 0
    peak_trust = lp.trust_scalar

    friction_rolls   = rng.uniform(0, 1, size=steps)
    wait_rolls       = rng.uniform(0, 1, size=steps)
    resolution_rolls = rng.uniform(0, 1, size=steps)

    for s in range(steps):
        cd.friction_event = 1 if friction_rolls[s] < frate else 0
        cd.actual_wait = ewait * (rng.uniform(1.1, 3.0) if wait_rolls[s] < wrate else rng.uniform(0.3, 1.0))
        cd.expected_wait = ewait
        cd.resolved = bool(resolution_rolls[s] < rrate)

        consec = consec + 1 if cd.resolved else 0
        max_consec = max(max_consec, consec)

        lp.update_after_step(cd)
        peak_trust = max(peak_trust, lp.trust_scalar)

        if not (0.0 <= lp.trust_scalar <= 1.0): violations["trust_bounds"] += 1
        if not (0.0 <= lp.volatility <= 1.0): violations["volatility_bounds"] += 1
        if lp.memory_flag > 1.0: violations["memory_ceiling"] += 1
        if lp.memory_flag < prev_memory: violations["memory_monotonic"] += 1
        prev_memory = lp.memory_flag
        if not (0 <= lp.friction_count <= lp._FRICTION_CAP): violations["friction_count_bounds"] += 1
        if not (0.0 <= cd.perceived_wait <= 1.0): violations["perceived_wait_bounds"] += 1

    final_trust.append(lp.trust_scalar); final_frust.append(cd.frustration)
    final_memory.append(lp.memory_flag); final_volatility.append(lp.volatility)
    final_friction_count.append(lp.friction_count)
    max_consecutive_resolved.append(max_consec); peak_trust_seen.append(peak_trust)

# ... (summary statistics printed; see Validation/tier0_stress_test.py for full output code)
```

## 3. Full code — Run B (Tier 0-1 combined)

Also present, unmodified, at `Validation/tier0_1_stress_test.py` in this repo.

```python
import sys, time
sys.path.insert(0, "Latent"); sys.path.insert(0, "Domain"); sys.path.insert(0, "Sim")
sys.path.insert(0, "Model"); sys.path.insert(0, "SDK")
import numpy as np
from CallerState import CallerState
from Build_Graph import build_graph
from Telemetry import TelemetryKernel
from Replay import ReplayEngine
from Simulator import Simulator

N_CALLS = 250_000
REPLAY_SAMPLE_EVERY = 10  # full replay-equivalence check on 1 in 10 calls
rng = np.random.RandomState(42)

GRAPH = build_graph()  # built once, stateless, reused across all 250k calls
INTENTS = ["billing", "tech", "cancel", "upgrade", "complaint", "sales", "general"]

call_lengths       = rng.randint(1, 16, size=N_CALLS)
friction_rates      = rng.uniform(0.0, 0.5, size=N_CALLS)
wait_overrun_rates  = rng.uniform(0.0, 0.5, size=N_CALLS)
expected_waits      = rng.uniform(10.0, 120.0, size=N_CALLS)
resolution_rates    = rng.uniform(0.0, 0.5, size=N_CALLS)
caller_intents      = rng.choice(INTENTS, size=N_CALLS)

violations = {
    "trust_bounds": 0, "volatility_bounds": 0, "memory_ceiling": 0, "memory_monotonic": 0,
    "friction_count_bounds": 0, "perceived_wait_bounds": 0,
    "route_did_not_reach_agent": 0, "moved_flag_mismatch": 0,
    "max_steps_false_negative": 0, "replay_mismatch": 0,
}
replay_engine = ReplayEngine()

t0 = time.time()
for i in range(N_CALLS):
    telemetry = TelemetryKernel()
    sim = Simulator(graph=GRAPH, telemetry=telemetry, max_steps=815)
    caller = CallerState.new(f"c{i}", intent=caller_intents[i], emotion="NEUTRAL")

    steps = call_lengths[i]
    frate, wrate, ewait, rrate = friction_rates[i], wait_overrun_rates[i], expected_waits[i], resolution_rates[i]
    friction_rolls = rng.uniform(0, 1, size=steps)
    wait_rolls = rng.uniform(0, 1, size=steps)
    resolution_rolls = rng.uniform(0, 1, size=steps)
    prev_memory = 0.0

    for s in range(steps):
        caller.dynamic.friction_event = 1 if friction_rolls[s] < frate else 0
        caller.dynamic.actual_wait = ewait * (rng.uniform(1.1, 3.0) if wait_rolls[s] < wrate else rng.uniform(0.3, 1.0))
        caller.dynamic.expected_wait = ewait
        caller.dynamic.resolved = bool(resolution_rolls[s] < rrate)

        route_before = list(caller.route)
        try:
            result = sim.step(caller)
        except RuntimeError:
            violations["max_steps_false_negative"] += 1
            break

        if result["moved"] != (caller.route != route_before):
            violations["moved_flag_mismatch"] += 1

        lp = caller.latent
        if not (0.0 <= lp.trust_scalar <= 1.0): violations["trust_bounds"] += 1
        if not (0.0 <= lp.volatility <= 1.0): violations["volatility_bounds"] += 1
        if lp.memory_flag > 1.0: violations["memory_ceiling"] += 1
        if lp.memory_flag < prev_memory: violations["memory_monotonic"] += 1
        prev_memory = lp.memory_flag
        if not (0 <= lp.friction_count <= lp._FRICTION_CAP): violations["friction_count_bounds"] += 1
        if not (0.0 <= caller.dynamic.perceived_wait <= 1.0): violations["perceived_wait_bounds"] += 1

    if caller.route[-1] not in (f"{caller_intents[i]}_agent", "exit") and steps >= 4:
        violations["route_did_not_reach_agent"] += 1

    if i % REPLAY_SAMPLE_EVERY == 0:
        reconstructed = replay_engine.replay_from_events(telemetry.ledger)
        if reconstructed["callers"].get(caller.caller_id) != caller.to_dict():
            violations["replay_mismatch"] += 1

# ... (summary statistics printed; see Validation/tier0_1_stress_test.py for full output code)
```

---

## 4. Results, verbatim, two independent runs each (fixed seed -> identical output both times)

### Run A — Tier 0 isolated
```
250,000 calls, 2,000,705 total steps, ~16.3s

Constraint violations (target zero):
  trust_bounds: 0            volatility_bounds: 0
  memory_ceiling: 0          memory_monotonic: 0
  friction_count_bounds: 0   perceived_wait_bounds: 0

Final-state distributions:
  trust_scalar     mean=0.5056  std=0.0171  min=0.3003  max=0.5718
  frustration      mean=0.1748  std=0.3090  min=0.0000  max=3.7250
  memory_flag      mean=0.1033  std=0.1386  min=0.0000  max=1.0000
  volatility       mean=0.2716  std=0.0559  min=0.0823  max=0.6600
  friction_count   mean=2.5741  std=2.7265  min=0.0000  max=20.0000

Peak trust reached at ANY point, across all 250,000 calls: 0.5718
  (theoretical ceiling is 0.6; best case in the population was 11
  consecutive resolved steps, which the relief formula's exponential
  approach-to-ceiling math predicts would land near this value -- getting
  materially closer to 0.6 requires roughly 44 consecutive relief steps,
  which no realistic call length reaches)

Correlations:
  friction_rate vs final trust_scalar:   r=-0.2485
  resolution_rate vs final trust_scalar: r=+0.4663
  resolution_rate vs peak trust seen:    r=+0.4753
```

### Run B — Tier 0-1 combined
```
250,000 calls, 2,000,705 total steps, ~121-123s

Violations (target zero, ALL categories):
  trust_bounds: 0             volatility_bounds: 0
  memory_ceiling: 0           memory_monotonic: 0
  friction_count_bounds: 0    perceived_wait_bounds: 0
  route_did_not_reach_agent: 0    moved_flag_mismatch: 0
  max_steps_false_negative: 0     replay_mismatch: 0   <- 25,000 full
                                                            reconstructions
                                                            checked, all
                                                            exact matches

Sanity cross-check against Run A:
  trust_scalar  mean=0.5055  std=0.0171   (Run A: 0.5056 / 0.0171)
  memory_flag   mean=0.1037  std=0.1394   (Run A: 0.1033 / 0.1386)
```

---

## 5. What a reviewer should independently check

1. **Re-run both scripts verbatim.** Fixed seed means the output above
   should reproduce exactly. If it doesn't, something changed in
   `LatentPayload`, `Simulator`, or their dependencies since this was
   written -- that itself is the finding.
2. **Vary the seed.** Both scripts hardcode `RandomState(42)`. Try several
   other seeds and confirm violation counts stay at zero. A single seed,
   however large the sample, is still one draw from the input space.
3. **Widen the variable ranges.** All 5 variables were capped at 0.5 for the
   rate-type variables specifically to represent a *plausible* population,
   not worst-case. Pushing `friction_rate`/`resolution_rate` to 1.0, or
   `call_length` well past 15, is a legitimate stress extension this
   document doesn't cover.
4. **Check the `replay_mismatch` logic directly**, since it's the strongest
   single claim in Run B: pick one sampled call, print
   `caller.to_dict()` and `replay_engine.replay_from_events(telemetry.ledger)`
   side by side, confirm the equality by eye rather than trusting the
   aggregate counter.
5. **Confirm the two calibration findings independently**, since they're
   arithmetic claims, not just simulation output: verify that 11 consecutive
   relief steps from baseline 0.5 toward a ceiling of 0.6 at
   `_RELIEF_RATE=0.1` predicts ~0.569-0.571 by hand-computing the geometric
   series, and check it against the observed 0.5715-0.5718.

## 6. What this does NOT establish (stated so it can't be overclaimed)

- No tunable constant (`escalation_rate`, `_FRICTION_CAP`,
  `_TRUST_OVERSHOOT_CAP`, etc.) has been validated against real call center
  data. This run confirms the *logic* holds at volume, not that the
  *numbers* are correct for any real deployment.
- `max_steps` enforcement firing correctly (the true-positive case) is not
  exercised here -- call lengths never approached the 815 limit. That's
  covered separately in the unit test suite, not in this document.
- Nothing here touches Tier 2 (`PPOEngine`/`MARLEngine`) or above. Those
  remain built-and-disconnected per `SCORECARD.md`.
- Multi-call/session-boundary behavior (`reset_for_new_call`) is not
  exercised -- every synthetic caller here represents a single call, not a
  redialing history.
