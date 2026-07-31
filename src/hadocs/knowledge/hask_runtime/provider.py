from __future__ import annotations

from collections.abc import Mapping

from .models import RuntimeBundle, TypedMatcherContract


_MATCHER_OUTCOMES = frozenset({
    "conflict",
    "match",
    "missing_evidence",
    "no_match",
    "partial_match",
    "unknown_applicability",
})


class KnowledgeProvider:
    def __init__(self) -> None:
        self._bundle: RuntimeBundle | None = None

    def activate(self, bundle: RuntimeBundle) -> None:
        self._bundle = bundle

    def deactivate(self) -> None:
        self._bundle = None

    @property
    def active(self) -> bool:
        return self._bundle is not None

    @property
    def bundle(self) -> RuntimeBundle | None:
        return self._bundle

    def items(self, artifact: str) -> tuple:
        if self._bundle is None:
            return ()
        return self._bundle.artifacts[artifact]["items"]

    def typed_matcher_contracts(self) -> tuple[TypedMatcherContract, ...]:
        """Expose only complete typed contracts from the validated snapshot."""

        contracts: list[TypedMatcherContract] = []
        for record in self.items("evidence_matchers.json"):
            if not isinstance(record, Mapping):
                raise ValueError("typed HASK matcher contract is invalid")
            raw = record.get("matcher_contract")
            if raw is None:
                continue
            if not isinstance(raw, Mapping):
                raise ValueError("typed HASK matcher contract is invalid")
            scope = raw.get("platform_scope")
            required = raw.get("required_fields")
            outcomes = raw.get("outcomes")
            values = {
                "record_ref": record.get("id"),
                "matcher_id": record.get("id"),
                "version": raw.get("version"),
                "observation_types": raw.get("observation_types"),
                "evidence_target": raw.get("evidence_target"),
            }
            if (
                not all(isinstance(value, str) and value for value in (
                    values["record_ref"],
                    values["matcher_id"],
                    values["version"],
                    values["evidence_target"],
                ))
                or not isinstance(scope, Mapping)
                or not isinstance(scope.get("include"), tuple)
                or not scope["include"]
                or not all(isinstance(item, str) and item for item in scope["include"])
                or not isinstance(values["observation_types"], tuple)
                or not values["observation_types"]
                or not all(
                    isinstance(item, str) and item
                    for item in values["observation_types"]
                )
                or not isinstance(required, tuple)
                or not required
                or not isinstance(outcomes, Mapping)
                or not _MATCHER_OUTCOMES.issubset(outcomes)
            ):
                raise ValueError("typed HASK matcher contract is invalid")
            fields: list[tuple[str, str]] = []
            for field in required:
                if not isinstance(field, Mapping):
                    raise ValueError("typed HASK matcher contract is invalid")
                path = field.get("path")
                value_type = field.get("value_type")
                if not isinstance(path, str) or not path or not isinstance(
                    value_type, str
                ) or not value_type:
                    raise ValueError("typed HASK matcher contract is invalid")
                fields.append((path, value_type))
            contracts.append(TypedMatcherContract(
                record_ref=values["record_ref"],
                matcher_id=values["matcher_id"],
                version=values["version"],
                platform_scope=tuple(sorted(scope["include"])),
                observation_types=tuple(sorted(values["observation_types"])),
                required_fields=tuple(sorted(fields)),
                evidence_target=values["evidence_target"],
            ))
        return tuple(sorted(
            contracts,
            key=lambda item: (item.matcher_id, item.version, item.record_ref),
        ))
