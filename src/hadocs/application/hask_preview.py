from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
import html
import json
from pathlib import Path
from typing import Any


PREVIEW_NOTICE = (
    "Experimental preview — HASK results are candidate-only and do not affect "
    "findings, recommendations, Root Causes or Health Score."
)
ANALYTICAL_IMPACT = (
    "HASK Preview is read-only and candidate-only. It does not change findings, "
    "incidents, Root Causes, recommendations, severity, Health Score, Potential "
    "Health Score, estimated score gain, device status, or analytical ordering."
)


class PreviewClassification(StrEnum):
    SUPPORTED_CANDIDATE = "SUPPORTED_CANDIDATE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REJECTED_CONFLICT = "REJECTED_CONFLICT"
    BUNDLE_DISABLED = "BUNDLE_DISABLED"
    BUNDLE_UNAVAILABLE = "BUNDLE_UNAVAILABLE"
    BUNDLE_INVALID = "BUNDLE_INVALID"


@dataclass(frozen=True, slots=True)
class PreviewCoverage:
    artifact: str
    item_count: int


@dataclass(frozen=True, slots=True)
class PreviewKnowledge:
    platform_id: str
    title: str
    summary: str
    status: str


@dataclass(frozen=True, slots=True)
class PreviewCandidate:
    classification: PreviewClassification
    hask_record_ref: str
    matcher_id: str
    matcher_version: str
    supporting_evidence_categories: tuple[str, ...]
    missing_evidence_categories: tuple[str, ...]
    rejection_code: str | None
    applicability: str
    explanation: str


@dataclass(frozen=True, slots=True)
class PreviewMatcherReadiness:
    state: str
    matcher_id: str
    matcher_version: str
    hask_record_ref: str
    platform_scope: tuple[str, ...]
    candidate_emitted: bool
    missing_evidence_categories: tuple[str, ...]
    rejection_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HaskPreviewSnapshot:
    feature_enabled: bool
    hask_runtime_enabled: bool
    bundle_available: bool
    bundle_valid: bool
    bundle_source: str
    classification: PreviewClassification
    validation_state: str
    compatibility_state: str
    contract_version: str | None
    knowledge_content_version: str | None
    knowledge_schema_version: str | None
    checksum_prefix: str | None
    coverage: tuple[PreviewCoverage, ...]
    relevant_knowledge: tuple[PreviewKnowledge, ...]
    candidates: tuple[PreviewCandidate, ...]
    matcher_readiness: tuple[PreviewMatcherReadiness, ...]
    candidate_bridge_state: str
    candidate_bridge_rejection_code: str | None
    limitations: tuple[str, ...]
    notice: str = PREVIEW_NOTICE
    analytical_impact_statement: str = ANALYTICAL_IMPACT

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["classification"] = self.classification.value
        for candidate in value["candidates"]:
            candidate["classification"] = candidate["classification"].value
        return value

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.as_dict(), ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")


def _boolean(config: Mapping[str, object], key: str) -> bool:
    value = config.get(key, False)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean value")
    return value


def _empty_snapshot(
    *,
    preview_enabled: bool,
    runtime_enabled: bool,
    available: bool,
    source: str,
    classification: PreviewClassification,
    validation: str,
    limitation: str,
) -> HaskPreviewSnapshot:
    return HaskPreviewSnapshot(
        feature_enabled=preview_enabled,
        hask_runtime_enabled=runtime_enabled,
        bundle_available=available,
        bundle_valid=False,
        bundle_source=source,
        classification=classification,
        validation_state=validation,
        compatibility_state="not_checked",
        contract_version=None,
        knowledge_content_version=None,
        knowledge_schema_version=None,
        checksum_prefix=None,
        coverage=(),
        relevant_knowledge=(),
        candidates=(),
        matcher_readiness=(),
        candidate_bridge_state="NOT_AVAILABLE",
        candidate_bridge_rejection_code=None,
        limitations=(limitation,),
    )


