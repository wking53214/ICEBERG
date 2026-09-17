# config.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class RLConfig:
    """
    Reinforcement learning hyperparameters.
    Shared across PPO, MARL, and Staffing RL.
    """
    ppo_lr: float = 3e-4
    ppo_gamma: float = 0.99
    ppo_eps_clip: float = 0.2

    marl_lr: float = 3e-4
    marl_hidden: int = 32
    marl_agents: int = 4

    staffing_lr: float = 3e-4
    staffing_delta_limit: float = 0.5  # +/- FTE


@dataclass
class SimulatorConfig:
    """
    Simulator-level settings.
    """
    max_steps_per_call: int = 20
    perceived_wait_increment: float = 1.0
    frustration_rate: float = 0.02
    latent_memory_increment: float = 0.01


@dataclass
class ClusterConfig:
    """
    Parallel cluster runner settings.
    """
    num_workers: int = 8
    default_callers: int = 50
    default_steps: int = 12
    start_node: str = "root"


@dataclass
class GovernanceConfig:
    """
    Governance + structural integrity settings.
    """
    enable_structural_hash: bool = True
    enable_replay_recording: bool = True
    enable_seed_freeze: bool = True
    max_telemetry_events: int = 10000


@dataclass
class IcebergConfig:
    """
    Unified configuration object for Iceberg 3.x.
    """
    rl: RLConfig = RLConfig()
    simulator: SimulatorConfig = SimulatorConfig()
    cluster: ClusterConfig = ClusterConfig()
    governance: GovernanceConfig = GovernanceConfig()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rl": asdict(self.rl),
            "simulator": asdict(self.simulator),
            "cluster": asdict(self.cluster),
            "governance": asdict(self.governance),
        }

    def override(self, section: str, key: str, value: Any):
        """
        Override a configuration value at runtime.
        Example:
            cfg.override("rl", "ppo_lr", 1e-4)
        """
        if not hasattr(self, section):
            raise KeyError(f"Unknown config section: {section}")

        section_obj = getattr(self, section)
        if not hasattr(section_obj, key):
            raise KeyError(f"Unknown config key: {key}")

        setattr(section_obj, key, value)