from __future__ import annotations

from pathlib import Path
from typing import Protocol

from hadocs.knowledge.hask_pilot.loader import BundleError, HaskBundle, load_bundle, negotiate_version
from hadocs.version import RELEASE_VERSION


class TrustVerifier(Protocol):
    def verify(self, bundle_path: Path, manifest: dict) -> str: ...


class UnsignedChecksumTrust:
    """PI1 trust policy: validated manifest checksums, no publisher signature."""

    def verify(self, bundle_path: Path, manifest: dict) -> str:
        return "checksum_valid_signature_not_implemented"


class VersionNegotiator:
    HADOCS_VERSION = RELEASE_VERSION

    def negotiate(self, producer_version: str) -> str:
        return negotiate_version(producer_version)

    def validate_hadocs_version(self, minimum: str | None) -> str:
        if minimum is None:
            return "hadocs_version_unspecified"
        try:
            current = tuple(map(int, self.HADOCS_VERSION.split(".")))
            required = tuple(map(int, minimum.split(".")))
        except (AttributeError, ValueError) as exc:
            raise BundleError("schema_failed", "invalid HADocs version metadata") from exc
        if required > current:
            raise BundleError("unsupported_hadocs_version", f"bundle requires HADocs {minimum}")
        return "hadocs_version_supported"


class ContractValidator:
    CONTRACT_NAME = "hask-hadocs"
    REQUIRED_MANIFEST_FIELDS = {
        "contract_name", "contract_version", "knowledge_content_version", "knowledge_schema_version",
        "authoritative_sha256", "schema_registry_sha256", "artifact_sha256", "artifacts",
    }

    def __init__(self, negotiator: VersionNegotiator | None = None, trust: TrustVerifier | None = None) -> None:
        self.negotiator = negotiator or VersionNegotiator()
        self.trust = trust or UnsignedChecksumTrust()

    def validate(self, path: Path, *, strict: bool = True) -> tuple[HaskBundle, str, str]:
        bundle = load_bundle(path, strict=strict)
        missing = self.REQUIRED_MANIFEST_FIELDS - set(bundle.manifest)
        if missing:
            raise BundleError("schema_failed", f"manifest fields missing: {sorted(missing)}")
        if bundle.manifest.get("contract_name") != self.CONTRACT_NAME:
            raise BundleError("schema_failed", "unexpected consumer contract name")
        identifiers: list[str] = []
        readiness_platforms: list[str] = []
        for name, artifact in bundle.artifacts.items():
            for item in artifact["items"]:
                if not isinstance(item, dict):
                    raise BundleError("schema_failed", "artifact item identity is invalid")
                identity = item.get("id")
                if isinstance(identity, str) and identity:
                    identifiers.append(identity)
                elif name == "readiness.json" and isinstance(
                    item.get("platform"), str
                ) and item["platform"]:
                    readiness_platforms.append(item["platform"])
                else:
                    raise BundleError("schema_failed", "artifact item identity is invalid")
        if len(identifiers) != len(set(identifiers)):
            raise BundleError("schema_failed", "duplicate artifact identity")
        if len(readiness_platforms) != len(set(readiness_platforms)):
            raise BundleError("schema_failed", "duplicate readiness platform identity")
        compatibility = self.negotiator.negotiate(bundle.manifest["contract_version"])
        if compatibility == "incompatible_major_version":
            raise BundleError(compatibility, "unsupported contract major version")
        self.negotiator.validate_hadocs_version(bundle.manifest.get("minimum_hadocs_version"))
        trust = self.trust.verify(path, bundle.manifest)
        return bundle, compatibility, trust
