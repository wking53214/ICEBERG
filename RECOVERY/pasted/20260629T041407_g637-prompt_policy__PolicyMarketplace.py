# policy/PolicyMarketplace.py
from __future__ import annotations
from typing import Dict, Any, Callable


class PolicyMarketplace:
    """
    Pluggable policy hub for Iceberg 3.x.

    Supports:
      - routing policies
      - reward-shaping policies
      - governance policies
      - staffing policies
      - extraction policies

    Each policy is a callable:
      policy(context: Dict[str, Any]) -> Dict[str, Any]
    """

    def __init__(self):
        self._policies: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}

    # ---------------------------------------------------------
    # REGISTER
    # ---------------------------------------------------------
    def register(self, name: str, policy: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Register a policy by name.
        """
        self._policies[name] = policy

    # ---------------------------------------------------------
    # UNREGISTER
    # ---------------------------------------------------------
    def unregister(self, name: str):
        """
        Remove a policy.
        """
        if name in self._policies:
            del self._policies[name]

    # ---------------------------------------------------------
    # LIST
    # ---------------------------------------------------------
    def list(self) -> Dict[str, str]:
        """
        List available policies.
        """
        return {name: policy.__doc__ or "" for name, policy in self._policies.items()}

    # ---------------------------------------------------------
    # APPLY
    # ---------------------------------------------------------
    def apply(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a named policy to a context.
        """
        if name not in self._policies:
            raise KeyError(f"Policy '{name}' not found")

        return self._policies[name](context)

    # ---------------------------------------------------------
    # SAFE APPLY WITH FALLBACK
    # ---------------------------------------------------------
    def apply_or_default(
        self,
        name: str,
        context: Dict[str, Any],
        default: Callable[[Dict[str, Any]], Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        Apply a policy if present, otherwise use default.
        """
        if name in self._policies:
            return self._policies[name](context)
        if default:
            return default(context)
        return context