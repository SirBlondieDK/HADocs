from __future__ import annotations

from collections.abc import Callable, Mapping
import json
from pathlib import Path
from typing import Any


_FORBIDDEN_MARKERS = (
    "refh1_entity_",
    "persisted_scan_ref",
    "supporting_observation_ids",
    "supporting_relationship_ids",
    "database_id",
    "entity_id",
    "device_id",
)

_CLASSIFICATIONS = {
    "SUPPORTED_CANDIDATE",
    "INSUFFICIENT_EVIDENCE",
    "NOT_APPLICABLE",
    "REJECTED_CONFLICT",
    "BUNDLE_DISABLED",
    "BUNDLE_UNAVAILABLE",
    "BUNDLE_INVALID",
}


def _items(value: object) -> tuple[object, ...]:
    return tuple(value) if isinstance(value, (list, tuple)) else ()


def _text(value: object, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _count(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _string_list(value: object) -> list[str]:
    return [item for item in _items(value) if isinstance(item, str)]


def sanitize_preview_payload(value: object) -> dict[str, Any] | None:
    """Return only the public HASK Preview contract or fail closed."""

    if not isinstance(value, Mapping):
        return None

    serialized = json.dumps(value, ensure_ascii=True, sort_keys=True).casefold()
    if any(marker in serialized for marker in _FORBIDDEN_MARKERS):
        return None

    classification = _text(value.get("classification"))
    if classification not in _CLASSIFICATIONS:
        return None

    coverage = []
    for item in _items(value.get("coverage")):
        if not isinstance(item, Mapping):
            continue
        artifact = _text(item.get("artifact"))
        if artifact:
            coverage.append(
                {
                    "artifact": artifact,
                    "item_count": _count(item.get("item_count")),
                }
            )

    knowledge = []
    for item in _items(value.get("relevant_knowledge")):
        if not isinstance(item, Mapping):
            continue
        platform_id = _text(item.get("platform_id"))
        if platform_id:
            knowledge.append(
                {
                    "platform_id": platform_id,
                    "title": _text(item.get("title"), platform_id),
                    "summary": _text(item.get("summary")),
                    "status": _text(item.get("status"), "unknown"),
                }
            )

    matcher_readiness = []
    for item in _items(value.get("matcher_readiness")):
        if not isinstance(item, Mapping):
            continue
        readiness_state = _text(item.get("state"))
        if readiness_state not in {
            "READY",
            "BLOCKED",
            "NOT_APPLICABLE",
            "REJECTED_CONFLICT",
        }:
            continue
        matcher_readiness.append(
            {
                "state": readiness_state,
                "matcher_id": _text(item.get("matcher_id")),
                "matcher_version": _text(item.get("matcher_version")),
                "hask_record_ref": _text(item.get("hask_record_ref")),
                "platform_scope": _string_list(item.get("platform_scope")),
                "candidate_emitted": item.get("candidate_emitted") is True,
                "missing_evidence_categories": _string_list(
                    item.get("missing_evidence_categories")
                ),
                "rejection_codes": _string_list(item.get("rejection_codes")),
            }
        )

    candidates = []
    for item in _items(value.get("candidates")):
        if not isinstance(item, Mapping):
            continue
        candidate_classification = _text(item.get("classification"))
        if candidate_classification not in _CLASSIFICATIONS:
            continue
        candidates.append(
            {
                "classification": candidate_classification,
                "hask_record_ref": _text(item.get("hask_record_ref")),
                "matcher_id": _text(item.get("matcher_id")),
                "matcher_version": _text(item.get("matcher_version")),
                "supporting_evidence_categories": _string_list(
                    item.get("supporting_evidence_categories")
                ),
                "missing_evidence_categories": _string_list(
                    item.get("missing_evidence_categories")
                ),
                "rejection_code": _optional_text(item.get("rejection_code")),
                "applicability": _text(item.get("applicability"), "not confirmed"),
                "explanation": _text(item.get("explanation")),
            }
        )

    return {
        "feature_enabled": value.get("feature_enabled") is True,
        "hask_runtime_enabled": value.get("hask_runtime_enabled") is True,
        "bundle_available": value.get("bundle_available") is True,
        "bundle_valid": value.get("bundle_valid") is True,
        "bundle_source": _text(value.get("bundle_source"), "unknown"),
        "classification": classification,
        "validation_state": _text(value.get("validation_state"), "unknown"),
        "compatibility_state": _text(value.get("compatibility_state"), "not_checked"),
        "contract_version": _optional_text(value.get("contract_version")),
        "knowledge_content_version": _optional_text(
            value.get("knowledge_content_version")
        ),
        "knowledge_schema_version": _optional_text(
            value.get("knowledge_schema_version")
        ),
        "checksum_prefix": _optional_text(value.get("checksum_prefix")),
        "coverage": coverage,
        "relevant_knowledge": knowledge,
        "candidates": candidates,
        "matcher_readiness": matcher_readiness,
        "candidate_bridge_state": _text(
            value.get("candidate_bridge_state"), "NOT_AVAILABLE"
        ),
        "candidate_bridge_rejection_code": _optional_text(
            value.get("candidate_bridge_rejection_code")
        ),
        "limitations": _string_list(value.get("limitations")),
        "notice": _text(value.get("notice")),
        "analytical_impact_statement": _text(
            value.get("analytical_impact_statement")
        ),
    }


def load_latest_preview(
    path: Path,
    fallback: Mapping[str, object] | Callable[[], Mapping[str, object]],
) -> tuple[dict[str, Any], str]:
    try:
        persisted = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        persisted = None

    safe = sanitize_preview_payload(persisted)
    if safe is not None:
        return safe, "latest_scan"

    fallback_value = fallback() if callable(fallback) else fallback
    fallback_safe = sanitize_preview_payload(fallback_value)
    if fallback_safe is None:
        raise ValueError("live HASK Preview payload violated its public contract")
    return fallback_safe, "live_status"


def database_status_payload(status: object) -> dict[str, Any]:
    raw_counts = getattr(status, "counts", {})
    counts = {
        str(name): _count(value)
        for name, value in raw_counts.items()
    } if isinstance(raw_counts, Mapping) else {}

    return {
        "enabled": getattr(status, "enabled", False) is True,
        "identity_initialized": (
            getattr(status, "identity_initialized", False) is True
        ),
        "protected_backend": _text(
            getattr(status, "protected_backend", None),
            "not configured",
        ),
        "protected_material_valid": (
            getattr(status, "protected_material_valid", False) is True
        ),
        "database_file_present": (
            getattr(status, "database_file_present", False) is True
        ),
        "schema_version": getattr(status, "schema_version", None),
        "integrity_status": _text(
            getattr(status, "integrity_status", None),
            "not available",
        ),
        "foreign_key_status": _text(
            getattr(status, "foreign_key_status", None),
            "not available",
        ),
        "counts": counts,
        "hask_enabled": getattr(status, "hask_enabled", False) is True,
        "candidate_bridge_enabled": (
            getattr(status, "candidate_bridge_enabled", False) is True
        ),
        "native_domain_status_enabled": (
            getattr(status, "native_domain_status_enabled", False) is True
        ),
        "limitation": _text(getattr(status, "limitation", None)),
    }


def build_web_preview(
    preview: Mapping[str, Any],
    *,
    source: str,
    database_status: object,
) -> dict[str, Any]:
    result = dict(preview)
    coverage = result.get("coverage", [])
    knowledge = result.get("relevant_knowledge", [])
    candidates = result.get("candidates", [])
    matcher_readiness = result.get("matcher_readiness", [])

    classifications: dict[str, int] = {}
    for candidate in candidates:
        name = str(candidate.get("classification", "UNKNOWN"))
        classifications[name] = classifications.get(name, 0) + 1

    readiness_states: dict[str, int] = {}
    for matcher in matcher_readiness:
        name = str(matcher.get("state", "UNKNOWN"))
        readiness_states[name] = readiness_states.get(name, 0) + 1

    matcher_record_count = sum(
        _count(item.get("item_count"))
        for item in coverage
        if item.get("artifact") == "evidence_matchers"
    )

    result["preview_data_source"] = source
    result["statistics"] = {
        "artifact_count": len(coverage),
        "knowledge_record_count": sum(
            _count(item.get("item_count")) for item in coverage
        ),
        "relevant_platform_count": len(knowledge),
        "candidate_count": classifications.get("SUPPORTED_CANDIDATE", 0),
        "candidate_evaluation_count": len(matcher_readiness),
        "candidate_classifications": classifications,
        "matcher_record_count": matcher_record_count,
        "executable_matcher_count": len(matcher_readiness),
        "matcher_readiness_states": readiness_states,
    }
    result["operational_database"] = database_status_payload(database_status)
    return result
