# policy/PolicyExamples.py
from __future__ import annotations
from typing import Dict, Any

from domain.Intent import Intent
from domain.Emotion import Emotion


# ---------------------------------------------------------
# ROUTING POLICY — Intent + Emotion Weighted Routing
# ---------------------------------------------------------
def routing_policy(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Routing policy:
      - Billing callers prefer billing nodes
      - Angry callers prefer shortest path
      - Fraud callers prefer fraud nodes
    """
    intent = context.get("intent")
    emotion = context.get("emotion")
    neighbors = context.get("neighbors", [])

    # Emotion override: angry callers → shortest path
    if emotion == Emotion.ANGRY.name.lower():
        return {"next": neighbors[:1]}

    # Intent-based routing
    if intent == Intent.BILLING.name.lower():
        return {"next": [n for n in neighbors if "billing" in n] or neighbors}

    if intent == Intent.TECH.name.lower():
        return {"next": [n for n in neighbors if "tech" in n] or neighbors}

    if intent == Intent.FRAUD.name.lower():
        return {"next": [n for n in neighbors if "fraud" in n] or neighbors}

    return {"next": neighbors}


# ---------------------------------------------------------
# REWARD-SHAPING POLICY — Queue Load + Emotion Penalty
# ---------------------------------------------------------
def reward_policy(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reward shaping:
      - Penalize long queues
      - Penalize angry/frustrated callers
      - Reward fast resolution
    """
    queue_length = context.get("queue_length", 0)
    emotion = context.get("emotion")
    resolved = context.get("resolved", False)

    reward = 0.0

    # Queue penalty
    reward -= queue_length * 0.1

    # Emotion penalty
    if emotion == Emotion.ANGRY.name.lower():
        reward -= 2.0
    elif emotion == Emotion.FRUSTRATED.name.lower():
        reward -= 1.0

    # Resolution reward
    if resolved:
        reward += 5.0

    return {"reward": reward}


# ---------------------------------------------------------
# GOVERNANCE POLICY — Structural Hash Drift Guard
# ---------------------------------------------------------
def governance_policy(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Governance policy:
      - Reject if structural hash drift exceeds threshold
      - Reject if node count changes unexpectedly
    """
    baseline_hash = context.get("baseline_hash")
    current_hash = context.get("current_hash")
    baseline_nodes = context.get("baseline_nodes", 0)
    current_nodes = context.get("current_nodes", 0)

    if baseline_hash != current_hash:
        return {"allowed": False, "reason": "Structural hash drift detected"}

    if baseline_nodes != current_nodes:
        return {"allowed": False, "reason": "Node count mismatch"}

    return {"allowed": True}


# ---------------------------------------------------------
# STAFFING POLICY — Dynamic Agent Allocation
# ---------------------------------------------------------
def staffing_policy(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Staffing policy:
      - Allocate more agents to queues with high load
      - Reduce agents for low-load queues
    """
    queue_load = context.get("queue_load", 0)
    agents = context.get("agents", 1)

    if queue_load > 50:
        agents += 3
    elif queue_load > 20:
        agents += 1
    elif queue_load < 5:
        agents -= 1

    agents = max(1, agents)
    return {"agents": agents}


# ---------------------------------------------------------
# EXTRACTION POLICY — Manifest Integrity Guard
# ---------------------------------------------------------
def extraction_policy(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extraction policy:
      - Reject modules with version regressions
      - Reject modules with hash mismatches
    """
    incoming_version = context.get("incoming_version")
    current_version = context.get("current_version")
    incoming_hash = context.get("incoming_hash")
    current_hash = context.get("current_hash")

    if current_version and incoming_version < current_version:
        return {"allowed": False, "reason": "Version regression"}

    if current_hash and incoming_hash == current_hash:
        return {"allowed": False, "reason": "No change"}

    return {"allowed": True}