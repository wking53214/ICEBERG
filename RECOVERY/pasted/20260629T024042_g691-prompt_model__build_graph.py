# model/build_graph.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List

from domain.QueueState import QueueState


@dataclass
class Node:
    """
    A single node in the Iceberg routing graph.
    """
    node_id: str
    message: str
    actions: List[str]
    queue: str | None = None  # queue name or None


class Graph:
    """
    Routing graph for Iceberg 3.x.
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.neighbors: Dict[str, List[str]] = {}
        self.queues: Dict[str, QueueState] = {}

    # ---------------------------------------------------------
    # NODE MANAGEMENT
    # ---------------------------------------------------------
    def add_node(self, node_id: str, message: str, actions: List[str], queue: str | None = None):
        self.nodes[node_id] = Node(node_id=node_id, message=message, actions=actions, queue=queue)

    def add_edge(self, src: str, dst: str):
        if src not in self.neighbors:
            self.neighbors[src] = []
        self.neighbors[src].append(dst)

    # ---------------------------------------------------------
    # QUEUE MANAGEMENT
    # ---------------------------------------------------------
    def add_queue(self, name: str, staffing: float = 1.0, sl: float = 0.80, abandon: float = 0.02):
        self.queues[name] = QueueState(
            name=name,
            staffing=staffing,
            target_service_level=sl,
            abandonment_rate=abandon,
        )

    def init_queues(self) -> Dict[str, QueueState]:
        """
        Return a copy of queue objects for simulator use.
        """
        return {k: v for k, v in self.queues.items()}

    # ---------------------------------------------------------
    # SERIALIZATION
    # ---------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {
                nid: {
                    "message": n.message,
                    "actions": n.actions,
                    "queue": n.queue,
                }
                for nid, n in self.nodes.items()
            },
            "neighbors": self.neighbors,
            "queues": {
                qname: q.snapshot()
                for qname, q in self.queues.items()
            },
        }


# ---------------------------------------------------------
# GRAPH CONSTRUCTION
# ---------------------------------------------------------
def build_graph() -> Graph:
    g = Graph()

    # -----------------------------
    # QUEUES
    # -----------------------------
    g.add_queue("billing_q", staffing=3.0, sl=0.85, abandon=0.03)
    g.add_queue("tech_q", staffing=4.0, sl=0.80, abandon=0.04)
    g.add_queue("fraud_q", staffing=2.0, sl=0.90, abandon=0.02)
    g.add_queue("general_q", staffing=5.0, sl=0.75, abandon=0.05)

    # -----------------------------
    # NODES
    # -----------------------------
    g.add_node(
        "root",
        message="Welcome to Iceberg Support.",
        actions=["billing", "tech", "fraud", "general"],
        queue=None,
    )

    g.add_node(
        "billing",
        message="Billing department.",
        actions=["pay_bill", "refund", "agent"],
        queue="billing_q",
    )

    g.add_node(
        "tech",
        message="Technical support.",
        actions=["troubleshoot", "reset_modem", "agent"],
        queue="tech_q",
    )

    g.add_node(
        "fraud",
        message="Fraud prevention.",
        actions=["verify_identity", "report_fraud", "agent"],
        queue="fraud_q",
    )

    g.add_node(
        "general",
        message="General inquiries.",
        actions=["hours", "location", "agent"],
        queue="general_q",
    )

    # -----------------------------
    # EDGES
    # -----------------------------
    g.add_edge("root", "billing")
    g.add_edge("root", "tech")
    g.add_edge("root", "fraud")
    g.add_edge("root", "general")

    # Allow agent escalation from any department
    for dept in ["billing", "tech", "fraud", "general"]:
        g.add_node(
            f"{dept}_agent",
            message=f"{dept.capitalize()} agent queue.",
            actions=["end_call"],
            queue=f"{dept}_q",
        )
        g.add_edge(dept, f"{dept}_agent")

    return g