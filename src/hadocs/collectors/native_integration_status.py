from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re

from hadocs.providers import HomeAssistantProvider


CONTRACT_VERSION = "hadocs.integration-status-domain.v1"
OBSERVATION_KEY_PREFIX = f"{CONTRACT_VERSION}:"
SOURCE_COMMAND = "config_entries/get"
RELEVANT_DOMAINS = frozenset({"mikrotik", "unifi"})
VERIFIED_STATES = frozenset(
    {
        "loaded",
        "setup_error",
        "migration_error",
        "setup_retry",
        "not_loaded",
        "failed_unload",
        "setup_in_progress",
        "unload_in_progress",
    }
)
PROBLEM_STATES = frozenset(
    {"setup_error", "migration_error", "setup_retry", "failed_unload"}
)
EVIDENCE_COMPLETE = "AUTHORITATIVE_SETUP_LIFECYCLE"
EVIDENCE_PARTIAL = "PARTIAL_UNKNOWN_STATE"

# Home Assistant integration domains are lowercase underscore slugs. The API
# source is Core's authenticated config_entries/get WebSocket command; its
# response fragment and ConfigEntryState enum are defined here:
# https://github.com/home-assistant/core/blob/dev/homeassistant/components/config/config_entries.py
# https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py
_DOMAIN_PATTERN = re.compile(r"[a-z0-9_]+")


class NativeIntegrationStatusError(ValueError):
    """A redacted failure at the native integration-status boundary."""


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def canonical_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        dict(value),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def observation_key(domain: str) -> str:
    if _DOMAIN_PATTERN.fullmatch(domain) is None or domain not in RELEVANT_DOMAINS:
        raise NativeIntegrationStatusError(
            "native integration-status observation has an invalid domain"
        )
    return f"{OBSERVATION_KEY_PREFIX}{domain}"


def validate_domain_observation(value: object) -> dict[str, object]:
    """Return one allowlisted canonical aggregate or fail with a redacted error."""

    if not isinstance(value, Mapping):
        raise NativeIntegrationStatusError(
            "native integration-status observation has an invalid shape"
        )
    allowed = {
        "contract_version",
        "domain",
        "entry_count",
        "state_counts",
        "problem_entry_count",
        "unknown_state_count",
        "observed_at",
        "evidence_quality",
        "immutable_digest",
    }
    if set(value) != allowed:
        raise NativeIntegrationStatusError(
            "native integration-status observation has invalid fields"
        )
    domain = value.get("domain")
    if not isinstance(domain, str):
        raise NativeIntegrationStatusError(
            "native integration-status observation has an invalid domain"
        )
    observation_key(domain)
    if value.get("contract_version") != CONTRACT_VERSION:
        raise NativeIntegrationStatusError(
            "native integration-status observation has an invalid contract"
        )
    observed_at = value.get("observed_at")
    if not isinstance(observed_at, str) or not observed_at.strip():
        raise NativeIntegrationStatusError(
            "native integration-status observation time is invalid"
        )
    state_counts_value = value.get("state_counts")
    if not isinstance(state_counts_value, Mapping):
        raise NativeIntegrationStatusError(
            "native integration-status state counts are invalid"
        )
    state_counts: dict[str, int] = {}
    for state, count in state_counts_value.items():
        if (
            not isinstance(state, str)
            or state not in VERIFIED_STATES
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count <= 0
        ):
            raise NativeIntegrationStatusError(
                "native integration-status state counts are invalid"
            )
        state_counts[state] = count
    entry_count = value.get("entry_count")
    problem_count = value.get("problem_entry_count")
    unknown_count = value.get("unknown_state_count")
    if any(
        not isinstance(item, int) or isinstance(item, bool) or item < 0
        for item in (entry_count, problem_count, unknown_count)
    ):
        raise NativeIntegrationStatusError(
            "native integration-status aggregate counts are invalid"
        )
    assert isinstance(entry_count, int)
    assert isinstance(problem_count, int)
    assert isinstance(unknown_count, int)
    if entry_count <= 0 or entry_count != sum(state_counts.values()) + unknown_count:
        raise NativeIntegrationStatusError(
            "native integration-status aggregate counts conflict"
        )
    expected_problem_count = sum(
        count for state, count in state_counts.items() if state in PROBLEM_STATES
    )
    if problem_count != expected_problem_count:
        raise NativeIntegrationStatusError(
            "native integration-status problem count conflicts"
        )
    expected_quality = EVIDENCE_COMPLETE if unknown_count == 0 else EVIDENCE_PARTIAL
    if value.get("evidence_quality") != expected_quality:
        raise NativeIntegrationStatusError(
            "native integration-status evidence quality conflicts"
        )
    core: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "domain": domain,
        "entry_count": entry_count,
        "state_counts": dict(sorted(state_counts.items())),
        "problem_entry_count": problem_count,
        "unknown_state_count": unknown_count,
        "observed_at": observed_at,
        "evidence_quality": expected_quality,
    }
    digest = value.get("immutable_digest")
    expected_digest = hashlib.sha256(canonical_bytes(core)).hexdigest()
    if digest != expected_digest:
        raise NativeIntegrationStatusError(
            "native integration-status immutable digest conflicts"
        )
    core["immutable_digest"] = expected_digest
    return core