def _candidate_explanation(classification: PreviewClassification) -> str:
    return {
        PreviewClassification.SUPPORTED_CANDIDATE: (
            "Validated local evidence supports an experimental HASK candidate; "
            "HADocs has not confirmed a Root Cause."
        ),
        PreviewClassification.INSUFFICIENT_EVIDENCE: (
            "Relevant HASK knowledge exists, but required authoritative local "
            "evidence is missing."
        ),
        PreviewClassification.NOT_APPLICABLE: (
            "The validated knowledge does not apply to the observed platform context."
        ),
        PreviewClassification.REJECTED_CONFLICT: (
            "Conflicting evidence rejected the candidate without changing HADocs analysis."
        ),
    }[classification]


def _safe_candidates(result: object | None) -> tuple[PreviewCandidate, ...]:
    if result is None:
        return ()
    safe: list[PreviewCandidate] = []
    for item in getattr(result, "candidates", ()):
        try:
            classification = PreviewClassification(str(item.classification.value))
        except (AttributeError, ValueError):
            continue
        if classification is not PreviewClassification.SUPPORTED_CANDIDATE:
            continue
        categories: list[str] = []
        if getattr(item, "supporting_observation_ids", ()):
            categories.append("validated observation")
        if getattr(item, "supporting_relationship_ids", ()):
            categories.append("validated relationship")
        safe.append(
            PreviewCandidate(
                classification=classification,
                hask_record_ref=str(getattr(item, "hask_record_ref", "")),
                matcher_id=str(getattr(item, "matcher_id", "")),
                matcher_version=str(getattr(item, "matcher_version", "")),
                supporting_evidence_categories=tuple(categories),
                missing_evidence_categories=tuple(
                    sorted(str(value) for value in getattr(item, "missing_evidence_categories", ()))
                ),
                rejection_code=(
                    str(item.rejection_code) if getattr(item, "rejection_code", None) else None
                ),
                applicability=(
                    "applicable"
                    if classification is PreviewClassification.SUPPORTED_CANDIDATE
                    else "not confirmed"
                ),
                explanation=_candidate_explanation(classification),
            )
        )
    ordered = sorted(
        safe,
        key=lambda item: (
            item.classification.value,
            item.matcher_id,
            item.matcher_version,
            item.hask_record_ref,
            item.missing_evidence_categories,
            item.rejection_code or "",
        ),
    )
    return tuple(dict.fromkeys(ordered))


def _safe_matcher_readiness(
    result: object | None,
) -> tuple[PreviewMatcherReadiness, ...]:
    if result is None:
        return ()

    allowed_states = {
        "READY",
        "BLOCKED",
        "NOT_APPLICABLE",
        "REJECTED_CONFLICT",
    }
    safe: list[PreviewMatcherReadiness] = []
    for item in getattr(result, "matcher_readiness", ()):
        raw_state = getattr(item, "state", None)
        state_value = getattr(raw_state, "value", raw_state)
        state = str(state_value) if state_value is not None else ""
        if state not in allowed_states:
            continue

        safe.append(
            PreviewMatcherReadiness(
                state=state,
                matcher_id=str(getattr(item, "matcher_id", "")),
                matcher_version=str(getattr(item, "matcher_version", "")),
                hask_record_ref=str(getattr(item, "hask_record_ref", "")),
                platform_scope=tuple(sorted(
                    str(value)
                    for value in getattr(item, "platform_scope", ())
                    if str(value)
                )),
                candidate_emitted=(
                    getattr(item, "candidate_emitted", False) is True
                ),
                missing_evidence_categories=tuple(sorted(
                    str(value)
                    for value in getattr(
                        item, "missing_evidence_categories", ()
                    )
                    if str(value)
                )),
                rejection_codes=tuple(sorted(
                    str(value)
                    for value in getattr(item, "rejection_codes", ())
                    if str(value)
                )),
            )
        )

    return tuple(sorted(
        safe,
        key=lambda item: (
            item.matcher_id,
            item.matcher_version,
            item.hask_record_ref,
        ),
    ))


def _bridge_status(result: object | None) -> tuple[str, str | None]:
    if result is None:
        return "NOT_AVAILABLE", None

    raw_state = getattr(result, "state", None)
    state_value = getattr(raw_state, "value", raw_state)
    state = str(state_value) if state_value is not None else "UNKNOWN"
    if state not in {"READY", "REJECTED"}:
        state = "UNKNOWN"

    raw_rejection = getattr(result, "rejection_code", None)
    rejection = str(raw_rejection) if raw_rejection else None
    return state, rejection


