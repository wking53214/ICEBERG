# dashboard/DashboardServer.py
from __future__ import annotations
import json
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from typing import Dict, Any

from telemetry.TelemetryAggregator import TelemetryAggregator
from replay.ReplayRunner import ReplayRunner
from governance.GovernanceEnvelope import GovernanceEnvelope


def build_dashboard(graph, simulator, telemetry: TelemetryAggregator, replay_runner: ReplayRunner, governance: GovernanceEnvelope):
    app = FastAPI(title="Iceberg 3.x Dashboard")

    # ---------------------------------------------------------
    # ROOT PAGE — SIMPLE HTML DASHBOARD
    # ---------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    def root():
        return """
        <html>
        <head>
            <title>Iceberg Dashboard</title>
            <style>
                body { font-family: Arial; margin: 40px; }
                h1 { color: #333; }
                pre { background: #f4f4f4; padding: 20px; border-radius: 8px; }
            </style>
        </head>
        <body>
            <h1>Iceberg 3.x Dashboard</h1>
            <p>Use the endpoints below to view telemetry, replay summaries, and governance drift.</p>
            <ul>
                <li><a href="/telemetry">/telemetry</a></li>
                <li><a href="/telemetry/summary">/telemetry/summary</a></li>
                <li><a href="/governance/drift">/governance/drift</a></li>
                <li><a href="/replay/summary">/replay/summary</a></li>
            </ul>
        </body>
        </html>
        """

    # ---------------------------------------------------------
    # RAW TELEMETRY
    # ---------------------------------------------------------
    @app.get("/telemetry")
    def telemetry_dump():
        return telemetry.snapshot()

    # ---------------------------------------------------------
    # TELEMETRY SUMMARY
    # ---------------------------------------------------------
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
            "latent_drift": latent_drift[-20:],  # last 20 latent snapshots
        }

    # ---------------------------------------------------------
    # GOVERNANCE DRIFT
    # ---------------------------------------------------------
    @app.get("/governance/drift")
    def governance_drift():
        return governance.drift_report()

    # ---------------------------------------------------------
    # REPLAY SUMMARY
    # ---------------------------------------------------------
    @app.get("/replay/summary")
    def replay_summary():
        # ReplayRunner stores no ledger itself; user provides path
        return {
            "message": "POST /replay/run or /replay/verify via HTTP API to generate replay summaries."
        }

    return app