# graph/NodeModel.py
from __future__ import annotations
from typing import Dict, Any, Optional


class NodeModel:
    """
    Rich node metadata for Iceberg 3.x.

    Provides:
      - queue binding
      - routing rules
      - intent weighting
      - emotion weighting
      - entry/exit flags
      - governance metadata
      - structural-hash-safe serialization
    """

    def __init__(
        self,
        node_id: str,
        queue: Optional[str] = None,
        *,
        entry: bool = False,
        exit: bool = False,
        intent_weights: Optional[Dict[str, float]] = None,
        emotion_weights: Optional[Dict[str, float]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.queue = queue
        self.entry = entry
        self.exit = exit
        self.intent_weights = intent_weights or {}
        self.emotion_weights = emotion_weights or {}
        self.meta = meta or {}

    # ---------------------------------------------------------
    # SERIALIZATION
    # ---------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """
        JSON-safe export for structural hashing.
        """
        return {
            "node_id": self.node_id,
            "queue": self.queue,
            "entry": self.entry,
            "exit": self.exit,
            "intent_weights": self.intent_weights,
            "emotion_weights": self.emotion_weights,
            "meta": self.meta,
        }

    # ---------------------------------------------------------
    # ROUTING RULES
    # ---------------------------------------------------------
    def weight_for_intent(self, intent: str) -> float:
        """
        Return routing weight for a given intent.
        """
        return self.intent_weights.get(intent, 1.0)

    def weight_for_emotion(self, emotion: str) -> float:
        """
        Return routing weight for a given emotion.
        """
        return self.emotion_weights.get(emotion, 1.0)