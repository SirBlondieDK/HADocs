from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import re
import struct
import unicodedata
from typing import TYPE_CHECKING, Protocol

from hadocs.collectors.native_integration_status import (
    OBSERVATION_KEY_PREFIX,
    PROBLEM_STATES,
    canonical_bytes as canonical_native_bytes,
    observation_key as native_observation_key,
    validate_domain_observation,
)
from hadocs.knowledge.hask_pilot.loader import BundleError
from hadocs.knowledge.hask_runtime import BundleManager, RuntimeConfig

if TYPE_CHECKING:
    from hadocs.hask_database import (
        OperationalSliceResult,
        ScanCompletionResult,
    )


_SCOPE_PATTERN = re.compile(r"is1_[0-9a-f]{64}")
_SUBJECT_PATTERN = re.compile(r"refh1_entity_[0-9a-f]{64}")
_OBSERVATION_DOMAIN = "hadocs-generic-metadata/observation-id/v1"
_PLATFORM_PREDICATE = "entity_uses_platform"


class CandidateClassification(StrEnum):
    SUPPORTED_CANDIDATE = "SUPPORTED_CANDIDATE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NO_MATCH = "NO_MATCH"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REJECTED_CONFLICT = "REJECTED_CONFLICT"


class CandidateBridgeState(StrEnum):
    READY = "READY"
    REJECTED = "REJECTED"