@dataclass(frozen=True, slots=True)
class DomainIntegrationStatusObservation:
    contract_version: str
    domain: str
    entry_count: int
    state_counts: tuple[tuple[str, int], ...]
    problem_entry_count: int
    unknown_state_count: int
    observed_at: str
    evidence_quality: str
    immutable_digest: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "domain": self.domain,
            "entry_count": self.entry_count,
            "state_counts": dict(self.state_counts),
            "problem_entry_count": self.problem_entry_count,
            "unknown_state_count": self.unknown_state_count,
            "observed_at": self.observed_at,
            "evidence_quality": self.evidence_quality,
            "immutable_digest": self.immutable_digest,
        }


class NativeIntegrationStatusCollector:
    """Aggregate config-entry setup lifecycle state without retaining identity."""

    def __init__(self, clock: Callable[[], str] | None = None) -> None:
        self._clock = clock or _utc_now

    def collect(
        self, provider: HomeAssistantProvider
    ) -> list[dict[str, object]]:
        response = provider.get_config_entries()
        if not isinstance(response, Sequence) or isinstance(response, (str, bytes)):
            raise NativeIntegrationStatusError(
                "native integration-status response has an invalid shape"
            )

        # Raw entry_id exists only in this local de-duplication map. Neither its
        # keys nor any original response record cross the collector boundary.
        distinct: dict[str, tuple[str, str]] = {}
        for raw in response:
            if not isinstance(raw, Mapping):
                raise NativeIntegrationStatusError(
                    "native integration-status response contains an invalid entry"
                )
            entry_id = raw.get("entry_id")
            domain = raw.get("domain")
            state = raw.get("state")
            if not isinstance(entry_id, str) or not entry_id:
                raise NativeIntegrationStatusError(
                    "native integration-status response is missing entry identity"
                )
            if (
                not isinstance(domain, str)
                or _DOMAIN_PATTERN.fullmatch(domain) is None
            ):
                raise NativeIntegrationStatusError(
                    "native integration-status response has an invalid domain"
                )
            if not isinstance(state, str) or not state:
                raise NativeIntegrationStatusError(
                    "native integration-status response has an invalid state"
                )
            if domain not in RELEVANT_DOMAINS:
                continue
            semantic = (domain, state)
            previous = distinct.get(entry_id)
            if previous is not None and previous != semantic:
                raise NativeIntegrationStatusError(
                    "native integration-status response contains conflicting entries"
                )
            distinct[entry_id] = semantic

        grouped: dict[str, Counter[str]] = defaultdict(Counter)
        unknown: Counter[str] = Counter()
        for domain, state in distinct.values():
            if state in VERIFIED_STATES:
                grouped[domain][state] += 1
            else:
                unknown[domain] += 1
                grouped.setdefault(domain, Counter())

        observed_at = self._clock()
        if not isinstance(observed_at, str) or not observed_at.strip():
            raise NativeIntegrationStatusError(
                "native integration-status observation time is invalid"
            )

        result: list[dict[str, object]] = []
        for domain in sorted(grouped):
            state_counts = tuple(sorted(grouped[domain].items()))
            unknown_count = unknown[domain]
            entry_count = sum(count for _, count in state_counts) + unknown_count
            problem_count = sum(
                count for state, count in state_counts if state in PROBLEM_STATES
            )
            core: dict[str, object] = {
                "contract_version": CONTRACT_VERSION,
                "domain": domain,
                "entry_count": entry_count,
                "state_counts": dict(state_counts),
                "problem_entry_count": problem_count,
                "unknown_state_count": unknown_count,
                "observed_at": observed_at,
                "evidence_quality": (
                    EVIDENCE_COMPLETE if unknown_count == 0 else EVIDENCE_PARTIAL
                ),
            }
            digest = hashlib.sha256(canonical_bytes(core)).hexdigest()
            result.append(
                DomainIntegrationStatusObservation(
                    contract_version=CONTRACT_VERSION,
                    domain=domain,
                    entry_count=entry_count,
                    state_counts=state_counts,
                    problem_entry_count=problem_count,
                    unknown_state_count=unknown_count,
                    observed_at=observed_at,
                    evidence_quality=str(core["evidence_quality"]),
                    immutable_digest=digest,
                ).as_dict()
            )
        return result
