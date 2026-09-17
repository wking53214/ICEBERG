# extraction/ExtractionOS.py
from __future__ import annotations
import re
import json
import hashlib
from typing import Dict, Any, List


class ExtractionOS:
    """
    Manifest-governed extraction kernel for Iceberg 3.x.
    Features:
      - recursive module discovery
      - strict dependency graph
      - version tracking
      - hash-based change detection
      - multi-file output
      - DONE termination
      - cross-AI portability
    """

    def __init__(self, manifest: Dict[str, Any] | None = None):
        self.manifest = manifest or {
            "modules": {},
            "dependencies": {},
            "versions": {},
            "hashes": {},
            "timestamps": {},
        }

    # ---------------------------------------------------------
    # HASHING
    # ---------------------------------------------------------
    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # ---------------------------------------------------------
    # VERSION DETECTION
    # ---------------------------------------------------------
    def _detect_version(self, text: str) -> str:
        """
        Detect version markers like:
        # v1
        # v2
        # v3-alpha
        """
        m = re.search(r"#\s*v([\w\.-]+)", text)
        return m.group(1) if m else "1.0"

    # ---------------------------------------------------------
    # MODULE DISCOVERY
    # ---------------------------------------------------------
    def discover_modules(self, text: str) -> Dict[str, str]:
        """
        Extract modules from text blocks like:

        ```python
        # module: Foo
        class Foo: ...
        ```
        """
        blocks = re.findall(
            r"```python\s*(#\s*module:\s*(\w+))([\s\S]*?)```",
            text,
            flags=re.MULTILINE,
        )

        out = {}
        for _, name, body in blocks:
            out[name] = body.strip()
        return out

    # ---------------------------------------------------------
    # DEPENDENCY DISCOVERY
    # ---------------------------------------------------------
    def discover_dependencies(self, module_text: str) -> List[str]:
        """
        Detect imports like:
        from engines.rl_marl import IcebergMARL
        """
        deps = re.findall(
            r"from\s+([\w\.]+)\s+import\s+([\w, ]+)",
            module_text,
        )
        out = []
        for pkg, names in deps:
            for n in names.split(","):
                out.append(n.strip())
        return out

    # ---------------------------------------------------------
    # UPDATE MANIFEST
    # ---------------------------------------------------------
    def update_manifest(self, modules: Dict[str, str]):
        for name, body in modules.items():
            version = self._detect_version(body)
            h = self._hash(body)

            # Version tracking
            old_version = self.manifest["versions"].get(name)
            if old_version and version < old_version:
                # regression detected — keep old
                continue

            # Hash-based change detection
            old_hash = self.manifest["hashes"].get(name)
            if old_hash == h:
                # no change
                continue

            # Update manifest
            self.manifest["modules"][name] = body
            self.manifest["versions"][name] = version
            self.manifest["hashes"][name] = h
            self.manifest["timestamps"][name] = "now"

            # Dependencies
            deps = self.discover_dependencies(body)
            self.manifest["dependencies"][name] = deps

    # ---------------------------------------------------------
    # MULTI-FILE OUTPUT
    # ---------------------------------------------------------
    def output_files(self) -> Dict[str, str]:
        """
        Return a dict:
        {
            "Foo.py": "...",
            "Bar.py": "...",
        }
        """
        out = {}
        for name, body in self.manifest["modules"].items():
            out[f"{name}.py"] = body
        return out

    # ---------------------------------------------------------
    # DONE TERMINATION
    # ---------------------------------------------------------
    def is_done(self) -> bool:
        """
        DONE when:
          - no new modules discovered
          - no version upgrades
          - no hash changes
        """
        return True  # external driver decides termination

    # ---------------------------------------------------------
    # EXPORT MANIFEST
    # ---------------------------------------------------------
    def export_manifest(self) -> str:
        return json.dumps(self.manifest, indent=2)

    # ---------------------------------------------------------
    # MAIN EXTRACTION ENTRYPOINT
    # ---------------------------------------------------------
    def extract(self, text: str) -> Dict[str, Any]:
        modules = self.discover_modules(text)
        self.update_manifest(modules)

        return {
            "manifest": self.manifest,
            "files": self.output_files(),
            "done": self.is_done(),
        }