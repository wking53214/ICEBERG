# cli/iceberg_cli.py
from __future__ import annotations
import argparse
import json
import sys

from replay.ReplayRunner import ReplayRunner
from replay.SnapshotManager import SnapshotManager
from replay.ReplayVerifier import ReplayVerifier


class IcebergCLI:
    """
    Command-line interface for Iceberg 3.x.
    Provides:
      - replay-run
      - replay-verify
      - snapshot-save
      - snapshot-load
      - snapshot-verify
    """

    def __init__(self, graph, simulator):
        self.graph = graph
        self.simulator = simulator
        self.runner = ReplayRunner(graph, simulator)
        self.snapshots = SnapshotManager()
        self.verifier = ReplayVerifier(graph, simulator)

    # ---------------------------------------------------------
    # REPLAY RUN
    # ---------------------------------------------------------
    def replay_run(self, ledger_path: str, snapshot_name: str | None):
        result = self.runner.run(ledger_path, snapshot_name)
        print(json.dumps(result, indent=2))

    # ---------------------------------------------------------
    # REPLAY VERIFY
    # ---------------------------------------------------------
    def replay_verify(self, ledger_path: str):
        result = self.verifier.verify(ledger_path)
        print(json.dumps(result, indent=2))

    # ---------------------------------------------------------
    # SNAPSHOT SAVE
    # ---------------------------------------------------------
    def snapshot_save(self, name: str, caller, node_id: str):
        structural_hash = self.verifier.compute_structural_hash()
        snap = self.snapshots.save(
            name=name,
            caller=caller,
            node_id=node_id,
            latent=self.simulator.latent,
            queues=self.graph.queues,
            structural_hash=structural_hash,
        )
        print(json.dumps(snap, indent=2))

    # ---------------------------------------------------------
    # SNAPSHOT LOAD
    # ---------------------------------------------------------
    def snapshot_load(self, name: str):
        snap = self.snapshots.load(name)
        print(json.dumps(snap, indent=2))

    # ---------------------------------------------------------
    # SNAPSHOT VERIFY
    # ---------------------------------------------------------
    def snapshot_verify(self, name: str):
        snap = self.snapshots.load(name)
        result = self.snapshots.verify(snap, self.graph)
        print(json.dumps(result, indent=2))


# -------------------------------------------------------------
# ENTRYPOINT
# -------------------------------------------------------------
def main(graph, simulator):
    cli = IcebergCLI(graph, simulator)

    parser = argparse.ArgumentParser(description="Iceberg 3.x CLI")
    sub = parser.add_subparsers(dest="cmd")

    # replay-run
    rr = sub.add_parser("replay-run")
    rr.add_argument("ledger")
    rr.add_argument("--snapshot", default=None)

    # replay-verify
    rv = sub.add_parser("replay-verify")
    rv.add_argument("ledger")

    # snapshot-save
    ss = sub.add_parser("snapshot-save")
    ss.add_argument("name")
    ss.add_argument("caller_id")
    ss.add_argument("node")

    # snapshot-load
    sl = sub.add_parser("snapshot-load")
    sl.add_argument("name")

    # snapshot-verify
    sv = sub.add_parser("snapshot-verify")
    sv.add_argument("name")

    args = parser.parse_args()

    if args.cmd == "replay-run":
        cli.replay_run(args.ledger, args.snapshot)
    elif args.cmd == "replay-verify":
        cli.replay_verify(args.ledger)
    elif args.cmd == "snapshot-save":
        print("Snapshot-save requires a live caller object; integrate with your runtime.")
    elif args.cmd == "snapshot-load":
        cli.snapshot_load(args.name)
    elif args.cmd == "snapshot-verify":
        cli.snapshot_verify(args.name)
    else:
        parser.print_help()
        sys.exit(1)