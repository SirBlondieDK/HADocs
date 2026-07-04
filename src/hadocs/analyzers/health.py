def calculate_health_score(analysis: dict) -> tuple[int, list[str]]:
    score = 100
    notes = []

    critical = len(analysis.get("offline_critical", []))
    if critical:
        penalty = min(50, critical * 12)
        score -= penalty
        notes.append(f"{critical} critical entities are offline or unknown (-{penalty})")

    ignored = len(analysis.get("ignored_unknown_unavailable", []))
    if ignored:
        notes.append(f"{ignored} system/service entities were ignored in Health Score")

    return max(0, min(100, score)), notes