def _preview_classification(
    candidates: tuple[PreviewCandidate, ...],
    readiness: tuple[PreviewMatcherReadiness, ...],
) -> PreviewClassification:
    if candidates:
        return PreviewClassification.SUPPORTED_CANDIDATE

    states = {item.state for item in readiness}
    if "REJECTED_CONFLICT" in states:
        return PreviewClassification.REJECTED_CONFLICT
    if "BLOCKED" in states:
        return PreviewClassification.INSUFFICIENT_EVIDENCE
    if states and states == {"NOT_APPLICABLE"}:
        return PreviewClassification.NOT_APPLICABLE
    return PreviewClassification.INSUFFICIENT_EVIDENCE


class HaskPreviewService:
    """Build one immutable, redacted model for every Preview surface."""

    def __init__(self, *, discovery: object | None = None, validator: object | None = None) -> None:
        self._discovery = discovery
        self._validator = validator

    def snapshot(
        self,
        config: Mapping[str, object],
        *,
        candidate_result: object | None = None,
        relevant_platforms: Iterable[str] = (),
    ) -> HaskPreviewSnapshot:
        preview_enabled = _boolean(config, "hask_preview_enabled")
        runtime_enabled = _boolean(config, "hask_enabled")
        raw_path = config.get("hask_bundle_path")
        explicit = None
        if isinstance(raw_path, (str, Path)) and str(raw_path).strip():
            explicit = Path(raw_path)

        from hadocs.knowledge.hask_runtime.discovery import BundleDiscovery

        discovery = self._discovery or BundleDiscovery()
        found = discovery.discover(explicit)
        available = found.path is not None

        if not preview_enabled or not runtime_enabled:
            return _empty_snapshot(
                preview_enabled=preview_enabled,
                runtime_enabled=runtime_enabled,
                available=available,
                source=found.source,
                classification=PreviewClassification.BUNDLE_DISABLED,
                validation="not_loaded",
                limitation=(
                    "Enable both HASK Preview and the HASK runtime to validate and view "
                    "candidate knowledge. All controls are disabled by default."
                ),
            )
        if not available:
            return _empty_snapshot(
                preview_enabled=True,
                runtime_enabled=True,
                available=False,
                source=found.source,
                classification=PreviewClassification.BUNDLE_UNAVAILABLE,
                validation="missing",
                limitation=(
                    "The explicitly configured bundle is unavailable. HADocs did not "
                    "silently fall back to another bundle."
                    if explicit is not None
                    else "No validated packaged or configured HASK bundle is available."
                ),
            )

        from hadocs.knowledge.hask_pilot.loader import BundleError
        from hadocs.knowledge.hask_runtime.validation import ContractValidator

        validator = self._validator or ContractValidator()
        try:
            bundle, compatibility, _trust = validator.validate(found.path, strict=True)
        except (BundleError, OSError, TypeError, ValueError):
            return _empty_snapshot(
                preview_enabled=True,
                runtime_enabled=True,
                available=True,
                source=found.source,
                classification=PreviewClassification.BUNDLE_INVALID,
                validation="invalid",
                limitation=(
                    "Bundle validation failed closed. No HASK candidate evaluation was used."
                ),
            )

        coverage = tuple(
            PreviewCoverage(name.removesuffix(".json"), len(artifact["items"]))
            for name, artifact in sorted(bundle.artifacts.items())
        )
        requested = {str(value).strip().casefold() for value in relevant_platforms if str(value).strip()}
        knowledge: list[PreviewKnowledge] = []
        for item in bundle.items("platform_index.json"):
            platform_id = str(item.get("id", ""))
            if requested and platform_id.casefold() not in requested:
                continue
            if not requested:
                continue
            knowledge.append(
                PreviewKnowledge(
                    platform_id=platform_id,
                    title=str(item.get("title", platform_id)),
                    summary=str(item.get("summary", "")),
                    status=str(item.get("status", "unknown")),
                )
            )
        candidates = _safe_candidates(candidate_result)
        matcher_readiness = _safe_matcher_readiness(candidate_result)
        bridge_state, bridge_rejection = _bridge_status(candidate_result)
        state = _preview_classification(candidates, matcher_readiness)
        manifest = bundle.manifest
        checksum = str(manifest.get("artifact_sha256", ""))
        return HaskPreviewSnapshot(
            feature_enabled=True,
            hask_runtime_enabled=True,
            bundle_available=True,
            bundle_valid=True,
            bundle_source=found.source,
            classification=state,
            validation_state="valid",
            compatibility_state=compatibility,
            contract_version=str(manifest.get("contract_version")),
            knowledge_content_version=str(manifest.get("knowledge_content_version")),
            knowledge_schema_version=str(manifest.get("knowledge_schema_version")),
            checksum_prefix=checksum[:12] if checksum else None,
            coverage=coverage,
            relevant_knowledge=tuple(sorted(knowledge, key=lambda item: item.platform_id)),
            candidates=candidates,
            matcher_readiness=matcher_readiness,
            candidate_bridge_state=bridge_state,
            candidate_bridge_rejection_code=bridge_rejection,
            limitations=(
                "Only bounded typed matchers are executable; bundle record counts are not matcher counts.",
                "UniFi and MikroTik diagnoses require authoritative controller/API results when those platforms are applicable.",
                "Authenticated probes and network logins are not performed.",
            ),
        )


