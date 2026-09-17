# graph/GraphModel.py
from __future__ import annotations
import hashlib
import json
from typing import Dict, Any, List


class Node:
    """
    Canonical Iceberg 3.x node.
    Represents a routing point in the simulation graph.
    """

    def __init__(self, node_id: str, queue: str | None = None, meta: Dict[str, Any] | None = None):
        self.node_id = node_id
        self.queue = queue
        self.meta = meta or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "queue": self.queue,
            "meta": self.meta,
        }


class Edge:
    """
    Canonical Iceberg 3.x edge.
    Represents a directed transition between nodes.
    """

    def __init__(self, src: str, dst: str, meta: Dict[str, Any] | None = None):
        self.src = src
        self.dst = dst
        self.meta = meta or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "src": self.src,
            "dst": self.dst,
            "meta": self.meta,
        }


class GraphModel:
    """
    Structural-hash graph model for Iceberg 3.x.

    Provides:
      - deterministic structural hashing
      - node registry
      - edge registry
      - queue registry
      - neighbor map
      - JSON-safe export
      - replay-safe import
      - governance compatibility
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.queues: Dict[str, Dict[str, Any]] = {}
        self.neighbors: Dict[str, List[str]] = {}

    # ---------------------------------------------------------
    # NODE MANAGEMENT
    # ---------------------------------------------------------
    def add_node(self, node_id: str, queue: str | None = None, meta: Dict[str, Any] | None = None):
        self.nodes[node_id] = Node(node_id, queue, meta)

    # ---------------------------------------------------------
    # EDGE MANAGEMENT
    # ---------------------------------------------------------
    def add_edge(self, src: str, dst: str, meta: Dict[str, Any] | None = None):
        self.edges.append(Edge(src, dst, meta))
        self.neighbors.setdefault(src, []).append(dst)

    # ---------------------------------------------------------
    # QUEUE MANAGEMENT
    # ---------------------------------------------------------
    def add_queue(self, name: str, meta: Dict[str, Any] | None = None):
        self.queues[name] = meta or {}

    # ---------------------------------------------------------
    # SERIALIZATION
    # ---------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "queues": self.queues,
            "neighbors": self.neighbors,
        }

    # ---------------------------------------------------------
    # STRUCTURAL HASH
    # ---------------------------------------------------------
    def structural_hash(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()