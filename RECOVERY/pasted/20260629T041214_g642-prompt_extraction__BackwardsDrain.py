# extraction/BackwardsDrain.py
from __future__ import annotations
from typing import List, Dict, Any

from extraction.ExtractionOS import ExtractionOS
from extraction.ManifestValidator import ManifestValidator


class BackwardsDrain:
    """
    Historical-ingestion pipeline for ExtractionOS.
    Processes older chats first, ensuring:
      - deterministic ordering
      - stable manifest evolution
      - version monotonicity
      - hash-based change detection
      - dependency reconciliation
      - conflict resolution
    """

    def __init__(self):
        self.kernel = ExtractionOS()
        self.validator = ManifestValidator()

    # ---------------------------------------------------------
    # ORDERING
    # ---------------------------------------------------------
    def _sort_oldest_first(self, chats: List[str]) -> List[str]:
        """
        BackwardsDrain always processes oldest chats first.
        Assumes chats are provided in chronological order.
        If not, caller must sort externally.
        """
        return chats  # already oldest → newest

    # ---------------------------------------------------------
    # INGEST
    # ---------------------------------------------------------
    def ingest(self, chats: List[str]) -> Dict[str, Any]:
        """
        Run ExtractionOS on each chat in oldest-first order.
        """
        ordered = self._sort_oldest_first(chats)
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
    def run(self, chats: List[str]) -> Dict[str, Any]:
        """
        Full BackwardsDrain pipeline.
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