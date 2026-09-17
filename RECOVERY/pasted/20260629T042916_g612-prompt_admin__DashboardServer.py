# admin/DashboardServer.py
from __future__ import annotations
from typing import Dict, Any

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

from admin.IcebergAdminDashboard import IcebergAdminDashboard


class DashboardServer:
    """
    Real-time web server wrapper for IcebergAdminDashboard.

    Provides:
      - REST endpoints for all dashboard panels
      - WebSocket streaming for live metrics
      - Governance + drift status endpoints
      - Replay snapshot endpoint
      - Load-test execution endpoint
    """

    def __init__(self, dashboard: IcebergAdminDashboard):
        self.dashboard = dashboard
        self.app = FastAPI()

        # Register routes
        self._register_routes()

    # ---------------------------------------------------------
    # ROUTES
    # ---------------------------------------------------------
    def _register_routes(self):

        @self.app.get("/live")
        def live_metrics():
            return JSONResponse(self.dashboard.live_metrics())

        @self.app.get("/analytics")
        def analytics():
            return JSONResponse(self.dashboard.analytics.report())

        @self.app.get("/governance")
        def governance():
            return JSONResponse(self.dashboard.governance.status())

        @self.app.get("/drift/{baseline_hash}")
        def drift(baseline_hash: str):
            return JSONResponse(self.dashboard.drift_status(baseline_hash))

        @self.app.get("/replay")
        def replay_snapshot():
            return JSONResponse(self.dashboard.replay_snapshot())

        @self.app.post("/load/suite")
        def run_load_suite():
            return JSONResponse(self.dashboard.run_load_suite())

        @self.app.post("/routing")
        def routing_diagnostics(caller_context: Dict[str, Any]):
            return JSONResponse(self.dashboard.routing_diagnostics(caller_context))

        @self.app.get("/report")
        def full_report():
            return JSONResponse(self.dashboard.report())

        # -----------------------------------------------------
        # WEBSOCKET STREAMING
        # -----------------------------------------------------
        @self.app.websocket("/stream/live")
        async def live_stream(ws: WebSocket):
            await ws.accept()
            while True:
                await ws.send_json(self.dashboard.live_metrics())

    # ---------------------------------------------------------
    # RETURN FASTAPI APP
    # ---------------------------------------------------------
    def build(self) -> FastAPI:
        return self.app