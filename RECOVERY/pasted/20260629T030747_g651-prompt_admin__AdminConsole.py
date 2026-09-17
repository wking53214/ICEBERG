# admin/AdminConsole.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, Any

from governance.GovernanceEnvelope import GovernanceEnvelope
from replay.ReplayRunner import ReplayRunner
from replay.SnapshotManager import SnapshotManager
from telemetry.TelemetryAggregator import TelemetryAggregator
from cluster.ClusterRunner import ClusterRunner


def build_admin_console(
    graph,
    simulator,
    telemetry: TelemetryAggregator,
    governance: GovernanceEnvelope,
    replay_runner: ReplayRunner,
    snapshots: SnapshotManager,
    cluster: ClusterRunner,
):
    app = FastAPI(title="Iceberg 3.x Admin Console")

    # ---------------------------------------------------------
    # ROOT PAGE — ADMIN CONSOLE UI
    # ---------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    def root():
        return """
        <html>
        <head>
            <title>Iceberg Admin Console</title>
            <style>
                body { font-family: Arial; margin: 40px; }
                h1 { color: #333; }
                pre { background: #f4f4f4; padding: 20px; border-radius: 8px; }
                .section { margin-bottom: 40px; }
            </style>
        </head>
        <body>
            <h1>Iceberg 3.x Admin Console</h1>

            <div class="section">
                <h2>Governance</h2>
                <ul>
                    <li><a href="/governance/hash">Structural Hash</a></li>
                    <li><a href="/governance/drift">Drift Report</a></li>
                </ul>
            </div>

            <div class="section">
                <h2>Replay</h2>
                <ul>
                    <li><a href="/replay/help">Replay Instructions</a></li>
                </ul>
            </div>

            <div class="section">
                <h2>Snapshots</h2>
                <ul>
                    <li><a href="/snapshot/list">List Snapshots</a></li>
                </ul>
            </div>

            <div class="section">
                <h2>Telemetry</h2>
                <ul>
                    <li><a href="/telemetry">Raw Telemetry</a></li>
                    <li><a href="/telemetry/summary">Telemetry Summary</a></li>
                </ul>
            </div>

            <div class="section">
                <h2>Cluster</h2>
                <ul>
                    <li><a href="/cluster/help">Cluster Execution Instructions</a></li>
                </ul>
            </div>
        </body>
        </html>
        """

    # ---------------------------------------------------------
    # GOVERNANCE
    # ---------------------------------------------------------
    @app.get("/governance/hash")
    def governance_hash():
        return {
            "baseline": governance.baseline_hash(),
            "current": governance.current_hash(),
        }

    @app.get("/governance/drift")
    def governance_drift():
        return governance.drift_report()

    # ---------------------------------------------------------
    # TELEMETRY
    # ---------------------------------------------------------
    @app.get("/telemetry")
    def telemetry_dump():
        return telemetry.snapshot()

    @app.get("/telemetry/summary")
    def telemetry_summary():
        snap = telemetry.snapshot()
        events = snap["events"]

        callers = {}
        nodes = {}
        latent_drift = []

        for e in events:
            evt = e["event"]
            cid = evt.get("caller_id")
            node = evt.get("node")
            lat = evt.get("latent")

            if cid:
                callers[cid] = callers.get(cid, 0) + 1
            if node:
                nodes[node] = nodes.get(node, 0) + 1
            if lat:
                latent_drift.append(lat)

        return {
            "total_events": snap["count"],
            "callers": callers,
            "nodes": nodes,
            "latent_drift": latent_drift[-20:],
        }

    # ---------------------------------------------------------
    # SNAPSHOTS
    # ---------------------------------------------------------
    @app.get("/snapshot/list")
    def snapshot_list():
        import os
        files = os.listdir(snapshots.directory)
        return {"snapshots": files}

    @app.get("/snapshot/load/{name}")
    def snapshot_load(name: str):
        try:
            return snapshots.load(name)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Snapshot not found")

    @app.get("/snapshot/verify/{name}")
    def snapshot_verify(name: str):
        snap = snapshots.load(name)
        return snapshots.verify(snap, graph)

    # ---------------------------------------------------------
    # REPLAY
    # ---------------------------------------------------------
    @app.get("/replay/help")
    def replay_help():
        return {
            "instructions": [
                "POST /replay/run via HTTP API to replay a ledger.",
                "POST /replay/verify via HTTP API to verify deterministic replay.",
                "ReplayRunner is integrated with AdminConsole via HTTP API.",
            ]
        }

    # ---------------------------------------------------------
    # CLUSTER
    # ---------------------------------------------------------
    @app.get("/cluster/help")
    def cluster_help():
        return {
            "instructions": [
                "POST /cluster/run via HTTP API to execute parallel caller batches.",
                "ClusterRunner is governance-wrapped and telemetry-integrated.",
            ]
        }

    return app