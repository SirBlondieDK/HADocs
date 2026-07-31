from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "1.0.0"
REQUIRED = (
    "applicability.json", "competing_causes.json", "conflicts.json", "diagnostic_scenarios.json",
    "evidence_catalog.json", "evidence_matchers.json", "known_gaps.json", "platform_index.json",
    "provenance.json", "readiness.json", "recommendations.json", "root_cause_candidates.json",
    "verification_paths.json",
)


class BundleError(ValueError):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


def negotiate_version(producer: str, consumer: str = CONTRACT_VERSION) -> str:
    try:
        left, right = tuple(map(int, producer.split("."))), tuple(map(int, consumer.split(".")))
    except (AttributeError, ValueError) as exc:
        raise BundleError("schema_failed", "invalid semantic version") from exc
    if len(left) != 3 or len(right) != 3:
        raise BundleError("schema_failed", "invalid semantic version")
    if left[0] != right[0]:
        return "incompatible_major_version"
    return "compatible_with_unknown_fields" if left[1] > right[1] else "compatible"


def _aggregate(path: Path) -> str:
    digest = hashlib.sha256()
    for name in sorted(REQUIRED):
        digest.update(name.encode()); digest.update(b"\0"); digest.update((path / name).read_bytes()); digest.update(b"\0")
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class HaskBundle:
    manifest: dict[str, Any]
    artifacts: dict[str, dict[str, Any]]

    def items(self, artifact: str) -> tuple[dict[str, Any], ...]:
        return tuple(self.artifacts[artifact]["items"])

    def index(self, artifact: str) -> dict[str, dict[str, Any]]:
        return {item["id"]: item for item in self.items(artifact)}

    def platform(self, platform_id: str) -> dict[str, Any]:
        try:
            return self.index("platform_index.json")[platform_id]
        except KeyError as exc:
            raise BundleError("no_match", f"platform {platform_id} not found") from exc


def load_bundle(path: Path, *, strict: bool = True) -> HaskBundle:
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        raise BundleError("incomplete_bundle", "manifest is missing")
    missing = [name for name in REQUIRED if not (path / name).is_file()]
    if missing:
        raise BundleError("incomplete_bundle", f"missing bundle file {missing[0]}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BundleError("schema_failed", "invalid manifest") from exc
    version_result = negotiate_version(manifest.get("contract_version"))
    if version_result == "incompatible_major_version":
        raise BundleError(version_result, "unsupported contract major version")
    if set(manifest.get("artifacts", {})) != set(REQUIRED):
        raise BundleError("schema_failed", "manifest artifact set differs from contract")
    artifacts: dict[str, dict[str, Any]] = {}
    for name in REQUIRED:
        raw = (path / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["artifacts"][name]:
            raise BundleError("checksum_failed", f"checksum failed for {name}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BundleError("schema_failed", f"invalid JSON in {name}") from exc
        if not isinstance(value, dict) or value.get("contract_version") is None or not isinstance(value.get("items"), list):
            raise BundleError("schema_failed", f"invalid typed artifact {name}")
        artifacts[name] = value
    if _aggregate(path) != manifest.get("artifact_sha256"):
        raise BundleError("checksum_failed", "aggregate checksum failed")
    if strict:
        ids = {item["id"] for artifact in artifacts.values() for item in artifact["items"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
        unresolved: list[str] = []
        for artifact in artifacts.values():
            for item in artifact["items"]:
                for targets in item.get("references", {}).values():
                    unresolved.extend(target for target in targets if target not in ids)
                unresolved.extend(edge["target_id"] for edge in item.get("relationships", []) if edge["target_id"] not in ids)
                for claim in item.get("claims", []):
                    unresolved.extend(source for source in claim.get("source_ids", []) if source not in ids)
        if unresolved:
            raise BundleError("unresolved_reference", sorted(set(unresolved))[0])
    return HaskBundle(manifest, artifacts)
