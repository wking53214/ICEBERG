# Target Manifest Specification

**Status:** Design spec, stasis (not yet implemented)
**Depends on:** `LatentPayload` (done), `CallerState.snapshot()` (done)
**Blocks:** `containment_validity`, `declared_intent`, sandbox stop-thresholds — all three
turn out to be instances of this one mechanism, not separate features.

---

## 0. Why this exists

Every stasis item from today that involves a number someone has to choose —
when is friction bad enough to override an exit, what counts as a well-handled
recovery, when does a training run stop, what abandonment ceiling is acceptable —
ran into the same missing piece: **there was nowhere in the architecture for that
choice to be made on the record.** It was always implicit. "Someone decides."

The Target Manifest is that place. It exists to keep three roles permanently
separate, because collapsing any two of them reopens the exact containment-gaming
failure mode this whole system was built to prevent:

| Role | Who | Job |
|---|---|---|
| **Declares the target** | The business | Decides what "acceptable" means |
| **Pursues the target** | The engine (friction layer + sandbox + routing) | Tries to hit it |
| **Audits the pursuit** | `GovernanceEnvelope` | Checks whether the pursuit was honest |

If the same component sets the target and audits whether it was hit, the referee
is a player. The Manifest's entire job is making sure that never happens quietly.

---

## 1. Lifecycle: Observe → Lock → Consult → Declare → Pursue → Govern

```
┌─────────────┐     ┌────────┐     ┌──────────┐     ┌───────────┐     ┌─────────┐
│ OBSERVATION │ ──> │  LOCK  │ ──> │ CONSULT  │ ──> │ DECLARE   │ ──> │ PURSUE  │
│ (read-only) │     │(hash)  │     │(recommend)│     │(business) │     │(sandbox │
└─────────────┘     └────────┘     └──────────┘     └───────────┘     │ + live) │
                                                                        └────┬────┘
                                                                             │
                                                                        ┌────▼────┐
                                                                        │ GOVERN  │
                                                                        │(ongoing)│
                                                                        └─────────┘
```

The order is a hard rule, not a suggestion: **the report locks before any target
conversation starts.** If the report can still change after someone's seen what
target they want, it stops being a measurement and becomes a case being built for
a number already picked. Locking is what makes "the report modifies the decision,
not the other way around" true by construction instead of by intention.

---

## 2. Phase 1 — Observation

Two data sources, and they are not the same kind of evidence:

- **Live (`measured`)** — Iceberg runs in read-only mode against real traffic.
  Zero decision authority; it watches and records via the same `LatentPayload`
  / `CallerState.snapshot()` machinery already built, just with no routing
  output consumed by anything.
- **Historical (`reconstructed`)** — prior-system logs (call duration, transfer
  counts, abandon flags) run back through the friction model to infer what
  frustration probably looked like before Iceberg existed.

Every number in the resulting report carries one of those two tags. Don't let
an inference wear a measurement's clothes.

**Coverage window:** minimum one full billing/business cycle (monthly, not
weekly — cyclicality like month-end billing spikes will hide inside a
single-week sample).

**Integrity flag:** any historical period where the prior system's containment
number can't be verified as unmanipulated (see `containment_validity`, §5) is
tagged `integrity_unknown` rather than trusted at face value. A baseline built
on a number the old system may have quietly engineered is a baseline built on
sand — flag it, don't discard it, but don't let it anchor a target unchallenged.

---

## 3. Phase 2 — Lock

The completed observation report is hashed (same SHA-256 structural hashing
discipline as `LatentPayload`) and becomes immutable. This happens **before**
anyone, including William, begins forming a recommendation. No edits after
this point, only new, separately-hashed follow-up reports.

---

## 4. Phase 3 — Consult

William's role here is **consultancy, not direction.** The distinction matters
structurally, not just semantically: a consultant recommending achievable-looking
targets for their own system is a known conflict of interest, and the fix isn't
removing his input, his operational background is exactly why it's needed. The
fix is making the input visible and separately accountable from the decision.

**Recommendation record** (consultant input):
```
{
  "manifest_id": "...",
  "recommended_by": "William",
  "based_on_report_hash": "<locked observation report hash>",
  "recommendation": { ... },
  "rationale": "...",
  "timestamp": "..."
}
```
This is advisory. It is never what governance audits against.

---

## 5. Phase 4 — Declare

The business makes the actual binding choice. This is a **separate hashed
record** from the recommendation, even if the business adopts William's
recommendation verbatim — the point isn't that they might differ, it's that
authorship and authority stay distinguishable on the record either way.

**Declaration record** (binding, what governance checks against):
```
{
  "manifest_id": "...",
  "declared_by": "<business role/name>",
  "based_on_recommendation": "<recommendation record id, optional>",
  "target": {
    "metric": "friction_reduction",       // NEVER containment — see §6
    "definition": "...",
    "threshold": ...,
    "measurement_window": "..."
  },
  "declared_at": "...",
  "status": "active"
}
```

This is the record type every other stasis item's "someone decides" moment
should resolve to:
- `declared_intent` (graph node tagging) is a Declaration scoped to one node.
- `containment_validity`'s crisis override reason/expected-end-condition is a
  Declaration scoped to an emergency window.
- A sandbox training run's stop condition is a Declaration scoped to one
  training cycle.

Same record shape, same locking discipline, different scope. Not three
features — one mechanism, reused.

---

## 6. Hard constraint: the target metric can never be containment

Per the mantra, containment is a byproduct, not a goal. A Declaration whose
`metric` field is containment, or any proxy for "did the caller stay on the
line" rather than "was the caller's friction reduced," is invalid by
construction. This needs to be a schema-level constraint, not a style
guideline, or the Manifest becomes the exact loophole it exists to close.

Corollary from the sandbox conversation: the metric must count abandoned
callers as maximal friction, not as missing data points. A metric that only
scores *resolved* calls lets a policy improve its number by causing more
abandonment, the same failure wearing a new costume.

---

## 7. Phase 5/6 — Pursue and Govern

Out of scope for this spec (covered by existing/stasis items):
- Pursue = sandbox training (constrained randomness) + live deterministic
  deployment, per the earlier sandbox/live boundary discussion.
- Govern = `GovernanceEnvelope` checking live outcomes against the active
  Declaration on an ongoing basis, not just at deployment time. This is
  where B (the aggregation layer) becomes permanent infrastructure rather
  than a one-time report generator — same rollup logic, running forever.

---

## 8. What this spec does NOT decide (explicitly deferred)

- The actual schema/storage for manifest records (JSON files, DB, event log —
  unspecified).
- Who at "the business" has authority to sign a Declaration — an org question,
  not an engineering one.
- Whether a weak-but-technically-compliant Declaration should be blocked or
  merely made visible. Current lean: visible, not blocked — Iceberg's job is
  making a bad choice impossible to hide, not making the choice for the
  business. Worth revisiting once a real business is in the loop.
- The historical-data adapter needed to actually produce `reconstructed`
  entries from a prior system's logs. Does not exist yet.
