# graph/GraphAnalytics.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple

from graph.GraphModel import GraphModel


class GraphAnalytics:
    """
    Analytical engine for Iceberg 3.x graphs.

    Provides:
      - node/edge/queue metrics
      - structural hash comparison
      - drift detection
      - neighbor analysis
      - queue pressure metrics
      - governance-ready insights
    """

    def __init__(self, graph: GraphModel):
        self.graph = graph

    # ---------------------------------------------------------
    # BASIC METRICS
    # ---------------------------------------------------------
    def node_count(self) -> int:
        return len(self.graph.nodes)

    def edge_count(self) -> int:
        return len(self.graph.edges)

    def queue_count(self) -> int:
        return len(self.graph.queues)

    # ---------------------------------------------------------
    # NEIGHBOR METRICS
    # ---------------------------------------------------------
    def neighbor_map(self) -> Dict[str, List[str]]:
        return self.graph.neighbors

    def degree(self, node_id: str) -> int:
        return len(self.graph.neighbors.get(node_id, []))

    def degree_distribution(self) -> Dict[str, int]:
        return {n: len(v) for n, v in self.graph.neighbors.items()}

    # ---------------------------------------------------------
    # QUEUE PRESSURE
    # ---------------------------------------------------------
    def queue_pressure(self) -> Dict[str, float]:
        """
        Pressure = load / (1 + number_of_nodes_bound_to_queue)
        """
        pressure = {}
        for qname, meta in self.graph.queues.items():
            load = meta.get("load", 0)
            bound_nodes = sum(1 for n in self.graph.nodes.values() if n.queue == qname)
            pressure[qname] = load / (1 + bound_nodes)
        return pressure

    # ---------------------------------------------------------
    # STRUCTURAL HASH
    # ---------------------------------------------------------
    def structural_hash(self) -> str:
        return self.graph.structural_hash()

    # ---------------------------------------------------------
    # DRIFT DETECTION
    # ---------------------------------------------------------
    def detect_drift(self, baseline_hash: str) -> Dict[str, Any]:
        current_hash = self.graph.structural_hash()
        drift = baseline_hash != current_hash
        return {
            "baseline_hash": baseline_hash,
            "current_hash": current_hash,
            "drift": drift,
        }

    # ---------------------------------------------------------
    # NODE METADATA SUMMARY
    # ---------------------------------------------------------
    def node_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Summarize node metadata for governance + dashboard.
        """
        summary = {}
        for nid, node in self.graph.nodes.items():
            summary[nid] = {
                "queue": node.queue,
                "meta": node.meta,
                "degree": len(self.graph.neighbors.get(nid, [])),
            }
        return summary

    # ---------------------------------------------------------
    # FULL ANALYTICS REPORT
    # ---------------------------------------------------------
    def report(self) -> Dict[str, Any]:
        return {
            "nodes": self.node_count(),
            "edges": self.edge_count(),
            "queues": self.queue_count(),
            "degree_distribution": self.degree_distribution(),
            "queue_pressure": self.queue_pressure(),
            "structural_hash": self.structural_hash(),
            "node_summary": self.node_summary(),
        }