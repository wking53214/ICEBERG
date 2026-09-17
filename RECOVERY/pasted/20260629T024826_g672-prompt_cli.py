# cli.py
from __future__ import annotations
import argparse
import json

from config import IcebergConfig
from governance.governance import GovernanceEnvelope
from simulator.simulator import IcebergSimulator
from simulator.cluster_runner import ClusterRunner
from telemetry.aggregator import TelemetryAggregator
from model.build_graph import build_graph

from domain.CallerState import CallerState
from domain.Intent import Intent
from domain.Emotion import Emotion


def bootstrap():
    """
    Boot Iceberg components for CLI usage.
    """
    cfg = IcebergConfig()

    graph = build_graph()
    telemetry = TelemetryAggregator(max_events=cfg.governance.max_telemetry_events)

    from engines.rl_ppo import PPORouter
    from engines.rl_marl import IcebergMARL
    from engines.staffing_rl import StaffingOptimizerRL

    ppo_router = PPORouter(graph, graph.neighbors)
    marl_engine = IcebergMARL(graph, graph.queues, latent=None, priors=None)
    staffing_rl = StaffingOptimizerRL(graph, graph.queues, latent=None, priors=None)

    simulator = IcebergSimulator(
        graph=graph,
        ppo_router=ppo_router,
        marl_engine=marl_engine,
        staffing_rl=staffing_rl,
        telemetry=telemetry,
    )

    cluster = ClusterRunner(
        graph=graph,
        simulator=simulator,
        telemetry=telemetry,
        num_workers=cfg.cluster.num_workers,
    )

    gov = GovernanceEnvelope(graph, cfg.governance)

    return cfg, graph, simulator, cluster, telemetry, gov


def run_simulate(args, simulator):
    intent = Intent[args.intent]
    emotion = Emotion[args.emotion]

    caller = CallerState(
        caller_id=args.caller_id,
        intent=intent,
        emotion=emotion,
        posterior={
            "billing": 0.25,
            "tech": 0.25,
            "fraud": 0.25,
            "general": 0.25,
        },
    )

    out = simulator.step(caller, args.node)
    print(json.dumps(out, indent=2))


def run_cluster(args, cluster):
    result = cluster.run_cluster(
        num_callers=args.callers,
        steps=args.steps,
        start_node=args.node,
    )
    print(json.dumps(result, indent=2))


def run_governance(gov):
    print(json.dumps(gov.governance_gate(), indent=2))


def run_replay_verify(gov):
    print(json.dumps(gov.verify_replay(), indent=2))


def run_snapshot_verify(args, gov):
    print(json.dumps(gov.verify_snapshot(args.name), indent=2))


def run_telemetry(telemetry):
    print(json.dumps(telemetry.dump(), indent=2))


def main():
    cfg, graph, simulator, cluster, telemetry, gov = bootstrap()

    parser = argparse.ArgumentParser(description="Iceberg 3.x CLI")
    sub = parser.add_subparsers(dest="cmd")

    # simulate
    sim = sub.add_parser("simulate", help="Run a single caller simulation")
    sim.add_argument("--caller_id", required=True)
    sim.add_argument("--intent", required=True)
    sim.add_argument("--emotion", required=True)
    sim.add_argument("--node", default="root")

    # cluster
    cl = sub.add_parser("cluster", help="Run a cluster simulation")
    cl.add_argument("--callers", type=int, default=50)
    cl.add_argument("--steps", type=int, default=12)
    cl.add_argument("--node", default="root")

    # governance
    sub.add_parser("governance", help="Run governance gate")

    # replay verify
    sub.add_parser("replay_verify", help="Verify replay ledger")

    # snapshot verify
    snap = sub.add_parser("snapshot_verify", help="Verify a snapshot")
    snap.add_argument("--name", required=True)

    # telemetry
    sub.add_parser("telemetry", help="Dump telemetry")

    args = parser.parse_args()

    if args.cmd == "simulate":
        run_simulate(args, simulator)
    elif args.cmd == "cluster":
        run_cluster(args, cluster)
    elif args.cmd == "governance":
        run_governance(gov)
    elif args.cmd == "replay_verify":
        run_replay_verify(gov)
    elif args.cmd == "snapshot_verify":
        run_snapshot_verify(args, gov)
    elif args.cmd == "telemetry":
        run_telemetry(telemetry)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()