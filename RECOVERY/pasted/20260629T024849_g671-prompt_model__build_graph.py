# model/build_graph.py
from __future__ import annotations
from typing import Dict, Any


class GraphNode:
    """
    A single IVR node.
    """
    def __init__(self, node_id: str, prompt: str, queue: str | None = None):
        self.node_id = node_id
        self.prompt = prompt
        self.queue = queue  # optional queue assignment


class QueueState:
    """
    Queue metrics used by staffing RL + simulator.
    """
    def __init__(self, name: str):
        self.name = name
        self.active_calls = 0
        self.staffing = 5.0
        self.target_service_level = 0.80
        self.abandonment_rate = 0.05

    def apply_delta(self, delta: float):
        self.staffing = max(0.0, self.staffing + delta)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "active_calls": self.active_calls,
            "staffing": self.staffing,
            "target_service_level": self.target_service_level,
            "abandonment_rate": self.abandonment_rate,
        }


class RoutingGraph:
    """
    Full routing graph for Iceberg 3.x.
    Contains:
      - nodes
      - queues
      - neighbors
    """

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.queues: Dict[str, QueueState] = {}
        self.neighbors: Dict[str, list[str]] = {}

    # ---------------------------------------------------------
    # ADDERS
    # ---------------------------------------------------------
    def add_node(self, node_id: str, prompt: str, queue: str | None = None):
        self.nodes[node_id] = GraphNode(node_id, prompt, queue)

    def add_queue(self, name: str):
        self.queues[name] = QueueState(name)

    def add_edges(self, node_id: str, next_nodes: list[str]):
        self.neighbors[node_id] = next_nodes

    # ---------------------------------------------------------
    # EXPORT
    # ---------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {
                nid: {
                    "prompt": n.prompt,
                    "queue": n.queue,
                }
                for nid, n in self.nodes.items()
            },
            "queues": {
                qname: q.snapshot()
                for qname, q in self.queues.items()
            },
            "neighbors": self.neighbors,
        }


# ---------------------------------------------------------
# GRAPH CONSTRUCTION
# ---------------------------------------------------------
def build_graph() -> RoutingGraph:
    g = RoutingGraph()

    # Queues
    g.add_queue("billing")
    g.add_queue("tech")
    g.add_queue("fraud")
    g.add_queue("general")

    # Nodes
    g.add_node("root", "Welcome to Iceberg IVR.")
    g.add_node("billing_menu", "Billing options.", queue="billing")
    g.add_node("tech_menu", "Technical support.", queue="tech")
    g.add_node("fraud_menu", "Fraud & security.", queue="fraud")
    g.add_node("general_menu", "General inquiries.", queue="general")

    # Edges
    g.add_edges("root", ["billing_menu", "tech_menu", "fraud_menu", "general_menu"])
    g.add_edges("billing_menu", ["root"])
    g.add_edges("tech_menu", ["root"])
    g.add_edges("fraud_menu", ["root"])
    g.add_edges("general_menu", ["root"])

    return g