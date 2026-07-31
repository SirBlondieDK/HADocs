from __future__ import annotations

from .loader import HaskBundle
from .models import CanonicalEvidenceMatch, KnowledgeCandidate, LocalEvidence

MAPPINGS = {
    "config_entry_setup_retry": ("config_entry_setup_retry",),
    "reauthentication_required": ("config_entry_reauthentication_required",),
    "entity_unavailable": ("entity_unavailable_state",),
    "unifi_controller_unreachable": ("unifi_controller_connection_state",),
    "unifi_authorization_failure": ("unifi_authorization_scope",),
    "mikrotik_api_unreachable": ("mikrotik_api_connection_state",),
    "mikrotik_authorization_failure": ("mikrotik_router_authorization_scope",),
    "dns_failure": ("dns_service_failure",),
}


def adapt_evidence(local: tuple[LocalEvidence, ...], bundle: HaskBundle) -> tuple[CanonicalEvidenceMatch, ...]:
    known = set(bundle.index("evidence_catalog.json")) | set(bundle.index("root_cause_candidates.json"))
    result = []
    for item in local:
        matched = tuple(value for value in MAPPINGS.get(item.evidence_id, ()) if value in known)
        result.append(CanonicalEvidenceMatch(item.evidence_id, matched, "matched" if matched else "no_match", len(matched) > 1))
    return tuple(result)


def adapt_candidates(platform_id: str, matches: tuple[CanonicalEvidenceMatch, ...], bundle: HaskBundle) -> tuple[KnowledgeCandidate, ...]:
    platform = bundle.platform(platform_id)
    canonical = {item for match in matches for item in match.canonical_ids}
    scenarios = bundle.index("diagnostic_scenarios.json")
    candidates = bundle.index("root_cause_candidates.json")
    recommendations = bundle.index("recommendations.json")
    verifications = bundle.index("verification_paths.json")
    applicability = bundle.items("applicability.json")
    conflicts = bundle.items("conflicts.json")
    gaps = bundle.items("known_gaps.json")
    selected_scenarios = []
    for scenario_id in platform["consumer_links"]["scenarios"]:
        scenario = scenarios[scenario_id]
        if canonical.intersection(scenario.get("references", {}).get("observations", [])):
            selected_scenarios.append(scenario)
    candidate_ids = sorted({item for scenario in selected_scenarios for item in scenario.get("references", {}).get("root_causes", [])})
    output = []
    for candidate_id in candidate_ids:
        candidate = candidates[candidate_id]
        scenario_ids = tuple(item["id"] for item in selected_scenarios if candidate_id in item.get("references", {}).get("root_causes", []))
        recommendation_ids = tuple(sorted({rid for item in selected_scenarios for rid in item.get("references", {}).get("recommendations", []) if rid in recommendations}))
        verification_ids = tuple(sorted(item["id"] for item in verifications.values() if item.get("recommendation_id") in recommendation_ids or item.get("record_id") in recommendation_ids))
        provenance = tuple(sorted({source for claim in candidate.get("claims", []) for source in claim.get("source_ids", [])}))
        app = tuple(item for item in applicability if item.get("record_id") == candidate_id)
        relevant_ids = {candidate_id, *scenario_ids, *recommendation_ids}
        output.append(KnowledgeCandidate(
            candidate_id, candidate.get("title", candidate_id), candidate.get("summary", ""), tuple(sorted(canonical)), (),
            tuple(sorted(set(platform["consumer_links"]["observations"]) - canonical)),
            tuple(item for item in candidate_ids if item != candidate_id), app,
            max((float(claim.get("confidence", 0.0)) for claim in candidate.get("claims", [])), default=0.0),
            scenario_ids, recommendation_ids, verification_ids, provenance,
            tuple(item for item in conflicts if item.get("record_id") in relevant_ids),
            tuple(item for item in gaps if item.get("record_id") in relevant_ids), False,
            {"pilot_only": True, "hadocs_score_impact": None, "confirmation_owner": "HADocs"},
        ))
    return tuple(output)
