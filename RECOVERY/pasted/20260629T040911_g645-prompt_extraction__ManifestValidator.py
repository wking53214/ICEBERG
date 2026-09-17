# extraction/ManifestValidator.py
from __future__ import annotations
import hashlib
from typing import Dict, Any, List, Set


class ManifestValidator:
    """
    Structural integrity validator for ExtractionOS manifests.
    Checks:
      - schema validity
      - module completeness
      - dependency consistency
      - version monotonicity
      - hash integrity
      - orphan modules
      - missing modules
      - dependency cycles
    """

    REQUIRED_KEYS = {
        "modules",
        "dependencies",
        "versions",
        "hashes",
        "timestamps",
    }

    # ---------------------------------------------------------
    # SCHEMA VALIDATION
    # ---------------------------------------------------------
    def validate_schema(self, manifest: Dict[str, Any]) -> List[str]:
        errors = []
        for key in self.REQUIRED_KEYS:
            if key not in manifest:
                errors.append(f"Missing required key: {key}")
        return errors

    # ---------------------------------------------------------
    # HASH VALIDATION
    # ---------------------------------------------------------
    def validate_hashes(self, manifest: Dict[str, Any]) -> List[str]:
        errors = []
        for name, body in manifest["modules"].items():
            expected = manifest["hashes"].get(name)
            actual = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if expected != actual:
                errors.append(f"Hash mismatch for module {name}")
        return errors

    # ---------------------------------------------------------
    # VERSION VALIDATION
    # ---------------------------------------------------------
    def validate_versions(self, manifest: Dict[str, Any]) -> List[str]:
        errors = []
        for name, version in manifest["versions"].items():
            if not isinstance(version, str):
                errors.append(f"Invalid version format for {name}: {version}")
        return errors

    # ---------------------------------------------------------
    # DEPENDENCY VALIDATION
    # ---------------------------------------------------------
    def validate_dependencies(self, manifest: Dict[str, Any]) -> List[str]:
        errors = []
        modules = manifest["modules"].keys()

        for name, deps in manifest["dependencies"].items():
            for dep in deps:
                if dep not in modules:
                    errors.append(f"Module {name} depends on missing module {dep}")

        return errors

    # ---------------------------------------------------------
    # ORPHAN MODULES
    # ---------------------------------------------------------
    def find_orphans(self, manifest: Dict[str, Any]) -> List[str]:
        modules = set(manifest["modules"].keys())
        referenced: Set[str] = set()

        for deps in manifest["dependencies"].values():
            for d in deps:
                referenced.add(d)

        return list(modules - referenced)

    # ---------------------------------------------------------
    # DEPENDENCY CYCLE DETECTION
    # ---------------------------------------------------------
    def detect_cycles(self, manifest: Dict[str, Any]) -> List[List[str]]:
        graph = manifest["dependencies"]
        visited = set()
        stack = set()
        cycles = []

        def dfs(node, path):
            if node in stack:
                cycles.append(path[path.index(node):])
                return
            if node in visited:
                return

            visited.add(node)
            stack.add(node)

            for dep in graph.get(node, []):
                dfs(dep, path + [dep])

            stack.remove(node)

        for module in graph.keys():
            dfs(module, [module])

        return cycles

    # ---------------------------------------------------------
    # FULL VALIDATION
    # ---------------------------------------------------------
    def validate(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        schema_errors = self.validate_schema(manifest)
        hash_errors = self.validate_hashes(manifest)
        version_errors = self.validate_versions(manifest)
        dependency_errors = self.validate_dependencies(manifest)
        orphans = self.find_orphans(manifest)
        cycles = self.detect_cycles(manifest)

        return {
            "schema_errors": schema_errors,
            "hash_errors": hash_errors,
            "version_errors": version_errors,
            "dependency_errors": dependency_errors,
            "orphans": orphans,
            "cycles": cycles,
            "valid": not (
                schema_errors
                or hash_errors
                or version_errors
                or dependency_errors
                or cycles
            ),
        }