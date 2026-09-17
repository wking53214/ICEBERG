# graph/GraphPresets.py
from __future__ import annotations
from graph.GraphBuilder import GraphBuilder


class GraphPresets:
    """
    Prebuilt graph topologies for Iceberg 3.x.
    Each preset returns a fully constructed GraphModel.
    """

    # ---------------------------------------------------------
    # BASIC SUPPORT FLOW
    # ---------------------------------------------------------
    @staticmethod
    def basic_support_flow():
        gb = GraphBuilder()

        gb.queue("billing_q", priority=1)
        gb.queue("tech_q", priority=1)
        gb.queue("fraud_q", priority=2)
        gb.queue("general_q", priority=3)

        gb.node("start")
        gb.node("billing", queue="billing_q")
        gb.node("tech", queue="tech_q")
        gb.node("fraud", queue="fraud_q")
        gb.node("general", queue="general_q")
        gb.node("end")

        gb.star("start", "billing", "tech", "fraud", "general")
        gb.linear("billing", "end")
        gb.linear("tech", "end")
        gb.linear("fraud", "end")
        gb.linear("general", "end")

        return gb.build()

    # ---------------------------------------------------------
    # IVR MENU FLOW
    # ---------------------------------------------------------
    @staticmethod
    def ivr_menu_flow():
        gb = GraphBuilder()

        gb.queue("ivr_q")
        gb.queue("agent_q")

        gb.node("welcome", queue="ivr_q")
        gb.node("menu", queue="ivr_q")
        gb.node("billing", queue="agent_q")
        gb.node("tech", queue="agent_q")
        gb.node("fraud", queue="agent_q")
        gb.node("goodbye")

        gb.linear("welcome", "menu")
        gb.star("menu", "billing", "tech", "fraud")
        gb.linear("billing", "goodbye")
        gb.linear("tech", "goodbye")
        gb.linear("fraud", "goodbye")

        return gb.build()

    # ---------------------------------------------------------
    # MULTI-STAGE ESCALATION FLOW
    # ---------------------------------------------------------
    @staticmethod
    def escalation_flow():
        gb = GraphBuilder()

        gb.queue("tier1_q", priority=1)
        gb.queue("tier2_q", priority=2)
        gb.queue("tier3_q", priority=3)

        gb.node("entry")
        gb.node("tier1", queue="tier1_q")
        gb.node("tier2", queue="tier2_q")
        gb.node("tier3", queue="tier3_q")
        gb.node("resolution")

        gb.linear("entry", "tier1", "tier2", "tier3", "resolution")

        return gb.build()

    # ---------------------------------------------------------
    # RING TOPOLOGY (LOAD BALANCING)
    # ---------------------------------------------------------
    @staticmethod
    def ring_topology():
        gb = GraphBuilder()

        gb.queue("ring_q")

        gb.node("n1", queue="ring_q")
        gb.node("n2", queue="ring_q")
        gb.node("n3", queue="ring_q")
        gb.node("n4", queue="ring_q")

        gb.ring("n1", "n2", "n3", "n4")

        return gb.build()

    # ---------------------------------------------------------
    # HYBRID STAR + LINEAR FLOW
    # ---------------------------------------------------------
    @staticmethod
    def hybrid_flow():
        gb = GraphBuilder()

        gb.queue("primary_q")
        gb.queue("secondary_q")

        gb.node("root", queue="primary_q")
        gb.node("a", queue="secondary_q")
        gb.node("b", queue="secondary_q")
        gb.node("c", queue="secondary_q")
        gb.node("end")

        gb.star("root", "a", "b", "c")
        gb.linear("a", "end")
        gb.linear("b", "end")
        gb.linear("c", "end")

        return gb.build()