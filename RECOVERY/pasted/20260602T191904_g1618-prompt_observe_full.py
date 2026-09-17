# observe_full.py
"""
OBSERVE Reference Implementation (IRB pilot reference)
- Purpose: runnable reference for engineering review and pilot testing.
- Safety: PATENT_CANDIDATE internals remain intentionally stubbed/redacted.
- Not production-ready. Use as a blueprint and test harness only.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import uuid
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable

logger = logging.getLogger("observe")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)


# -------------------------
# Basic types and utilities
# -------------------------

def now_ts() -> float:
    return time.time()

def iso_ts() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

def site_scoped_hmac(site_salt: bytes, patient_id: str) -> str:
    """One-way pseudonymization using HMAC-SHA256. Salt must come from HSM in production."""
    return hmac.new(site_salt, patient_id.encode("utf-8"), hashlib.sha256).hexdigest()


# -------------------------
# Data models
# -------------------------

@dataclass
class VitalSnapshot:
    ts: float
    heart_rate: Optional[float] = None
    respiratory_rate: Optional[float] = None
    spo2: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    temp_c: Optional[float] = None
    source: str = "monitor"  # "monitor" or "ehr"
    artifact: bool = False

@dataclass
class PatientContext:
    patient_id: str  # raw id at ingest boundary; do not export
    age_months: Optional[int] = None
    weight_kg: Optional[float] = None
    unit: str = "general_ward"
    visit_stage: str = "first_visit"
    post_op_day: Optional[int] = None
    physiology: Optional[str] = None
    season: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TemporalFeatures:
    window_seconds: int
    hr_momentum: float = 0.0
    rr_momentum: float = 0.0
    spo2_momentum: float = 0.0
    hr_variance: float = 0.0
    spo2_variance: float = 0.0
    cross_corr_hr_rr: float = 0.0

@dataclass
class RiskSignal:
    score: float
    confidence: float
    components: Dict[str, float]
    matched_patterns: List[Dict[str, Any]]
    ts: float
    provenance_hash: str = ""

    def compute_provenance(self) -> None:
        payload = json.dumps({
            "score": self.score,
            "confidence": self.confidence,
            "components": self.components,
            "matched_patterns": sorted([p.get("id", "") for p in self.matched_patterns]),
            "ts": self.ts,
        }, sort_keys=True)
        self.provenance_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class StyleVariantRecord:
    variant_id: str
    clinician_id: str
    label: str
    tone: str
    age_min_months: int
    age_max_months: int
    visit_stage_tags: List[str]
    allowed_topics: List[str]
    voice_enabled: bool
    consent_signed: bool
    created_at: float
    approved: bool
    approver_id: Optional[str]
    template_text: str
    provenance_hash: str

    def matches(self, ctx: PatientContext) -> bool:
        if ctx.age_months is None:
            return False
        if not (self.age_min_months <= ctx.age_months <= self.age_max_months):
            return False
        if self.visit_stage_tags and ctx.visit_stage not in self.visit_stage_tags:
            return False
        return True


@dataclass
class MessagePayload:
    message_id: str
    patient_pseudonym: str
    variant_id: str
    text: str
    display_mode: str  # "voice" or "visual"
    linked_signal_hashes: List[str]
    approver_id: Optional[str]
    approved_at: Optional[float]
    suppressed: bool = False
    suppression_reasons: List[str] = field(default_factory=list)
    provenance_hash: str = ""

    def compute_provenance(self) -> None:
        payload = json.dumps({
            "message_id": self.message_id,
            "variant_id": self.variant_id,
            "text": self.text,
            "linked_signal_hashes": sorted(self.linked_signal_hashes),
            "approver_id": self.approver_id,
            "approved_at": self.approved_at,
        }, sort_keys=True)
        self.provenance_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()


# -------------------------
# Simple in-memory WORM audit log
# -------------------------

class AuditEntry:
    def __init__(self, actor: str, action: str, entity_type: str, entity_id: str, before: Optional[Dict]=None, after: Optional[Dict]=None):
        self.entry_id = str(uuid.uuid4())
        self.ts = iso_ts()
        self.actor = actor
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.before = before
        self.after = after
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps({
            "entry_id": self.entry_id,
            "ts": self.ts,
            "actor": self.actor,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "before": self.before,
            "after": self.after,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class AuditLog:
    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._chain_tip = hashlib.sha256(b"genesis").hexdigest()

    def append(self, entry: AuditEntry) -> None:
        # chain the entry
        chain_payload = f"{self._chain_tip}:{entry.hash}"
        self._chain_tip = hashlib.sha256(chain_payload.encode("utf-8")).hexdigest()
        self._entries.append(entry)

    def verify(self) -> bool:
        tip = hashlib.sha256(b"genesis").hexdigest()
        for e in self._entries:
            expected = hashlib.sha256(f"{tip}:{e.hash}".encode("utf-8")).hexdigest()
            tip = expected
        return tip == self._chain_tip

    def export(self) -> List[Dict[str, Any]]:
        return [vars(e) for e in self._entries]


# -------------------------
# Artifact suppressor (simple)
# -------------------------

class ArtifactSuppressor:
    """
    Basic artifact suppression: mark snapshots with impossible vitals as artifact.
    Production: replace with robust signal quality checks.
    """
    def suppress(self, snap: VitalSnapshot) -> VitalSnapshot:
        # simple plausibility checks
        if snap.heart_rate is not None and (snap.heart_rate < 20 or snap.heart_rate > 300):
            snap.artifact = True
        if snap.spo2 is not None and (snap.spo2 <= 0 or snap.spo2 > 100):
            snap.artifact = True
        return snap


# -------------------------
# Temporal engine (simple implementation)
# -------------------------

class TemporalEngine:
    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self._buffers: Dict[str, List[VitalSnapshot]] = {}

    def ingest(self, patient_id: str, snap: VitalSnapshot) -> None:
        buf = self._buffers.setdefault(patient_id, [])
        buf.append(snap)
        cutoff = time.time() - self.window_seconds
        # keep only recent non-artifact snapshots
        self._buffers[patient_id] = [s for s in buf if s.ts >= cutoff and not s.artifact]

    def extract(self, patient_id: str) -> Optional[TemporalFeatures]:
        buf = self._buffers.get(patient_id, [])
        if len(buf) < 3:
            return None
        # compute simple momentum and variance
        hr_vals = [s.heart_rate for s in buf if s.heart_rate is not None]
        rr_vals = [s.respiratory_rate for s in buf if s.respiratory_rate is not None]
        spo2_vals = [s.spo2 for s in buf if s.spo2 is not None]
        def momentum(vals):
            if len(vals) < 2:
                return 0.0
            return (vals[-1] - vals[0]) / max(1.0, len(vals))
        def variance(vals):
            if len(vals) < 2:
                return 0.0
            mean = sum(vals)/len(vals)
            return sum((v-mean)**2 for v in vals)/len(vals)
        tf = TemporalFeatures(window_seconds=self.window_seconds)
        tf.hr_momentum = momentum(hr_vals) if hr_vals else 0.0
        tf.rr_momentum = momentum(rr_vals) if rr_vals else 0.0
        tf.spo2_momentum = momentum(spo2_vals) if spo2_vals else 0.0
        tf.hr_variance = variance(hr_vals) if hr_vals else 0.0
        tf.spo2_variance = variance(spo2_vals) if spo2_vals else 0.0
        # cross-correlation simple proxy
        if hr_vals and rr_vals and len(hr_vals)==len(rr_vals):
            n = len(hr_vals)
            mean_hr = sum(hr_vals)/n
            mean_rr = sum(rr_vals)/n
            num = sum((hr_vals[i]-mean_hr)*(rr_vals[i]-mean_rr) for i in range(n))
            den = max(1e-6, (sum((x-mean_hr)**2 for x in hr_vals)*sum((x-mean_rr)**2 for x in rr_vals))**0.5)
            tf.cross_corr_hr_rr = num/den if den>0 else 0.0
        return tf

    def flush(self, patient_id: str) -> None:
        self._buffers.pop(patient_id, None)


# -------------------------
# Heuristic rule set (conservative)
# -------------------------

class HeuristicRuleSet:
    """
    Conservative age-adjusted thresholds. Returns a RiskSignal based on heuristics only.
    """
    def __init__(self):
        pass

    def evaluate(self, snap: VitalSnapshot, ctx: PatientContext) -> RiskSignal:
        score = 0.0
        components = {}
        # example rules (very conservative)
        if snap.spo2 is not None:
            if snap.spo2 < 92:
                score += 0.25
                components["low_spo2"] = 0.25
        if snap.heart_rate is not None and ctx.age_months is not None:
            # simple age-based tachycardia thresholds (illustrative)
            if ctx.age_months < 12 and snap.heart_rate > 160:
                score += 0.2
                components["tachycardia_infant"] = 0.2
            elif ctx.age_months >= 12 and snap.heart_rate > 140:
                score += 0.1
                components["tachycardia_child"] = 0.1
        # clamp
        score = min(1.0, score)
        rs = RiskSignal(score=score, confidence=0.6, components=components, matched_patterns=[], ts=now_ts())
        rs.compute_provenance()
        return rs


# -------------------------
# Temporal vaccine (transparent)
# -------------------------

class TemporalVaccine:
    def __init__(self, vid: str, name: str, conditions: Dict[str, Any], boost: float, context_tags: List[str]):
        self.metadata = VaccineMetadataStub(vid, name, context_tags)
        self.conditions = conditions
        self.boost = boost

    def match(self, features: TemporalFeatures, context: PatientContext) -> Tuple[bool, float]:
        # simple transparent matching: check momentum thresholds
        ok = True
        if "hr_momentum_min" in self.conditions and features.hr_momentum < self.conditions["hr_momentum_min"]:
            ok = False
        if "spo2_momentum_max" in self.conditions and features.spo2_momentum > self.conditions["spo2_momentum_max"]:
            ok = False
        return (ok, self.boost if ok else 0.0)


@dataclass
class VaccineMetadataStub:
    vaccine_id: str
    name: str
    context_tags: List[str]
    version: int = 1
    created_at: float = field(default_factory=now_ts)
    approved_by: Optional[str] = None
    approval_status: str = "approved"
    decay_half_life_days: float = 90.0
    drift_frozen: bool = False
    last_triggered: Optional[float] = None


# -------------------------
# Behavioral vaccine (PATENT_CANDIDATE stub)
# -------------------------

class BehavioralVaccine:
    """
    PATENT_CANDIDATE: interface only. Implementations must be conservative and
    treated as curated rules derived from small-N cases. No automatic online
    parameter updates in pilot.
    """
    def __init__(self, metadata: VaccineMetadataStub):
        self.metadata = metadata

    def match(self, features: TemporalFeatures, context: PatientContext, history: List[VitalSnapshot]) -> Tuple[bool, float]:
        # REDACTED: proprietary matching logic
        return (False, 0.0)

    def decay_weight(self) -> float:
        # simple time-based decay stub
        age_days = (now_ts() - self.metadata.created_at) / 86400.0
        half = self.metadata.decay_half_life_days
        return 0.5 ** (age_days / half)


# -------------------------
# Hybrid risk engine
# -------------------------

class HybridRiskEngine:
    def __init__(self, heuristics: HeuristicRuleSet, temporal_vaccines: List[TemporalVaccine], behavioral_vaccines: List[BehavioralVaccine]):
        self.heuristics = heuristics
        self.temporal_vaccines = temporal_vaccines
        self.behavioral_vaccines = behavioral_vaccines

    def evaluate(self, snap: VitalSnapshot, features: TemporalFeatures, ctx: PatientContext, history: List[VitalSnapshot]) -> RiskSignal:
        # baseline from heuristics
        base = self.heuristics.evaluate(snap, ctx)
        score = base.score
        components = dict(base.components)
        matched = []

        # temporal vaccines additive
        for tv in self.temporal_vaccines:
            matched_flag, boost = tv.match(features, ctx)
            if matched_flag:
                score = min(1.0, score + boost)
                components[f"temporal:{tv.metadata.vaccine_id}"] = boost
                matched.append({"id": tv.metadata.vaccine_id, "type": "temporal", "boost": boost})

        # behavioral vaccines additive but only if active and approved
        for bv in self.behavioral_vaccines:
            if bv.metadata.drift_frozen or bv.metadata.approval_status != "approved":
                continue
            matched_flag, boost = bv.match(features, ctx, history)
            if matched_flag:
                weight = bv.decay_weight()
                adj = boost * weight
                score = min(1.0, score + adj)
                components[f"behavioral:{bv.metadata.vaccine_id}"] = adj
                matched.append({"id": bv.metadata.vaccine_id, "type": "behavioral", "boost": adj})

        rs = RiskSignal(score=score, confidence=0.6, components=components, matched_patterns=matched, ts=now_ts())
        rs.compute_provenance()
        return rs


# -------------------------
# Drift detector (simple)
# -------------------------

class DriftDetector:
    """
    Simple distribution-monitoring drift detector using rolling mean of scores.
    Production: replace with robust CUSUM/ADWIN and label-aware detectors.
    """
    def __init__(self, window: int = 200, threshold: float = 0.2):
        self.window = window
        self.threshold = threshold
        self._scores: List[float] = []

    def observe(self, signal: RiskSignal, ground_truth: Optional[bool] = None) -> None:
        self._scores.append(signal.score)
        if len(self._scores) > self.window:
            self._scores.pop(0)

    def drift_detected(self) -> bool:
        if len(self._scores) < max(10, self.window//10):
            return False
        mean = sum(self._scores)/len(self._scores)
        # naive: drift if mean deviates from 0.2 by threshold
        return abs(mean - 0.2) > self.threshold

    def reset(self) -> None:
        self._scores = []


# -------------------------
# Clinician Style Archive (CSA)
# -------------------------

class StyleArchive:
    def __init__(self):
        self._variants: Dict[str, StyleVariantRecord] = {}

    def add_variant(self, v: StyleVariantRecord) -> None:
        self._variants[v.variant_id] = v

    def get_candidates(self, ctx: PatientContext, preferred_tone: Optional[str] = None) -> List[StyleVariantRecord]:
        candidates = [v for v in self._variants.values() if v.approved and v.matches(ctx)]
        # deterministic ordering: narrowest age span first, then earliest created
        candidates.sort(key=lambda r: ((r.age_max_months - r.age_min_months), r.created_at))
        if preferred_tone:
            # prefer exact tone matches deterministically
            pref = [c for c in candidates if c.tone == preferred_tone]
            if pref:
                return pref
        return candidates


# -------------------------
# Safety gate and selection engine
# -------------------------

class SafetyGate:
    FORBIDDEN_PHRASES = frozenset({
        "diagnos", "you have", "cancer", "heart failure", "will need surgery",
        "is dying", "critical", "emergency",
    })

    def __init__(self, audit: AuditLog, child_score_floor: float = 0.5, general_floor: float = 0.3):
        self.audit = audit
        self.child_score_floor = child_score_floor
        self.general_floor = general_floor

    def check(self, payload: MessagePayload, signal: RiskSignal, ctx: PatientContext, parent_voice_enabled: bool, child_mode_enabled: bool) -> MessagePayload:
        reasons = []
        # parent control
        if payload.display_mode == "voice" and not parent_voice_enabled:
            reasons.append("parent_voice_disabled")
        # child-facing check
        if payload.display_mode == "voice" and child_mode_enabled:
            if signal.score < self.child_score_floor:
                reasons.append("score_below_child_floor")
        else:
            if signal.score < self.general_floor:
                reasons.append("score_below_general_floor")
        # content scan
        text = payload.text.lower()
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase in text:
                reasons.append(f"forbidden_phrase:{phrase}")
                break
        payload.suppressed = len(reasons) > 0
        payload.suppression_reasons = reasons
        self.audit.append(AuditEntry(actor="safety_gate", action="check", entity_type="message", entity_id=payload.message_id, after={"suppressed": payload.suppressed, "reasons": reasons}))
        return payload


class SelectionEngine:
    """
    Deterministic selection: given archive, context, controls, and signal, return a single variant or None.
    """
    def __init__(self):
        pass

    def select(self, archive: StyleArchive, ctx: PatientContext, controls: Dict[str, Any], signal: RiskSignal) -> Optional[StyleVariantRecord]:
        # deterministic pipeline:
        # 1) get candidates matching age and visit stage
        candidates = archive.get_candidates(ctx, preferred_tone=controls.get("preferred_tone"))
        if not candidates:
            return None
        # 2) enforce voice capability
        if not controls.get("voice_enabled", False):
            # prefer non-voice variants if available
            non_voice = [c for c in candidates if not c.voice_enabled]
            if non_voice:
                candidates = non_voice
        # 3) deterministic tie-breaker already applied in archive.get_candidates
        return candidates[0]


# -------------------------
# Hyperscale encoder (simple)
# -------------------------

class HyperscaleEncoder:
    """
    Encode de-identified state vector for on-prem LLM ingestion.
    Salt must be provided from secure store (HSM) in production.
    """
    def __init__(self, encoder_version: str, site_salt: bytes):
        self.encoder_version = encoder_version
        self.site_salt = site_salt

    def encode(self, patient_id: str, ctx: PatientContext, features: TemporalFeatures, signal: RiskSignal, active_vaccine_ids: List[str]) -> Dict[str, Any]:
        pseud = site_scoped_hmac(self.site_salt, patient_id)
        sv = {
            "schema_version": "observe_state_v1",
            "encoder_version": self.encoder_version,
            "patient_pseudonym": pseud,
            "context": {
                "age_bucket": self._age_bucket(ctx.age_months),
                "unit": ctx.unit,
                "visit_stage": ctx.visit_stage,
                "post_op_day": ctx.post_op_day,
                "physiology": ctx.physiology,
                "season": ctx.season,
            },
            "temporal_features": {
                "hr_momentum": features.hr_momentum,
                "rr_momentum": features.rr_momentum,
                "spo2_momentum": features.spo2_momentum,
            },
            "risk_signal": {
                "score": signal.score,
                "confidence": signal.confidence,
                "provenance_hash": signal.provenance_hash,
            },
            "active_vaccine_ids": active_vaccine_ids,
            "export_timestamp": iso_ts(),
        }
        # provenance for state vector
        sv_payload = json.dumps(sv, sort_keys=True)
        sv["provenance_hash"] = hashlib.sha256(sv_payload.encode("utf-8")).hexdigest()
        return sv

    def _age_bucket(self, age_months: Optional[int]) -> str:
        if age_months is None:
            return "unknown"
        if age_months < 12:
            return "0-11m"
        if age_months < 60:
            return "1-4y"
        if age_months < 144:
            return "5-11y"
        return "12+"

# -------------------------
# Pipeline orchestrator
# -------------------------

class OBSERVE:
    def __init__(
        self,
        site_salt: bytes,
        monitor_streamer: Callable[[str], VitalSnapshot],
        ehr_fetcher: Callable[[str], PatientContext],
    ):
        # core components
        self.audit = AuditLog()
        self.suppressor = ArtifactSuppressor()
        self.temporal = TemporalEngine(window_seconds=300)
        self.heuristics = HeuristicRuleSet()
        # example temporal vaccines
        self.temporal_vaccines = [
            TemporalVaccine("tv_resp_failure", "resp_failure_trajectory", {"spo2_momentum_max": -0.02, "hr_momentum_min": 5.0}, boost=0.12, context_tags=["post_op"]),
        ]
        self.behavioral_vaccines: List[BehavioralVaccine] = []  # curated, added via governance
        self.risk_engine = HybridRiskEngine(self.heuristics, self.temporal_vaccines, self.behavioral_vaccines)
        self.drift = DriftDetector(window=200, threshold=0.25)
        self.style_archive = StyleArchive()
        self.selection = SelectionEngine()
        self.safety = SafetyGate(self.audit)
        self.encoder = HyperscaleEncoder("v1", site_salt)
        self.monitor_streamer = monitor_streamer
        self.ehr_fetcher = ehr_fetcher
        # parent controls store (de-id patient pseudonym -> controls)
        self.parent_controls: Dict[str, Dict[str, Any]] = {}
        # approval gate (simple role check)
        self.approval_roles = {"attending", "cmo", "patient_safety_officer"}

    def register_behavioral_vaccine(self, bv: BehavioralVaccine) -> None:
        self.behavioral_vaccines.append(bv)
        self.audit.append(AuditEntry(actor="system", action="register_behavioral_vaccine", entity_type="vaccine", entity_id=bv.metadata.vaccine_id, after={"meta": vars(bv.metadata)}))

    def add_style_variant(self, variant: StyleVariantRecord) -> None:
        self.style_archive.add_variant(variant)
        self.audit.append(AuditEntry(actor=variant.clinician_id, action="add_style_variant", entity_type="style_variant", entity_id=variant.variant_id, after={"label": variant.label}))

    def set_parent_controls(self, patient_pseudonym: str, controls: Dict[str, Any]) -> None:
        self.parent_controls[patient_pseudonym] = controls

    def process_tick(self, patient_id: str) -> Dict[str, Any]:
        """
        Single tick: ingest -> suppress -> temporal -> risk -> encode -> CSA selection -> safety gate -> audit
        Returns a dict with state_vector, risk_signal, message_payload (if any), and status.
        """
        try:
            raw_snap = self.monitor_streamer(patient_id)
            clean = self.suppressor.suppress(raw_snap)
            ctx = self.ehr_fetcher(patient_id)

            # ingest temporal
            self.temporal.ingest(patient_id, clean)
            features = self.temporal.extract(patient_id)
            if features is None:
                return {"status": "insufficient_data"}

            # history read (simple)
            history = self.temporal._buffers.get(patient_id, [])  # for vaccine matching

            # risk evaluation
            risk = self.risk_engine.evaluate(clean, features, ctx, history)
            self.drift.observe(risk)
            # quarantine on drift
            if self.drift.drift_detected():
                for bv in self.behavioral_vaccines:
                    if not bv.metadata.drift_frozen:
                        bv.metadata.drift_frozen = True
                        self.audit.append(AuditEntry(actor="system", action="quarantine_vaccine", entity_type="vaccine", entity_id=bv.metadata.vaccine_id, after={"reason": "drift_detected"}))

            # encode state vector
            active_vaccine_ids = [v.metadata.vaccine_id for v in self.behavioral_vaccines if v.metadata.approval_status == "approved" and not v.metadata.drift_frozen]
            state_vector = self.encoder.encode(patient_id, ctx, features, risk, active_vaccine_ids)

            # CSA selection
            patient_pseud = site_scoped_hmac(self.encoder.site_salt, patient_id)
            controls = self.parent_controls.get(patient_pseud, {"voice_enabled": False, "child_mode": False, "preferred_tone": None})
            record = self.selection.select(self.style_archive, ctx, controls, risk)
            payload = None
            if record:
                display_mode = "voice" if controls.get("voice_enabled", False) and record.voice_enabled else "visual"
                payload = MessagePayload(
                    message_id=str(uuid.uuid4()),
                    patient_pseudonym=patient_pseud,
                    variant_id=record.variant_id,
                    text=record.template_text,
                    display_mode=display_mode,
                    linked_signal_hashes=[risk.provenance_hash],
                    approver_id=record.approver_id,
                    approved_at=record.created_at if record.approved else None,
                )
                payload = self.safety.check(payload, risk, ctx, parent_voice_enabled=controls.get("voice_enabled", False), child_mode_enabled=controls.get("child_mode", False))
                payload.compute_provenance()
                self.audit.append(AuditEntry(actor="system", action="deliver_message", entity_type="message", entity_id=payload.message_id, after={"suppressed": payload.suppressed}))

            # final audit for tick
            self.audit.append(AuditEntry(actor="system", action="process_tick", entity_type="patient", entity_id=patient_pseud, after={"state_vector_provenance": state_vector.get("provenance_hash"), "risk_provenance": risk.provenance_hash}))

            return {
                "status": "ok",
                "state_vector": state_vector,
                "risk_signal": {"score": risk.score, "confidence": risk.confidence, "provenance_hash": risk.provenance_hash},
                "message_payload": vars(payload) if payload else None,
            }

        except Exception as e:
            logger.exception("process_tick error")
            self.audit.append(AuditEntry(actor="system", action="process_tick_error", entity_type="patient", entity_id=patient_id, after={"error": str(e)}))
            return {"status": "error", "error": str(e)}


# -------------------------
# Minimal test harness
# -------------------------

def _fake_monitor_stream(patient_id: str) -> VitalSnapshot:
    # simple synthetic vitals for testing
    t = time.time()
    return VitalSnapshot(ts=t, heart_rate=150.0, respiratory_rate=55.0, spo2=88.0, systolic_bp=70.0, diastolic_bp=40.0, temp_c=36.5, source="monitor")

def _fake_ehr_fetch(patient_id: str) -> PatientContext:
    return PatientContext(patient_id=patient_id, age_months=72, weight_kg=12.0, unit="cardiac_stepdown", visit_stage="day_1", post_op_day=1, physiology="single_ventricle", season="winter")

def _demo():
    site_salt = b"demo_site_salt_please_replace_with_hsm"
    obs = OBSERVE(site_salt, _fake_monitor_stream, _fake_ehr_fetch)

    # add a sample style variant (approved)
    variant = StyleVariantRecord(
        variant_id=str(uuid.uuid4()),
        clinician_id="clinician_1",
        label="funny_5to10",
        tone="playful",
        age_min_months=60,
        age_max_months=120,
        visit_stage_tags=["day_1", "first_visit"],
        allowed_topics=["reassurance"],
        voice_enabled=True,
        consent_signed=True,
        created_at=now_ts(),
        approved=True,
        approver_id="attending_1",
        template_text="Your body is working hard to breathe. Let's try slow breaths together!",
        provenance_hash="",
    )
    obs.add_style_variant(variant)

    # set parent controls (enable voice)
    patient_pseud = site_scoped_hmac(site_salt, "patient-123")
    obs.set_parent_controls(patient_pseud, {"voice_enabled": True, "child_mode": False, "preferred_tone": "playful"})

    # run a few ticks
    for i in range(3):
        out = obs.process_tick("patient-123")
        print(json.dumps(out, indent=2))
        time.sleep(0.5)

    # verify audit chain
    print("Audit chain valid:", obs.audit.verify())
    print("Audit entries:", len(obs.audit._entries))

if __name__ == "__main__":
    _demo()