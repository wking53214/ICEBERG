# graph/GraphBuilder.py
from __future__ import annotations
from typing import Dict, Any, List

from graph.GraphModel import GraphModel


class GraphBuilder:
    """
    Deterministic DSL for constructing Iceberg 3.x graphs.

    Provides:
      - declarative node creation
      - declarative queue creation
      - declarative edge creation
      - routing helpers
      - structural-hash-safe graph assembly
      - replay-safe export
      - governance-compatible structure
    """

    def __init__(self):
        self.graph = GraphModel()

    # ---------------------------------------------------------
    # QUEUES
    # ---------------------------------------------------------
    def queue(self, name: str, **meta) -> "GraphBuilder":
        """
        Define a queue.
        """
        self.graph.add_queue(name, meta)
        return self

    # ---------------------------------------------------------
    # NODES
    # ---------------------------------------------------------
    def node(self, node_id: str, queue: str | None = None, **meta) -> "GraphBuilder":
        """
        Define a node.
        """
        self.graph.add_node(node_id, queue, meta)
        return self

    # ---------------------------------------------------------
    # EDGES
    # ---------------------------------------------------------
    def edge(self, src: str, dst: str, **meta) -> "GraphBuilder":
        """
        Define a directed edge.
        """
        self.graph.add_edge(src, dst, meta)
        return self

    # ---------------------------------------------------------
    # ROUTING HELPERS
    # ---------------------------------------------------------
    def linear(self, *nodes: str) -> "GraphBuilder":
        """
        Create a linear chain:
        A → B → C → D
        """
        for i in range(len(nodes) - 1):
            self.graph.add_edge(nodes[i], nodes[i + 1])
        return self

    def star(self, center: str, *targets: str) -> "GraphBuilder":
        """
        Create a star topology:
        center → t1
        center → t2
        center → t3
        """
        for t in targets:
            self.graph.add_edge(center, t)
        return self

    def ring(self, *nodes: str) -> "GraphBuilder":
        """
        Create a ring topology:
        A → B → C → A
        """
        for i in range(len(nodes)):
            self.graph.add_edge(nodes[i], nodes[(i + 1) % len(nodes)])
        return self

    # ---------------------------------------------------------
    # EXPORT
    # ---------------------------------------------------------
    def build(self) -> GraphModel:
        """
        Return the fully constructed graph.
        """
        return self.graph

    def to_dict(self) -> Dict[str, Any]:
        return self.graph.to_dict()

    def structural_hash(self) -> str:
        return self.graph.structural_hash()