def render_hask_preview_html(snapshot: HaskPreviewSnapshot) -> str:
    """Render the shared snapshot without adding any analytical semantics."""

    esc = lambda value: html.escape(str(value))
    coverage = "".join(
        f"<li><strong>{esc(item.artifact)}</strong>: {item.item_count}</li>"
        for item in snapshot.coverage
    ) or "<li>No validated coverage is available.</li>"
    knowledge = "".join(
        f"<li><strong>{esc(item.title)}</strong> — {esc(item.summary)}</li>"
        for item in snapshot.relevant_knowledge
    ) or "<li>No relevant platform knowledge has been evaluated.</li>"
    candidates = "".join(
        "<article class='hask-candidate'>"
        f"<h3>{esc(item.classification.value)}</h3>"
        f"<p>{esc(item.explanation)}</p>"
        f"<p><strong>HASK record:</strong> {esc(item.hask_record_ref)} · "
        f"<strong>Matcher:</strong> {esc(item.matcher_id)} {esc(item.matcher_version)}</p>"
        f"<p><strong>Supporting evidence:</strong> {esc(', '.join(item.supporting_evidence_categories) or 'none')}</p>"
        f"<p><strong>Missing evidence:</strong> {esc(', '.join(item.missing_evidence_categories) or 'none')}</p>"
        "</article>"
        for item in snapshot.candidates
    ) or "<p>No candidate evidence has been evaluated.</p>"
    limitations = "".join(f"<li>{esc(value)}</li>" for value in snapshot.limitations)
    return f"""
    <section class="section panel hask-preview" id="hask-preview">
      <div class="section-head"><h2>HASK Preview</h2><p><strong>Experimental · default disabled</strong></p></div>
      <p class="hask-notice">{esc(snapshot.notice)}</p>
      <h3>HASK status</h3><p>{esc(snapshot.classification.value)} · validation {esc(snapshot.validation_state)} · source {esc(snapshot.bundle_source)}</p>
      <h3>Bundle information</h3><p>Contract {esc(snapshot.contract_version or 'not loaded')} · knowledge {esc(snapshot.knowledge_content_version or 'not loaded')} · checksum {esc(snapshot.checksum_prefix or 'not checked')}</p>
      <h3>Knowledge coverage</h3><ul>{coverage}</ul>
      <h3>Relevant knowledge for this installation</h3><ul>{knowledge}</ul>
      <h3>Candidate insights</h3>{candidates}
      <h3>Conflicts and limitations</h3><ul>{limitations}</ul>
      <h3>Analytical impact</h3><p>{esc(snapshot.analytical_impact_statement)}</p>
      <h3>Enablement</h3><p>Enable HASK Preview and the HASK runtime explicitly. Candidate evaluation additionally retains the operational database, candidate-evidence, and native-status gates.</p>
    </section>
    """
