# extraction/ExtractionOS_Driver.py
from __future__ import annotations
import json
from typing import Dict, Any, List

from extraction.ExtractionOS import ExtractionOS
from extraction.ManifestValidator import ManifestValidator


class ExtractionOSDriver:
    """
    Orchestrates ExtractionOS across multiple chats.
    Responsibilities:
      - ingest chat logs
      - run ExtractionOS on each chat
      - merge manifests
      - resolve version conflicts
      - detect hash changes
      - coordinate BackwardsDrain + ForwardDrain
      - validate final manifest
      - produce multi-file output
    """

    def __init__(self):
        self.kernel = ExtractionOS()
        self.validator = ManifestValidator()

    # ---------------------------------------------------------
    # INGEST CHAT LOGS
    # ---------------------------------------------------------
    def ingest_chats(self, chats: List[str]) -> Dict[str, Any]:
        """
        Each chat is a raw text block.
        ExtractionOS is run on each block.
        """
        results = []

        for idx, chat in enumerate(chats):
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
    # MERGE MANIFESTS (if multiple kernels are used)
    # ---------------------------------------------------------
    def merge_manifests(self, manifests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple manifests into the driver's manifest.
        Version and hash rules:
          - highest version wins
          - newest hash wins
        """
        for m in manifests:
            for name, body in m["modules"].items():
                incoming_version = m["versions"][name]
                incoming_hash = m["hashes"][name]

                current_version = self.kernel.manifest["versions"].get(name)
                current_hash = self.kernel.manifest["hashes"].get(name)

                # Version upgrade
                if current_version is None or incoming_version > current_version:
                    self.kernel.manifest["modules"][name] = body
                    self.kernel.manifest["versions"][name] = incoming_version
                    self.kernel.manifest["hashes"][name] = incoming_hash
                    self.kernel.manifest["dependencies"][name] = m["dependencies"][name]
                    self.kernel.manifest["timestamps"][name] = m["timestamps"][name]
                    continue

                # Hash update without version bump
                if incoming_hash != current_hash:
                    self.kernel.manifest["modules"][name] = body
                    self.kernel.manifest["hashes"][name] = incoming_hash
                    self.kernel.manifest["timestamps"][name] = m["timestamps"][name]

        return self.kernel.manifest

    # ---------------------------------------------------------
    # VALIDATE FINAL MANIFEST
    # ---------------------------------------------------------
    def validate(self) -> Dict[str, Any]:
        return self.validator.validate(self.kernel.manifest)

    # ---------------------------------------------------------
    # EXPORT FILES
    # ---------------------------------------------------------
    def export_files(self) -> Dict[str, str]:
        return self.kernel.output_files()

    # ---------------------------------------------------------
    # EXPORT MANIFEST
    # ---------------------------------------------------------
    def export_manifest(self) -> str:
        return self.kernel.export_manifest()

    # ---------------------------------------------------------
    # FULL PIPELINE
    # ---------------------------------------------------------
    def run(self, chats: List[str]) -> Dict[str, Any]:
        """
        Full multi-chat extraction pipeline.
        """
        ingest_result = self.ingest_chats(chats)
        validation = self.validate()
        files = self.export_files()

        return {
            "ingest": ingest_result,
            "validation": validation,
            "files": files,
            "manifest": self.kernel.manifest,
        }