class MatcherReadinessState(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    NO_MATCH = "NO_MATCH"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REJECTED_CONFLICT = "REJECTED_CONFLICT"


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    classification: CandidateClassification
    hask_record_ref: str
    matcher_id: str
    matcher_version: str
    persisted_scan_ref: int
    protected_subject_ref: str
    supporting_observation_ids: tuple[int, ...]
    supporting_relationship_ids: tuple[int, ...]
    missing_evidence_categories: tuple[str, ...]
    rejection_code: str | None
    consumer_contract_version: str
    candidate_digest: str

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["classification"] = self.classification.value
        return value

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.as_dict(), ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class MatcherReadiness:
    state: MatcherReadinessState
    matcher_id: str
    matcher_version: str
    hask_record_ref: str
    platform_scope: tuple[str, ...]
    candidate_emitted: bool
    missing_evidence_categories: tuple[str, ...]
    rejection_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["state"] = self.state.value
        return value


@dataclass(frozen=True, slots=True)
class CandidateEvidenceBridgeResult:
    state: CandidateBridgeState
    candidates: tuple[CandidateEvidence, ...] = ()
    matcher_readiness: tuple[MatcherReadiness, ...] = ()
    rejection_code: str | None = None

    def canonical_bytes(self) -> bytes:
        value = {
            "candidates": [item.as_dict() for item in self.candidates],
            "matcher_readiness": [
                item.as_dict() for item in self.matcher_readiness
            ],
            "rejection_code": self.rejection_code,
            "state": self.state.value,
        }
        return json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")


class _DatabaseReader(Protocol):
    def read_operational_slice(self, result: object) -> object: ...
    def read_scan_completion(self, result: object) -> object: ...
    def list_entities_for_installation(
        self, installation_id: int
    ) -> tuple[Mapping[str, object], ...]: ...
    def list_relationships_for_installation(
        self, installation_id: int
    ) -> tuple[Mapping[str, object], ...]: ...


@dataclass(frozen=True, slots=True)
class _DomainStatusEvidence:
    observation_id: int
    domain: str
    entry_count: int
    state_counts: tuple[tuple[str, int], ...]
    problem_entry_count: int
    unknown_state_count: int


def _domain_status_evidence(
    observations: tuple[Mapping[str, object], ...],
    *,
    enabled: bool,
) -> tuple[dict[str, _DomainStatusEvidence], tuple[int, ...]]:
    by_domain: dict[str, _DomainStatusEvidence] = {}
    base_ids: list[int] = []
    for row in observations:
        key = row.get("observation_key")
        observation_id = row.get("id")
        if not isinstance(key, str) or not isinstance(observation_id, int):
            raise ValueError("persisted observation identity is invalid")
        if not key.startswith(OBSERVATION_KEY_PREFIX):
            base_ids.append(observation_id)
            continue
        if not enabled:
            continue
        payload_json = row.get("normalized_payload_json")
        if not isinstance(payload_json, str):
            raise ValueError("persisted native observation payload is invalid")
        try:
            decoded = json.loads(payload_json)
        except json.JSONDecodeError as error:
            raise ValueError("persisted native observation payload is invalid") from error
        payload = validate_domain_observation(decoded)
        domain = str(payload["domain"])
        if (
            key != native_observation_key(domain)
            or row.get("taxonomy_class") != "B"
            or row.get("authority_class") != "AUTHORITATIVE_FACT"
            or row.get("provenance_ref") is not None
            or row.get("observed_at") != payload["observed_at"]
            or row.get("privacy_class") != "LOCAL_ONLY"
            or row.get("retention_policy") != "RETAIN_UNTIL_SUPERSEDED"
            or payload_json.encode("utf-8") != canonical_native_bytes(payload)
            or row.get("immutable_digest")
            != hashlib.sha256(payload_json.encode("utf-8")).digest()
            or domain in by_domain
        ):
            raise ValueError("persisted native observation semantics conflict")
        state_counts = payload["state_counts"]
        assert isinstance(state_counts, dict)
        expected_problem_count = sum(
            int(count)
            for state, count in state_counts.items()
            if state in PROBLEM_STATES
        )
        problem_count = int(payload["problem_entry_count"])
        if problem_count != expected_problem_count:
            raise ValueError("persisted native problem evidence conflicts")
        by_domain[domain] = _DomainStatusEvidence(
            observation_id=observation_id,
            domain=domain,
            entry_count=int(payload["entry_count"]),
            state_counts=tuple(sorted(
                (str(state), int(count))
                for state, count in state_counts.items()
            )),
            problem_entry_count=problem_count,
            unknown_state_count=int(payload["unknown_state_count"]),
        )
    return by_domain, tuple(sorted(base_ids))


def _frame(value: str) -> bytes:
    encoded = unicodedata.normalize("NFC", value).encode("utf-8", errors="strict")
    return struct.pack(">I", len(encoded)) + encoded


def _loaded_component_reference(scope: str, platform: str) -> str:
    normalized = unicodedata.normalize("NFC", platform).encode("utf-8", errors="strict")
    allowed = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    escaped = "".join(
        chr(value) if value in allowed else f"%{value:02X}" for value in normalized
    )
    canonical_key = f"ck1:loaded_component:{escaped}"
    payload = (
        _frame(_OBSERVATION_DOMAIN)
        + _frame(scope)
        + _frame("rest.components")
        + _frame(canonical_key)
    )
    return f"obs1_{hashlib.sha256(payload).hexdigest()}"


def _missing_category(path: str) -> str:
    return f"NATIVE_{path.upper().replace('.', '_')}"


def _candidate(
    *,
    classification: CandidateClassification,
    hask_record_ref: str,
    matcher_id: str,
    matcher_version: str,
    persisted_scan_ref: int,
    protected_subject_ref: str,
    supporting_observation_ids: tuple[int, ...],
    supporting_relationship_ids: tuple[int, ...],
    missing_evidence_categories: tuple[str, ...],
    rejection_code: str | None,
    consumer_contract_version: str,
) -> CandidateEvidence:
    intent = {
        "classification": classification.value,
        "consumer_contract_version": consumer_contract_version,
        "hask_record_ref": hask_record_ref,
        "matcher_id": matcher_id,
        "matcher_version": matcher_version,
        "missing_evidence_categories": list(missing_evidence_categories),
        "persisted_scan_ref": persisted_scan_ref,
        "protected_subject_ref": protected_subject_ref,
        "rejection_code": rejection_code,
        "supporting_observation_ids": list(supporting_observation_ids),
        "supporting_relationship_ids": list(supporting_relationship_ids),
    }
    digest = hashlib.sha256(json.dumps(
        intent, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return CandidateEvidence(
        classification=classification,
        hask_record_ref=hask_record_ref,
        matcher_id=matcher_id,
        matcher_version=matcher_version,
        persisted_scan_ref=persisted_scan_ref,
        protected_subject_ref=protected_subject_ref,
        supporting_observation_ids=supporting_observation_ids,
        supporting_relationship_ids=supporting_relationship_ids,
        missing_evidence_categories=missing_evidence_categories,
        rejection_code=rejection_code,
        consumer_contract_version=consumer_contract_version,
        candidate_digest=f"hce1_{digest}",
    )


def _rejected(code: str) -> CandidateEvidenceBridgeResult:
    return CandidateEvidenceBridgeResult(
        state=CandidateBridgeState.REJECTED,
        rejection_code=code,
    )


def _matcher_readiness(
    matchers: tuple[object, ...],
    candidates: tuple[CandidateEvidence, ...],
) -> tuple[MatcherReadiness, ...]:
    readiness: list[MatcherReadiness] = []
    for matcher in matchers:
        matching = tuple(
            item
            for item in candidates
            if item.matcher_id == matcher.matcher_id
            and item.matcher_version == matcher.version
            and item.hask_record_ref == matcher.evidence_target
        )
        classifications = {item.classification for item in matching}
        if CandidateClassification.SUPPORTED_CANDIDATE in classifications:
            state = MatcherReadinessState.READY
        elif CandidateClassification.REJECTED_CONFLICT in classifications:
            state = MatcherReadinessState.REJECTED_CONFLICT
        elif CandidateClassification.INSUFFICIENT_EVIDENCE in classifications:
            state = MatcherReadinessState.BLOCKED
        elif CandidateClassification.NO_MATCH in classifications:
            state = MatcherReadinessState.NO_MATCH
        else:
            state = MatcherReadinessState.NOT_APPLICABLE

        readiness.append(
            MatcherReadiness(
                state=state,
                matcher_id=matcher.matcher_id,
                matcher_version=matcher.version,
                hask_record_ref=matcher.evidence_target,
                platform_scope=tuple(sorted(matcher.platform_scope)),
                candidate_emitted=(
                    CandidateClassification.SUPPORTED_CANDIDATE
                    in classifications
                ),
                missing_evidence_categories=tuple(sorted({
                    category
                    for item in matching
                    for category in item.missing_evidence_categories
                })),
                rejection_codes=tuple(sorted({
                    item.rejection_code
                    for item in matching
                    if item.rejection_code
                })),
            )
        )

    return tuple(sorted(
        readiness,
        key=lambda item: (
            item.matcher_id,
            item.matcher_version,
            item.hask_record_ref,
        ),
    ))


def build_candidate_evidence_bridge(
    *,
    service: _DatabaseReader,
    operational_slice: OperationalSliceResult,
    completion: ScanCompletionResult,
    config: Mapping[str, object],
) -> CandidateEvidenceBridgeResult:
    bundle_value = config.get("hask_bundle_path")
    if bundle_value is None:
        bundle_path = None
    elif isinstance(bundle_value, (str, Path)):
        normalized_bundle_path = str(bundle_value).strip()
        bundle_path = Path(normalized_bundle_path) if normalized_bundle_path else None
    else:
        return _rejected("HASK_CONFIGURATION_INVALID")
    strict = config.get("hask_strict_validation", True)
    cache_enabled = config.get("hask_cache_enabled", True)
    native_enabled = config.get("hask_native_integration_status_enabled", False)
    if (
        not isinstance(strict, bool)
        or not isinstance(cache_enabled, bool)
        or not isinstance(native_enabled, bool)
    ):
        return _rejected("HASK_CONFIGURATION_INVALID")

    manager = BundleManager(RuntimeConfig(
        enabled=True,
        bundle_path=bundle_path,
        strict_validation=strict,
        cache_enabled=cache_enabled,
    ))
    diagnostics = manager.startup()
    if not diagnostics.active or manager.provider.bundle is None:
        manager.shutdown()
        return _rejected("BUNDLE_VALIDATION_FAILED")
    try:
        try:
            matchers = manager.typed_matcher_contracts()
        except BundleError:
            return _rejected("CONSUMER_CONTRACT_INVALID")
        if not matchers:
            return _rejected("NO_TYPED_MATCHER_CONTRACT")
        consumer_contract_version = manager.provider.bundle.contract_version

        slice_records = service.read_operational_slice(operational_slice)
        completion_records = service.read_scan_completion(completion)
        installation_id = int(operational_slice.installation_id)
        scan_run_id = int(operational_slice.scan_run_id)
        context = slice_records.context
        scope = context.get("installation_scope")
        if (
            not isinstance(scope, str)
            or not _SCOPE_PATTERN.fullmatch(scope)
            or completion.scan_run_id != scan_run_id
            or completion_records.scan_run.get("id") != scan_run_id
        ):
            return _rejected("PERSISTED_EVIDENCE_CONFLICT")

        entities = service.list_entities_for_installation(installation_id)
        relationships = service.list_relationships_for_installation(installation_id)
        try:
            native_statuses, base_observation_ids = _domain_status_evidence(
                completion_records.observations,
                enabled=native_enabled,
            )
        except (TypeError, ValueError):
            return _rejected("PERSISTED_EVIDENCE_CONFLICT")
        by_subject: dict[str, list[Mapping[str, object]]] = {}
        entity_by_subject: dict[str, Mapping[str, object]] = {}
        for entity in entities:
            subject = entity.get("opaque_reference")
            if isinstance(subject, str) and _SUBJECT_PATTERN.fullmatch(subject):
                entity_by_subject[subject] = entity
                by_subject.setdefault(subject, [])
        orphaned_subjects: set[str] = set()
        for relationship in relationships:
            if (
                relationship.get("predicate") != _PLATFORM_PREDICATE
                or relationship.get("current_status") != "CURRENT"
            ):
                continue
            subject = relationship.get("source_ref")
            if not isinstance(subject, str) or subject not in entity_by_subject:
                if isinstance(subject, str) and _SUBJECT_PATTERN.fullmatch(subject):
                    orphaned_subjects.add(subject)
                continue
            by_subject[subject].append(relationship)

        candidates: list[CandidateEvidence] = []
        for matcher in matchers:
            target_platform = {
                _loaded_component_reference(scope, platform): platform
                for platform in matcher.platform_scope
            }
            expected_targets = set(target_platform)
            missing = tuple(sorted(
                _missing_category(path) for path, _ in matcher.required_fields
            ))
            for subject in sorted(entity_by_subject):
                entity = entity_by_subject[subject]
                platform_rows = sorted(
                    by_subject[subject], key=lambda item: (str(item["target_ref"]), int(item["id"]))
                )
                matching_rows = tuple(
                    item for item in platform_rows
                    if item.get("target_ref") in expected_targets
                )
                relationship_ids = tuple(sorted(
                    int(item["id"]) for item in (matching_rows or tuple(platform_rows))
                ))
                distinct_targets = {item.get("target_ref") for item in platform_rows}
                entity_conflict = (
                    entity.get("identity_status") != "ACTIVE"
                    or any(int(item["source_entity_id"]) != int(entity["id"]) for item in platform_rows)
                    or len(distinct_targets) > 1
                )
                candidate_observation_ids = base_observation_ids
                if entity_conflict:
                    classification = CandidateClassification.REJECTED_CONFLICT
                    rejection_code = "CONTRADICTORY_CURRENT_PLATFORM_EVIDENCE"
                    candidate_missing: tuple[str, ...] = ()
                elif matching_rows:
                    classification = CandidateClassification.INSUFFICIENT_EVIDENCE
                    rejection_code = None
                    candidate_missing = missing
                    matched_domain = target_platform[str(matching_rows[0]["target_ref"])]
                    native_status = native_statuses.get(matched_domain)
                    if native_status is not None:
                        candidate_observation_ids = tuple(sorted(
                            (*base_observation_ids, native_status.observation_id)
                        ))
                        if native_status.unknown_state_count > 0:
                            pass
                        elif len(native_status.state_counts) != 1:
                            classification = CandidateClassification.REJECTED_CONFLICT
                            rejection_code = "CONTRADICTORY_DOMAIN_STATUS_EVIDENCE"
                            candidate_missing = ()
                        else:
                            candidate_missing = tuple(
                                item for item in missing
                                if item != "NATIVE_PROBLEM_SIGNAL"
                            )
                            if not candidate_missing:
                                if (
                                    native_status.problem_entry_count
                                    == native_status.entry_count
                                ):
                                    classification = (
                                        CandidateClassification.SUPPORTED_CANDIDATE
                                    )
                                elif native_status.problem_entry_count == 0:
                                    classification = CandidateClassification.NO_MATCH
                                else:
                                    classification = (
                                        CandidateClassification.REJECTED_CONFLICT
                                    )
                                    rejection_code = (
                                        "CONTRADICTORY_DOMAIN_STATUS_EVIDENCE"
                                    )
                else:
                    classification = CandidateClassification.NOT_APPLICABLE
                    rejection_code = None
                    candidate_missing = ()
                candidates.append(_candidate(
                    classification=classification,
                    hask_record_ref=matcher.evidence_target,
                    matcher_id=matcher.matcher_id,
                    matcher_version=matcher.version,
                    persisted_scan_ref=scan_run_id,
                    protected_subject_ref=subject,
                    supporting_observation_ids=candidate_observation_ids,
                    supporting_relationship_ids=relationship_ids,
                    missing_evidence_categories=candidate_missing,
                    rejection_code=rejection_code,
                    consumer_contract_version=consumer_contract_version,
                ))
        if orphaned_subjects:
            return _rejected("PERSISTED_EVIDENCE_CONFLICT")
        preliminary = sorted(
            candidates,
            key=lambda item: (
                item.matcher_id,
                item.protected_subject_ref,
                item.hask_record_ref,
                item.candidate_digest,
            ),
        )
        deduplicated: list[CandidateEvidence] = []
        supported_matchers: set[tuple[str, str, str]] = set()
        for item in preliminary:
            supported_key = (
                item.matcher_id,
                item.matcher_version,
                item.hask_record_ref,
            )
            if item.classification is CandidateClassification.SUPPORTED_CANDIDATE:
                if supported_key in supported_matchers:
                    continue
                supported_matchers.add(supported_key)
            deduplicated.append(item)
        ordered = tuple(deduplicated)
        return CandidateEvidenceBridgeResult(
            state=CandidateBridgeState.READY,
            candidates=ordered,
            matcher_readiness=_matcher_readiness(matchers, ordered),
        )
    finally:
        manager.shutdown()
