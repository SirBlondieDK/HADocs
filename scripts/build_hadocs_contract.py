from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "scripts" / "hask_bundle_sources"
BUNDLE_ROOT = REPOSITORY_ROOT / "src" / "hadocs" / "knowledge" / "hask_bundle"
GENERATED_MARKER = "scripts/build_hadocs_contract.py; DO NOT EDIT"
_VERSION_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
)

if str(REPOSITORY_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from hadocs.knowledge.hask_pilot.loader import REQUIRED, BundleError  # noqa: E402
from hadocs.knowledge.hask_runtime.models import RuntimeBundle, freeze  # noqa: E402
from hadocs.knowledge.hask_runtime.provider import KnowledgeProvider  # noqa: E402
from hadocs.knowledge.hask_runtime.validation import ContractValidator  # noqa: E402


class BundleBuildError(ValueError):
    """A deterministic, public-safe bundle generation failure."""


@dataclass(frozen=True, slots=True)
class BuildResult:
    bundle_path: Path
    changed_files: tuple[str, ...]
    artifact_sha256: str


def canonical_json_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise BundleBuildError("bundle source is not canonical JSON data") from error
    return (text + "\n").encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BundleBuildError(f"invalid JSON source: {path.name}") from error
    if not isinstance(value, dict):
        raise BundleBuildError(f"invalid object source: {path.name}")
    return value


def _identity(item: Mapping[str, object]) -> str:
    identity = item.get("id")
    if isinstance(identity, str) and identity:
        return f"id:{identity}"
    platform = item.get("platform")
    if isinstance(platform, str) and platform:
        return f"platform:{platform}"
    raise BundleBuildError("artifact item is missing a stable identity")


def _validate_artifacts(
    artifacts: Mapping[str, dict[str, Any]], contract_version: str
) -> None:
    if set(artifacts) != set(REQUIRED):
        raise BundleBuildError("bundle artifact set differs from the runtime contract")

    global_ids: set[str] = set()
    readiness_platforms: set[str] = set()
    for name in REQUIRED:
        artifact = artifacts[name]
        expected_kind = name.removesuffix(".json")
        if (
            set(artifact) != {
                "_generated",
                "artifact_kind",
                "contract_version",
                "items",
                "metadata",
            }
            or artifact.get("_generated") != GENERATED_MARKER
            or artifact.get("artifact_kind") != expected_kind
            or artifact.get("contract_version") != contract_version
            or not isinstance(artifact.get("items"), list)
            or not isinstance(artifact.get("metadata"), dict)
        ):
            raise BundleBuildError(f"schema validation failed for {name}")

        local: set[str] = set()
        for item in artifact["items"]:
            if not isinstance(item, dict):
                raise BundleBuildError(f"schema validation failed for {name}")
            identity = _identity(item)
            if identity in local:
                raise BundleBuildError(f"duplicate identity in {name}: {identity}")
            local.add(identity)
            if identity.startswith("id:"):
                raw_id = identity.removeprefix("id:")
                if raw_id in global_ids:
                    raise BundleBuildError(f"duplicate bundle id: {raw_id}")
                global_ids.add(raw_id)
            elif name == "readiness.json":
                platform = identity.removeprefix("platform:")
                if platform in readiness_platforms:
                    raise BundleBuildError(
                        f"duplicate readiness platform: {platform}"
                    )
                readiness_platforms.add(platform)
            else:
                raise BundleBuildError(
                    f"non-readiness item lacks an id in {name}"
                )

    unresolved: set[str] = set()
    for artifact in artifacts.values():
        for item in artifact["items"]:
            references = item.get("references", {})
            if not isinstance(references, dict):
                raise BundleBuildError("record references have an invalid shape")
            for targets in references.values():
                if not isinstance(targets, list) or not all(
                    isinstance(target, str) and target for target in targets
                ):
                    raise BundleBuildError("record references have an invalid shape")
                unresolved.update(target for target in targets if target not in global_ids)
            relationships = item.get("relationships", [])
            if not isinstance(relationships, list):
                raise BundleBuildError("record relationships have an invalid shape")
            for relationship in relationships:
                if not isinstance(relationship, dict):
                    raise BundleBuildError("record relationships have an invalid shape")
                target = relationship.get("target_id")
                if not isinstance(target, str) or not target:
                    raise BundleBuildError("record relationship target is invalid")
                if target not in global_ids:
                    unresolved.add(target)
            claims = item.get("claims", [])
            if not isinstance(claims, list):
                raise BundleBuildError("record claims have an invalid shape")
            for claim in claims:
                if not isinstance(claim, dict):
                    raise BundleBuildError("record claims have an invalid shape")
                sources = claim.get("source_ids", [])
                if not isinstance(sources, list):
                    raise BundleBuildError("claim provenance has an invalid shape")
                unresolved.update(
                    source for source in sources
                    if not isinstance(source, str) or source not in global_ids
                )
    if unresolved:
        raise BundleBuildError(
            f"unresolved bundle reference: {sorted(unresolved)[0]}"
        )


def _update_metadata(artifacts: dict[str, dict[str, Any]]) -> None:
    evidence = artifacts["evidence_catalog.json"]
    evidence["metadata"] = {
        "claim_count": sum(
            item.get("type") == "claim" for item in evidence["items"]
        ),
        "evidence_record_count": sum(
            item.get("type") != "claim" for item in evidence["items"]
        ),
    }
    platforms = artifacts["platform_index.json"]
    platforms["metadata"] = {"platform_count": len(platforms["items"])}
    readiness = artifacts["readiness.json"]
    readiness_counts: dict[str, int] = {}
    for item in readiness["items"]:
        state = str(item.get("readiness", "UNKNOWN"))
        readiness_counts[state] = readiness_counts.get(state, 0) + 1
    readiness["metadata"] = {
        "readiness_counts": dict(sorted(readiness_counts.items()))
    }
    root_causes = artifacts["root_cause_candidates.json"]
    root_causes["metadata"] = {
        "confirmed_count": sum(
            item.get("status") == "confirmed" for item in root_causes["items"]
        )
    }
    verification = artifacts["verification_paths.json"]
    verification["metadata"] = {
        "incomplete_count": sum(
            item.get("verification_status") != "complete"
            for item in verification["items"]
        )
    }


def _record_count(artifacts: Mapping[str, dict[str, Any]]) -> int:
    primary = (
        "diagnostic_scenarios.json",
        "evidence_matchers.json",
        "platform_index.json",
        "provenance.json",
        "recommendations.json",
        "root_cause_candidates.json",
    )
    return sum(len(artifacts[name]["items"]) for name in primary) + int(
        artifacts["evidence_catalog.json"]["metadata"]["evidence_record_count"]
    )


def _manifest(
    base: Mapping[str, Any],
    version: str,
    artifacts: Mapping[str, dict[str, Any]],
    artifact_bytes: Mapping[str, bytes],
) -> dict[str, Any]:
    hashes = {
        name: hashlib.sha256(artifact_bytes[name]).hexdigest()
        for name in sorted(REQUIRED)
    }
    aggregate = hashlib.sha256()
    for name in sorted(REQUIRED):
        aggregate.update(name.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(artifact_bytes[name])
        aggregate.update(b"\0")

    manifest = dict(base)
    manifest.update(
        {
            "_generated": GENERATED_MARKER,
            "artifact_sha256": aggregate.hexdigest(),
            "artifacts": hashes,
            "bundle_file_count": len(REQUIRED),
            "claim_count": len(artifacts["applicability.json"]["items"]),
            "consumer_ready_platform_count": sum(
                item.get("readiness") == "CONSUMER_READY"
                for item in artifacts["readiness.json"]["items"]
            ),
            "generated_at": "content-addressed-no-wall-clock",
            "knowledge_content_version": version,
            "platform_count": len(artifacts["platform_index.json"]["items"]),
            "record_count": _record_count(artifacts),
            "relationship_count": sum(
                len(item.get("relationships", []))
                for artifact in artifacts.values()
                for item in artifact["items"]
            ),
        }
    )
    return manifest


def _apply_source_spec(
    artifacts: dict[str, dict[str, Any]], source: Mapping[str, Any]
) -> None:
    additions = source.get("additions", {})
    replacements = source.get("replacements", {})
    if not isinstance(additions, dict) or not isinstance(replacements, dict):
        raise BundleBuildError("bundle source patch has an invalid shape")

    touched: set[str] = set()
    for name, records in additions.items():
        if name not in artifacts or not isinstance(records, list):
            raise BundleBuildError("bundle source additions are invalid")
        artifacts[name]["items"].extend(records)
        touched.add(name)

    for name, records in replacements.items():
        if name not in artifacts or not isinstance(records, list):
            raise BundleBuildError("bundle source replacements are invalid")
        indexes = {
            _identity(item): index
            for index, item in enumerate(artifacts[name]["items"])
        }
        for record in records:
            if not isinstance(record, dict):
                raise BundleBuildError("bundle replacement record is invalid")
            identity = _identity(record)
            if identity not in indexes:
                raise BundleBuildError(
                    f"bundle replacement target does not exist: {identity}"
                )
            artifacts[name]["items"][indexes[identity]] = record
        touched.add(name)

    for name, artifact in artifacts.items():
        artifact["_generated"] = GENERATED_MARKER
        if name in touched:
            artifact["items"] = sorted(artifact["items"], key=_identity)


def build_bundle(
    version: str = "0.2.1",
    *,
    bundle_root: Path = BUNDLE_ROOT,
    source_path: Path | None = None,
    check: bool = False,
) -> BuildResult:
    if _VERSION_PATTERN.fullmatch(version) is None:
        raise BundleBuildError("bundle version must be a canonical semantic version")
    source_file = source_path or SOURCE_ROOT / f"{version}.json"
    source = _read_json(source_file)
    base_version = source.get("base_version")
    if (
        source.get("knowledge_content_version") != version
        or not isinstance(base_version, str)
        or _VERSION_PATTERN.fullmatch(base_version) is None
        or base_version == version
    ):
        raise BundleBuildError("bundle source version metadata is invalid")

    base_path = bundle_root / base_version
    base_manifest = _read_json(base_path / "manifest.json")
    artifacts = {
        name: _read_json(base_path / name)
        for name in REQUIRED
    }
    _apply_source_spec(artifacts, source)
    _update_metadata(artifacts)
    contract_version = base_manifest.get("contract_version")
    if not isinstance(contract_version, str) or not contract_version:
        raise BundleBuildError("base bundle contract version is invalid")
    _validate_artifacts(artifacts, contract_version)

    artifact_bytes = {
        name: canonical_json_bytes(artifacts[name]) for name in REQUIRED
    }
    manifest = _manifest(base_manifest, version, artifacts, artifact_bytes)
    manifest_bytes = canonical_json_bytes(manifest)
    output = {**artifact_bytes, "manifest.json": manifest_bytes}
    target = bundle_root / version

    with tempfile.TemporaryDirectory(prefix="hadocs-bundle-") as temporary:
        staging = Path(temporary) / version
        staging.mkdir()
        for name, raw in output.items():
            (staging / name).write_bytes(raw)
        try:
            validated, _compatibility, _trust = ContractValidator().validate(
                staging, strict=True
            )
            runtime = RuntimeBundle(
                checksum=str(validated.manifest["artifact_sha256"]),
                contract_version=str(validated.manifest["contract_version"]),
                manifest=freeze(validated.manifest),
                artifacts=freeze(validated.artifacts),
            )
            provider = KnowledgeProvider()
            provider.activate(runtime)
            provider.typed_matcher_contracts()
        except (BundleError, OSError, TypeError, ValueError) as error:
            raise BundleBuildError(f"generated bundle validation failed: {error}") from error

    changed = tuple(
        name
        for name, raw in sorted(output.items())
        if not (target / name).is_file() or (target / name).read_bytes() != raw
    )
    unexpected = (
        sorted(
            path.name
            for path in target.glob("*.json")
            if path.name not in output
        )
        if target.exists()
        else []
    )
    if unexpected:
        raise BundleBuildError(f"unexpected generated bundle file: {unexpected[0]}")
    if check and changed:
        raise BundleBuildError(
            "generated bundle is stale: " + ", ".join(changed)
        )
    if not check:
        target.mkdir(parents=True, exist_ok=True)
        for name in changed:
            destination = target / name
            with tempfile.NamedTemporaryFile(
                dir=target, prefix=f".{name}.", delete=False
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(output[name])
            temporary_path.replace(destination)

    return BuildResult(
        bundle_path=target,
        changed_files=changed,
        artifact_sha256=str(manifest["artifact_sha256"]),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and validate the packaged HADocs HASK consumer bundle."
    )
    parser.add_argument("--version", default="0.2.1")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        result = build_bundle(arguments.version, check=arguments.check)
    except BundleBuildError as error:
        parser.exit(1, f"bundle generation failed: {error}\n")
    action = "validated" if arguments.check else "generated"
    print(
        f"{action} {result.bundle_path} "
        f"({len(result.changed_files)} changed files, {result.artifact_sha256})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
