from __future__ import annotations

import re
from typing import Mapping, Protocol, Sequence

from .errors import IdempotencyConflictError, ValidationFailureError


TERMINAL_SCAN_STATES = frozenset({"SUCCEEDED", "FAILED", "INTERRUPTED", "CANCELLED"})
CAPABILITY_STATES = frozenset({"SUCCEEDED", "FAILED", "UNAVAILABLE", "UNSUPPORTED"})
SCAN_AUDIT_SUBJECT_ROLE = "TERMINAL_RESULT"
SCAN_AUDIT_EVIDENCE_ROLE = "COMPLETION_EVIDENCE"
ENTITY_KEY_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,128}")
ENTITY_PRESENT_REASON = "ENTITY_PRESENT_VALID"
ENTITY_REMOVAL_REASON = "AUTHORITATIVE_REMOVAL"
ENTITY_RECREATION_REASON = "AUTHORITATIVE_RECREATION"
RELATIONSHIP_PRESENT_REASON = "RELATIONSHIP_PRESENT_VALID"
RELATIONSHIP_REMOVAL_REASON = "AUTHORITATIVE_RELATIONSHIP_REMOVAL"
RELATIONSHIP_RECREATION_REASON = "AUTHORITATIVE_RELATIONSHIP_RECREATION"
RELATIONSHIP_TARGET_KINDS = {
    "entity_uses_platform": "integration",
    "entity_assigned_to_device": "device",
    "entity_assigned_to_area": "area",
    "entity_has_label": "label",
}


class CapabilityIntent(Protocol):
    capability_id: str
    status: str
    retryable: bool | None
    safe_error_code: str | None
    observation_contribution: bool
    completeness_contribution: str


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationFailureError(f"{name} must be non-empty text")


def validate_entity_intent(
    *,
    entity_key: str,
    raw_entity_id: str,
    lifecycle_state: str,
    reason_code: str,
) -> None:
    if not isinstance(entity_key, str) or not ENTITY_KEY_PATTERN.fullmatch(entity_key):
        raise ValidationFailureError("entity intent key is invalid")
    if not isinstance(raw_entity_id, str) or not raw_entity_id:
        raise ValidationFailureError("authoritative entity identity is invalid")
    if any(ord(character) < 32 or ord(character) == 127 for character in raw_entity_id):
        raise ValidationFailureError("authoritative entity identity is invalid")
    if lifecycle_state not in {"ACTIVE", "REMOVED"}:
        raise ValidationFailureError("entity lifecycle intent is not supported in this batch")
    expected_reason = {
        "ACTIVE": {ENTITY_PRESENT_REASON, ENTITY_RECREATION_REASON},
        "REMOVED": {ENTITY_REMOVAL_REASON},
    }[lifecycle_state]
    if reason_code not in expected_reason:
        raise ValidationFailureError("entity lifecycle evidence is inconsistent")


def validate_entity_transition(
    *, prior_state: str | None, result_state: str, reason_code: str
) -> bool:
    """Return whether an event is required for the supported frozen transition."""

    if prior_state is None:
        if result_state != "ACTIVE" or reason_code != ENTITY_PRESENT_REASON:
            raise ValidationFailureError("a new entity requires valid present identity evidence")
        return True
    if prior_state == result_state:
        expected = (
            ENTITY_PRESENT_REASON if result_state == "ACTIVE" else ENTITY_REMOVAL_REASON
        )
        if reason_code != expected:
            raise ValidationFailureError("unchanged entity evidence is inconsistent")
        return False
    if (
        prior_state == "ACTIVE"
        and result_state == "REMOVED"
        and reason_code == ENTITY_REMOVAL_REASON
    ):
        return True
    if (
        prior_state == "REMOVED"
        and result_state == "ACTIVE"
        and reason_code == ENTITY_RECREATION_REASON
    ):
        return True
    raise ValidationFailureError("entity lifecycle transition is not supported in this batch")


