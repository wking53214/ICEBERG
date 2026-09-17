# Iceberg Scorecard — 2026-07-02

Status categories used below, deliberately qualitative, not numeric. A single
decimal score (e.g. "9.5/10") implies a precision this codebase's history
doesn't support — the "excellent execution kernel" verdict from the first
outside review turned out to be describing a Simulator that silently never
ran. Categories instead:

- **PROVEN** — built, tested, verified live and/or fuzzed/red-teamed.
- **BUILT / DISCONNECTED** — code exists, passes its own tests, but is not
  wired to real data or the rest of the current architecture (orphaned or
  mocked).
- **SPEC ONLY** — designed in a written document, zero code.
- **SKETCHED** — discussed and reasoned through in conversation, not yet
  written up as a formal spec.
- **NOT STARTED** — named, nothing exists.
- **REMOVED (by design)** — deliberately cut. Not a gap.
- **PRE-EXISTING, OUT OF SCOPE** — part of the original broken scaffold from
  before this rebuild began. Never touched, never claimed as in-scope.

---

## Tier 0 — Friction measurement (the engine)

| Component | Status | Notes |
|---|---|---|
| `LatentPayload` | **PROVEN** | 3 red-team rounds with real fixes each, live through the real Simulator, 4,000+ randomized fuzz trajectories, zero invariant violations. |
| `CallerState` / `DynamicState` | **PROVEN** | `.new()`, `.route`, full snapshot export verified against replay. |
| `QueueState` | **PROVEN** | Basic mechanics only — no stress/load semantics yet (see Tier 3). |

This tier is the strongest thing in the codebase, and it's the one piece that
survived every review, every red-team pass, and every architecture change
without needing to be re-thought, only re-verified.

## Tier 1 — Deterministic core (the drivetrain)

| Component | Status | Notes |
|---|---|---|
| `Simulator` | **PROVEN** | Rebuilt to the adopted architecture, `max_steps` now actually enforced per-caller, graph validation added, richer return value. |
| `TelemetryKernel` | **PROVEN** | Had a real non-determinism bug (`time.time()` timestamps) — found and fixed, not just inherited-and-left. |
| `ReplayEngine` | **PROVEN** | Fully event-sourced; reconstructs from ledger alone, no live simulator reference needed. |
| `ClusterRunner` | **PROVEN, with one honestly-tracked gap** | 8/9 real tests pass. The 9th is `xfail` + a companion characterization test — the gap is real (no shared telemetry channel), documented in the code, not hidden. |
| `Build_Graph` / `RoutingGraph` | **PROVEN** | 6/6, including hash/snapshot equivalence. |

Test suite for this tier plus Tier 0: **86 passed, 1 skipped (no GPU
hardware), 1 xfailed (documented, not a defect).** Zero unexplained red.

## Tier 2 — Queue-level ML ("transmission")

| Component | Status | Notes |
|---|---|---|
| `PPOEngine` | **BUILT / DISCONNECTED** | Passes its own tests. Direction question resolved (higher stress-concentration → higher priority is correct). But it still takes an arbitrary `load` number with no real source — the thing that's supposed to feed it doesn't exist (Tier 3). Correctly shaped, fed nothing real yet. |
| `MARLEngine` | **BUILT / DISCONNECTED** | Same as above. |
| `StaffingRLEngine` | **REMOVED (by design)** | Not a gap — epistemically impossible from Iceberg's side of the ACD door (needs AHT, shrinkage, answered-vs-offered, none of which Iceberg can ever observe). |
| `BayesianIntentEngineGPU` (`bayes_gpu`) | **BUILT / DISCONNECTED** | A real bug was found and fixed here (unclamped `log(0)` → NaN, which broke determinism itself). Correct in isolation. Referenced by nothing except its own tests and the original broken scaffold. Fully orphaned. |

## Tier 3 — Aggregation / rollup layer

