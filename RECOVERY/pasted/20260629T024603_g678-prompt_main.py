# main.py
from __future__ import annotations

from model.build_graph import build_graph
from telemetry.aggregator import TelemetryAggregator

from engines.rl_ppo import PPORouter
from engines.rl_marl import IcebergMARL
from engines.staffing_rl import StaffingOptimizerRL

from simulator.simulator import IcebergSimulator
from simulator.cluster_runner import ClusterRunner


def bootstrap():
    """
    Boot the entire Iceberg 3.x system.
    """

    # ---------------------------------------------------------
    # 1. Build routing graph
    # ---------------------------------------------------------
    graph = build_graph()

    # ---------------------------------------------------------
    # 2. Telemetry
    # ---------------------------------------------------------
    telemetry = TelemetryAggregator(max_events=10000)

    # ---------------------------------------------------------
    # 3. RL Engines
    # ---------------------------------------------------------
    ppo_router = PPORouter(graph, graph.neighbors)
    marl_engine = IcebergMARL(graph, graph.queues, latent=None, priors=None)
    staffing_rl = StaffingOptimizerRL(graph, graph.queues, latent=None, priors=None)

    # ---------------------------------------------------------
    # 4. Simulator
    # ---------------------------------------------------------
    simulator = IcebergSimulator(
        graph=graph,
        ppo_router=ppo_router,
        marl_engine=marl_engine,
        staffing_rl=staffing_rl,
        telemetry=telemetry,
    )

    # ---------------------------------------------------------
    # 5. Cluster Runner
    # ---------------------------------------------------------
    cluster = ClusterRunner(
        graph=graph,
        simulator=simulator,
        telemetry=telemetry,
        num_workers=8,
    )

    return graph, simulator, cluster, telemetry


def main():
    graph, simulator, cluster, telemetry = bootstrap()

    print("Iceberg 3.x booted successfully.")
    print("Running cluster simulation...")

    result = cluster.run_cluster(
        num_callers=50,
        steps=12,
        start_node="root",
    )

    print("Cluster run complete.")
    print(result)


if __name__ == "__main__":
    main()