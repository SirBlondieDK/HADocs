from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .adapters import adapt_candidates, adapt_evidence
from .config import PilotConfig
from .loader import BundleError, load_bundle
from .models import LocalEvidence


def run_pilot(platform_id: str, local_input: list[dict[str, Any]], config: PilotConfig) -> dict[str, Any]:
    if not config.enabled:
        return {"status": "pilot_disabled", "platform": platform_id, "scan_impact": "none"}
    if config.bundle_path is None:
        raise BundleError("bundle_path_missing", "enabled pilot requires local bundle path")
    bundle = load_bundle(config.bundle_path, strict=config.strict_validation)
    local = tuple(LocalEvidence(str(item["evidence_id"]), str(item.get("state", "unknown")), str(item.get("details", ""))) for item in local_input)
    matches = adapt_evidence(local, bundle)
    candidates = adapt_candidates(platform_id, matches, bundle)
    return {
        "status": "candidate_only" if candidates else "no_root_cause_candidate",
        "platform": platform_id,
        "contract_version": bundle.manifest["contract_version"],
        "local_evidence": [asdict(item) for item in local],
        "canonical_evidence": [asdict(item) for item in matches],
        "candidates": [asdict(item) for item in candidates],
        "confirmed_candidates": [],
        "health_score_impact": None,
        "production_scoring_changed": False,
        "scan_impact": "none",
    }
