# extraction/ForwardDrain.py
from __future__ import annotations
from typing import List, Dict, Any

from extraction.ExtractionOS import ExtractionOS
from extraction.ManifestValidator import ManifestValidator


class ForwardDrain:
    """
    Incremental-ingestion pipeline for ExtractionOS.
    Processes new chats in forward order, ensuring:
      - incremental manifest evolution
      - version monotonicity
      - hash-based change detection
      - dependency reconciliation
      - conflict resolution
      - stable forward-only growth
    """

    def __init__(self, existing_manifest: Dict[str, Any] | None = None):
        # ForwardDrain starts from an existing manifest
        self.kernel = ExtractionOS(manifest=existing_manifest)
        self.validator = ManifestValidator()

    # ---------------------------------------------------------
    # ORDERING
    # ---------------------------------------------------------
    def _sort_newest_first(self, chats: List[str]) -> List[str]:
        """
        ForwardDrain always processes newest chats first.
        Assumes chats are provided in chronological order.
        If not, caller must sort externally.
        """
        return chats[::-1]  # newest → oldest

    # ---------------------------------------------------------
    # INGEST
    # ---------------------------------------------------------
    def ingest(self, chats: List[str]) -> Dict[str, Any]:
        """
        Run ExtractionOS on each chat in newest-first order.
        """
        ordered = self._sort_newest_first(chats)
        results = []

        for idx, chat in enumerate(ordered):
            out = self.kernel.extract(chat)
            results.append({
                "chat_index": idx,
                "modules": list(out["files"].keys()),
                "done": out["done"],
            })

        return {
            "results": results,
            "manifest": self.kernel.manifest,
        }

    # ---------------------------------------------------------
    # VALIDATE
    # ---------------------------------------------------------
    def validate(self) -> Dict[str, Any]:
        return self.validator.validate(self.kernel.manifest)

    # ---------------------------------------------------------
    # EXPORT
    # ---------------------------------------------------------
    def export_files(self) -> Dict[str, str]:
        return self.kernel.output_files()

    def export_manifest(self) -> str:
        return self.kernel.export_manifest()

    # ---------------------------------------------------------
    # FULL PIPELINE
    # ---------------------------------------------------------
    def run(self, chats: List[str]) -> Dict[str,Any]:
        """
        Full ForwardDrain pipeline.
        """
        ingest_result = self.ingest(chats)
        validation = self.validate()
        files = self.export_files()

        return {
            "ingest": ingest_result,
            "validation": validation,
            "files": files,
            "manifest": self.kernel.manifest,
        }