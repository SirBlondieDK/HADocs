from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from .models import Device, DeviceIdentity, DeviceMatch
from .repository import HUDDRepository


def normalize(value: str | None) -> str:
    """Normalize device identity values without inventing equivalences."""
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", value)


def _similarity(left: str | None, right: str | None) -> float:
    a, b = normalize(left), normalize(right)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


class DeviceMatcher:
    def __init__(self, repository: HUDDRepository) -> None:
        self.repository = repository

    def match(
        self,
        *,
        manufacturer: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        product_name: str | None = None,
        hardware_revision: str | None = None,
        region: str | None = None,
        identifiers: dict[str, str] | None = None,
    ) -> DeviceMatch:
        identity = DeviceIdentity(
            manufacturer=manufacturer,
            brand=brand,
            model=model,
            product_name=product_name,
            hardware_revision=hardware_revision,
            region=region,
            identifiers=identifiers or {},
        )
        candidates = self.repository.candidate_devices(identity, limit=100)
        if not candidates:
            return DeviceMatch(
                device=None,
                confidence=0.0,
                level="unknown",
                reason="No HUDD candidate matched the supplied identity",
                warnings=["The device should be added to the HUDD review queue"],
            )

        ranked = sorted(
            (self._score(identity, candidate) for candidate in candidates),
            key=lambda result: result.confidence,
            reverse=True,
        )
        best = ranked[0]
        if best.confidence < 0.45:
            return DeviceMatch(
                device=None,
                confidence=best.confidence,
                level="unknown",
                reason=f"Best candidate was below the acceptance threshold: {best.reason}",
                warnings=["Possible candidate exists, but manual verification is required"],
            )
        if len(ranked) > 1 and ranked[1].confidence >= best.confidence - 0.05:
            best.warnings.append("A second candidate has a nearly identical score")
            if best.level == "exact":
                best.level = "probable"
        return best

    def _score(self, identity: DeviceIdentity, device: Device) -> DeviceMatch:
        score = 0.0
        matched: list[str] = []
        warnings: list[str] = []
        details: list[str] = []

        target_identifiers = {
            normalize(kind): normalize(value)
            for kind, value in identity.identifiers.items()
            if normalize(value)
        }
        candidate_identifiers = {
            normalize(kind): {normalize(value) for value in values}
            for kind, values in device.identifiers.items()
        }
        for kind, value in target_identifiers.items():
            if value and value in candidate_identifiers.get(kind, set()):
                score += 0.65
                matched.append(f"identifier:{kind}")
                details.append(f"exact {kind} identifier")
                break

        model = normalize(identity.model)
        candidate_models = {normalize(device.model)} | {normalize(alias) for alias in device.aliases}
        candidate_models.discard("")
        if model and model in candidate_models:
            score += 0.55
            matched.append("model")
            details.append("exact model or model alias")
        elif model and device.model:
            similarity = _similarity(identity.model, device.model)
            if similarity >= 0.92:
                score += 0.30
                matched.append("model_similar")
                details.append(f"high model similarity ({similarity:.2f})")

        target_orgs = {normalize(identity.manufacturer), normalize(identity.brand)} - {""}
        candidate_orgs = {normalize(device.manufacturer), normalize(device.brand)} - {""}
        if target_orgs & candidate_orgs:
            score += 0.25
            matched.append("organization")
            details.append("exact brand/manufacturer")

        if identity.product_name and device.product_name:
            name_similarity = max(
                [_similarity(identity.product_name, device.product_name)]
                + [_similarity(identity.product_name, alias) for alias in device.aliases]
            )
            if name_similarity >= 0.90:
                score += 0.15
                matched.append("product_name")
                details.append(f"product-name similarity ({name_similarity:.2f})")
            elif name_similarity >= 0.75:
                score += 0.08
                matched.append("product_name_partial")
                details.append(f"partial product-name similarity ({name_similarity:.2f})")

        if identity.hardware_revision:
            if normalize(identity.hardware_revision) == normalize(device.hardware_revision):
                score += 0.05
                matched.append("hardware_revision")
                details.append("exact hardware revision")
            elif device.hardware_revision:
                score -= 0.12
                warnings.append("Hardware revision differs")

        if identity.region:
            if normalize(identity.region) == normalize(device.region):
                score += 0.05
                matched.append("region")
                details.append("exact region")
            elif device.region:
                score -= 0.10
                warnings.append("Region differs")

        score = max(0.0, min(score, 1.0))
        if score >= 0.90:
            level = "exact"
        elif score >= 0.70:
            level = "probable"
        elif score >= 0.45:
            level = "possible"
            warnings.append("Manual verification is recommended")
        else:
            level = "unknown"

        return DeviceMatch(
            device=device,
            confidence=round(score, 3),
            level=level,
            reason=", ".join(details) if details else "weak database candidate",
            matched_fields=matched,
            warnings=warnings,
        )