| Component | Status | Notes |
|---|---|---|
| Per-queue stress-concentration composite (frustration/trust-decay/volatility → one number) | **NOT STARTED** | This is what Tier 2 is actually waiting on. Without it, "load" is a placeholder. |
| General aggregation layer ("C") | **NOT STARTED** | The thing that turns thousands of individual `CallerState.snapshot()`s into queue- or menu-level findings. Nothing above Tier 1 can become a real recommendation without this. |

## Tier 4 — Governance

| Component | Status | Notes |
|---|---|---|
| `GovernanceEnvelope` | **NOT STARTED** | Referenced by name throughout the original scaffold and later design docs. Never has been real code. |
| Target Manifest (observe→lock→consult→declare→pursue→govern) | **SPEC ONLY** | Written, zero implementation. |
| Lever Registry (platform/deployment levers, open friction-tag vocabulary) | **SPEC ONLY** | Written, zero implementation. |
| Graph tagging (`delivers_payload`, `company_benefit`, `detriment`, `declared_intent`) | **SKETCHED** | Reasoned through in conversation days ago, never formalized as a spec, zero code. |
| Friction-type taxonomy (distinguishing re-ask friction from misroute friction, etc.) | **SKETCHED** | `friction_event` today is a flat, undifferentiated count. |

## Tier 5 — Business-facing recommendation surface

| Component | Status | Notes |
|---|---|---|
| Change-governance layer (concrete diff → declare → deploy → measure) | **SKETCHED** | Reasoned through, not yet a formal spec. |
| Menu-order recommendations | **BLOCKED** | On Tier 3. |
| Dead-end / detriment flagging | **BLOCKED** | On Tier 4's graph tagging. |
| Re-authentication friction flagging | **BLOCKED** | On Tier 4's friction taxonomy. |
| `mitigation_event` (wait-message experimentation) | **SKETCHED** | Real calibration numbers already gathered (silence +36% perceived wait, content −33%), zero code. |
| Peak-frustration / peak-end tracking | **SKETCHED** | Zero code. |
| Whisper prompt (descriptive ACD handoff) | **SKETCHED, least blocked of this tier** | Everything it needs already exists in `CallerState.snapshot()`. Genuinely close to buildable, just never scheduled. |

## Tier 6 — Interfaces

| Component | Status | Notes |
|---|---|---|
| `IcebergAPI` | **BUILT / DISCONNECTED — flagged explicitly** | Its own tests pass (`test_api_contract.py`, 3/3). But it wraps `MockSimulator`, not the real `Simulator`, and its call site still uses the *pre-adoption* `step(caller, start_node)` signature — it isn't just mocked, it's mocked against an architecture that no longer exists. Green tests here should not be read as "the API works." |
| Dashboard / Admin / `Main.py` | **PRE-EXISTING, OUT OF SCOPE** | Imports modules that have never existed (`dashboard_server`, `domain.governance_envelope`). Part of the original scaffold, never touched, never claimed as working. |

---

## Reading this honestly

The foundation (Tiers 0–1) is real and proven, more rigorously than almost
anything else in this session, three red-team rounds, a live rebuild after
adopting a different architecture, 4,000+ fuzz cases, zero unexplained test
failures. That part of the "car" is genuinely done.

Everything from Tier 2 up is either disconnected from real data, specified
but unbuilt, or blocked behind something else that's unbuilt. That's not a
regression from where the project stood a few sessions ago — if anything,
the scope of "done" grew today (Target Manifest, Lever Registry, the
friction-type taxonomy, the aggregation layer all got *named* as necessary
pieces that weren't even on the list before). Progress and the size of the
remaining work grew together, which is normal for a project this honestly
scoped, not a sign of stalling.

The single most important trap to avoid reading into this table: **a
component's tests passing is not the same claim as a component being real
and connected.** `IcebergAPI` and `bayes_gpu` both prove that directly —
green suites, genuinely correct code, and both disconnected from the actual
system. That gap is exactly what this scorecard exists to make visible
instead of letting a clean pytest run imply more than it does.
