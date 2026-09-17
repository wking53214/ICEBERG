# domain/Emotion.py
from __future__ import annotations
from enum import Enum


class Emotion(Enum):
    """
    Canonical emotional states for Iceberg 3.x.
    These map directly into:
      - PPO state vector
      - MARL state vector
      - Caller dynamic modeling
    """

    NEUTRAL = "neutral"
    IMPATIENT = "impatient"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"

    @staticmethod
    def from_str(name: str) -> "Emotion":
        name = name.lower()
        if name == "neutral":
            return Emotion.NEUTRAL
        if name == "impatient":
            return Emotion.IMPATIENT
        if name == "frustrated":
            return Emotion.FRUSTRATED
        return Emotion.ANGRY

    @staticmethod
    def list() -> list:
        return [
            Emotion.NEUTRAL,
            Emotion.IMPATIENT,
            Emotion.FRUSTRATED,
            Emotion.ANGRY,
        ]