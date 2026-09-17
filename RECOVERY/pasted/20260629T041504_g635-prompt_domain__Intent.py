# domain/Intent.py
from __future__ import annotations
from enum import Enum


class Intent(Enum):
    """
    Canonical intent categories for Iceberg 3.x.
    These map directly into:
      - Bayesian posterior keys
      - PPO state vector
      - MARL state vector
      - Simulator routing logic
    """

    BILLING = 0
    TECH = 1
    FRAUD = 2
    GENERAL = 3

    @staticmethod
    def from_str(name: str) -> "Intent":
        name = name.lower()
        if name == "billing":
            return Intent.BILLING
        if name == "tech":
            return Intent.TECH
        if name == "fraud":
            return Intent.FRAUD
        return Intent.GENERAL

    @staticmethod
    def list() -> list:
        return [
            Intent.BILLING,
            Intent.TECH,
            Intent.FRAUD,
            Intent.GENERAL,
        ]