def validate_relationship_intent(
    *,
    relationship_key: str,
    raw_source_entity_id: str,
    predicate: str,
    target_kind: str,
    raw_target_id: str,
    current_status: str,
    reason_code: str,
) -> None:
    if not isinstance(relationship_key, str) or not ENTITY_KEY_PATTERN.fullmatch(
        relationship_key
    ):
        raise ValidationFailureError("relationship intent key is invalid")
    for value in (raw_source_entity_id, raw_target_id):
        if (
            not isinstance(value, str)
            or not value
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise ValidationFailureError("relationship endpoint identity input is invalid")
    expected_target_kind = RELATIONSHIP_TARGET_KINDS.get(predicate)
    if expected_target_kind is None:
        raise ValidationFailureError("relationship predicate is not frozen")
    if target_kind != expected_target_kind:
        raise ValidationFailureError("relationship target kind conflicts with its predicate")
    if current_status not in {"CURRENT", "CURRENT_ABSENT"}:
        raise ValidationFailureError("relationship current intent is not supported")
    expected_reasons = {
        "CURRENT": {RELATIONSHIP_PRESENT_REASON, RELATIONSHIP_RECREATION_REASON},
        "CURRENT_ABSENT": {RELATIONSHIP_REMOVAL_REASON},
    }[current_status]
    if reason_code not in expected_reasons:
        raise ValidationFailureError("relationship lifecycle evidence is inconsistent")


def validate_relationship_transition(
    *,
    prior_status: str | None,
    result_status: str,
    reason_code: str,
) -> str | None:
    """Return the frozen event kind, or None for an equivalent current state."""

    if prior_status is None:
        if result_status != "CURRENT" or reason_code != RELATIONSHIP_PRESENT_REASON:
            raise ValidationFailureError(
                "a new relationship requires explicit valid tuple evidence"
            )
        return "CREATED"
    if prior_status == result_status:
        expected = (
            RELATIONSHIP_PRESENT_REASON
            if result_status == "CURRENT"
            else RELATIONSHIP_REMOVAL_REASON
        )
        if reason_code != expected:
            raise ValidationFailureError(
                "unchanged relationship evidence is inconsistent"
            )
        return None
    if (
        prior_status == "CURRENT"
        and result_status == "CURRENT_ABSENT"
        and reason_code == RELATIONSHIP_REMOVAL_REASON
    ):
        return "REMOVED"
    if (
        prior_status == "CURRENT_ABSENT"
        and result_status == "CURRENT"
        and reason_code == RELATIONSHIP_RECREATION_REASON
    ):
        return "RECREATED"
    raise ValidationFailureError(
        "relationship lifecycle transition is not supported in this batch"
    )


def validate_completion_intent(
    *,
    completion_idempotency_key: str,
    terminal_at: str,
    terminal_status: str,
    completeness: str,
    safe_error_code: str | None,
    capabilities: Sequence[CapabilityIntent],
    observation_ids: Sequence[int],
) -> None:
    _require_text(completion_idempotency_key, "completion_idempotency_key")
    _require_text(terminal_at, "terminal_at")
    if terminal_status not in TERMINAL_SCAN_STATES:
        raise ValidationFailureError("terminal_status is not a frozen terminal scan state")
    valid_scan_shape = (
        terminal_status == "SUCCEEDED"
        and completeness in {"COMPLETE", "PARTIAL"}
        and safe_error_code is None
    ) or (
        terminal_status in {"FAILED", "INTERRUPTED"}
        and completeness in {"PARTIAL", "UNAVAILABLE"}
        and isinstance(safe_error_code, str)
        and bool(safe_error_code.strip())
    ) or (
        terminal_status == "CANCELLED"
        and completeness in {"PARTIAL", "UNAVAILABLE"}
        and (
            safe_error_code is None
            or (isinstance(safe_error_code, str) and bool(safe_error_code.strip()))
        )
    )
    if not valid_scan_shape:
        raise ValidationFailureError("terminal scan intent violates frozen status semantics")
    if not capabilities:
        raise ValidationFailureError("scan completion requires capability outcomes")
    capability_ids: set[str] = set()
    for capability in capabilities:
        _require_text(capability.capability_id, "capability_id")
        if capability.capability_id in capability_ids:
            raise ValidationFailureError("capability outcome identities must be unique")
        capability_ids.add(capability.capability_id)
        validate_capability_intent(capability)
    if completeness == "COMPLETE" and any(
        item.status in {"FAILED", "UNAVAILABLE"}
        or (
            item.status != "UNSUPPORTED"
            and item.completeness_contribution != "COMPLETE"
        )
        for item in capabilities
    ):
        raise ValidationFailureError(
            "complete scan intent has a partial or unavailable capability"
        )
    if completeness == "UNAVAILABLE" and any(
        item.observation_contribution
        or item.completeness_contribution == "COMPLETE"
        for item in capabilities
    ):
        raise ValidationFailureError(
            "unavailable scan intent contains complete or observation contribution"
        )
    if completeness == "PARTIAL" and not any(
        item.completeness_contribution == "PARTIAL"
        or item.status in {"FAILED", "UNAVAILABLE"}
        for item in capabilities
    ):
        raise ValidationFailureError("partial scan intent lacks a partial capability")
    if not observation_ids:
        raise ValidationFailureError("scan completion requires observation evidence")
    if any(not isinstance(item, int) or isinstance(item, bool) or item <= 0 for item in observation_ids):
        raise ValidationFailureError("observation IDs must be positive integers")
    if len(set(observation_ids)) != len(observation_ids):
        raise ValidationFailureError("observation evidence identities must be unique")


def validate_capability_intent(capability: CapabilityIntent) -> None:
    if capability.status not in CAPABILITY_STATES:
        raise ValidationFailureError("capability status is not frozen")
    if not isinstance(capability.observation_contribution, bool):
        raise ValidationFailureError("observation_contribution must be boolean")
    contribution = capability.completeness_contribution
    valid = (
        capability.status == "SUCCEEDED"
        and capability.retryable is None
        and capability.safe_error_code is None
        and contribution in {"COMPLETE", "PARTIAL"}
    ) or (
        capability.status == "FAILED"
        and isinstance(capability.retryable, bool)
        and isinstance(capability.safe_error_code, str)
        and bool(capability.safe_error_code.strip())
        and not capability.observation_contribution
        and contribution in {"PARTIAL", "NONE"}
    ) or (
        capability.status == "UNAVAILABLE"
        and isinstance(capability.retryable, bool)
        and (
            capability.safe_error_code is None
            or (
                isinstance(capability.safe_error_code, str)
                and bool(capability.safe_error_code.strip())
            )
        )
        and not capability.observation_contribution
        and contribution in {"PARTIAL", "NONE"}
    ) or (
        capability.status == "UNSUPPORTED"
        and capability.retryable is None
        and capability.safe_error_code is None
        and not capability.observation_contribution
        and contribution == "NONE"
    )
    if not valid:
        raise ValidationFailureError("capability outcome violates frozen status semantics")


def validate_scan_state(
    scan: Mapping[str, object],
    *,
    expected_installation_id: int,
    terminal_at: str,
    terminal_status: str,
    completeness: str,
    safe_error_code: str | None,
) -> bool:
    if int(scan["installation_id"]) != expected_installation_id:
        raise ValidationFailureError("scan does not belong to the expected installation")
    status = str(scan["status"])
    if status == "RUNNING":
        if (
            scan["completeness"] != "PENDING"
            or scan["terminal_at"] is not None
            or scan["safe_error_code"] is not None
        ):
            raise ValidationFailureError("persisted running scan has an invalid starting shape")
        return False
    if status not in TERMINAL_SCAN_STATES:
        raise ValidationFailureError("persisted scan has an unsupported lifecycle state")
    expected = {
        "terminal_at": terminal_at,
        "status": terminal_status,
        "completeness": completeness,
        "safe_error_code": safe_error_code,
    }
    if any(scan.get(name) != value for name, value in expected.items()):
        raise IdempotencyConflictError("scan has a conflicting terminal result")
    return True


def validate_observation_ownership(
    *,
    scan_run_id: int,
    all_scan_observations: Sequence[Mapping[str, object]],
    requested_observations: Sequence[Mapping[str, object] | None],
    requested_ids: Sequence[int],
) -> None:
    if any(item is None for item in requested_observations):
        raise ValidationFailureError("completion references a missing observation")
    rows = tuple(item for item in requested_observations if item is not None)
    if any(int(item["scan_run_id"]) != scan_run_id for item in rows):
        raise ValidationFailureError("completion observation belongs to a different scan")
    persisted_ids = {int(item["id"]) for item in all_scan_observations}
    if set(requested_ids) != persisted_ids:
        raise ValidationFailureError(
            "completion must reference the exact persisted observation set for the scan"
        )


def validate_no_partial_completion(
    *,
    existing_capabilities: Sequence[Mapping[str, object]],
    linked_terminal_audits: Sequence[Mapping[str, object]],
    audit_for_idempotency: Mapping[str, object] | None,
) -> None:
    if existing_capabilities or linked_terminal_audits:
        raise ValidationFailureError("running scan has partial completion artifacts")
    if audit_for_idempotency is not None:
        raise IdempotencyConflictError("completion audit identity is already in use")


def validate_retry_artifacts(
    *,
    scan: Mapping[str, object],
    completion_idempotency_key: str,
    terminal_at: str,
    authority: str,
    architecture_version: str,
    capabilities: Sequence[CapabilityIntent],
    existing_capabilities: Sequence[Mapping[str, object]],
    linked_terminal_audits: Sequence[Mapping[str, object]],
    audit_for_idempotency: Mapping[str, object] | None,
    subject_links: Sequence[Mapping[str, object]],
    evidence_links: Sequence[Mapping[str, object]],
    observation_ids: Sequence[int],
    schema_version: int,
) -> tuple[tuple[int, ...], int]:
    by_capability = {str(item["capability_id"]): item for item in existing_capabilities}
    if set(by_capability) != {item.capability_id for item in capabilities}:
        raise IdempotencyConflictError("completion has conflicting capability identities")
    capability_ids: list[int] = []
    for intent in capabilities:
        row = by_capability[intent.capability_id]
        expected = {
            "scan_run_id": int(scan["id"]),
            "capability_id": intent.capability_id,
            "status": intent.status,
            "retryable": None if intent.retryable is None else int(intent.retryable),
            "safe_error_code": intent.safe_error_code,
            "observation_contribution": int(intent.observation_contribution),
            "completeness_contribution": intent.completeness_contribution,
            "recorded_at": terminal_at,
        }
        if any(row.get(name) != value for name, value in expected.items()):
            raise IdempotencyConflictError("completion has conflicting capability intent")
        capability_ids.append(int(row["id"]))

    if len(linked_terminal_audits) != 1 or audit_for_idempotency is None:
        raise IdempotencyConflictError("completed scan has inconsistent terminal audit identity")
    audit = linked_terminal_audits[0]
    if int(audit["id"]) != int(audit_for_idempotency["id"]):
        raise IdempotencyConflictError("completion audit identities do not resolve to one row")
    audit_expected = {
        "installation_id": int(scan["installation_id"]),
        "idempotency_key": completion_idempotency_key,
        "event_kind": "SCAN_TERMINATED",
        "recorded_at": terminal_at,
        "authority": authority,
        "provenance_ref": None,
        "architecture_version": architecture_version,
        "contract_version": scan["contract_version"],
        "schema_version": schema_version,
        "implementation_version": scan["implementation_version"],
        "outcome": "SUCCEEDED",
        "safe_failure_code": None,
    }
    if any(audit.get(name) != value for name, value in audit_expected.items()):
        raise IdempotencyConflictError("completion has conflicting terminal audit intent")

    expected_subjects = {
        ("SCAN_RUN", int(scan["id"]), SCAN_AUDIT_SUBJECT_ROLE),
    }
    actual_subjects = {
        (str(item["subject_kind"]), int(item["subject_id"]), str(item["role"]))
        for item in subject_links
    }
    if actual_subjects != expected_subjects:
        raise IdempotencyConflictError("completion has conflicting audit subject links")
    expected_evidence = {
        (observation_id, SCAN_AUDIT_EVIDENCE_ROLE, ordinal)
        for ordinal, observation_id in enumerate(observation_ids)
    }
    actual_evidence = {
        (int(item["observation_id"]), str(item["role"]), int(item["ordinal"]))
        for item in evidence_links
    }
    if actual_evidence != expected_evidence or len(evidence_links) != len(observation_ids):
        raise IdempotencyConflictError("completion has conflicting audit evidence links")
    return tuple(capability_ids), int(audit["id"])
