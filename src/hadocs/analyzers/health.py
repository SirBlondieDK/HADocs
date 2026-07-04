def calculate_health_score(analysis: dict) -> tuple[int, list[str]]:
    score = 100
    notes = []
    critical = len(analysis["offline_critical"])
    real_unavailable = len(analysis["real_unavailable"])
    real_unknown = len(analysis["real_unknown"])
    low_batteries = len(analysis["low_batteries"])
    devices_without_area = len(analysis["devices_without_area"])
    duplicates = len(analysis["duplicate_names"])
    if critical:
        penalty = min(50, critical * 12)
        score -= penalty
        notes.append(f"{critical} critical entities are offline or unknown (-{penalty})")
    if real_unavailable:
        penalty = min(25, real_unavailable * 2)
        score -= penalty
        notes.append(f"{real_unavailable} real entities are unavailable (-{penalty})")
    if real_unknown:
        penalty = min(15, real_unknown)
        score -= penalty
        notes.append(f"{real_unknown} real entities are unknown (-{penalty})")
    if low_batteries:
        severe = sum(1 for _, value in analysis["low_batteries"] if value <= 10)
        mild = low_batteries - severe
        penalty = min(20, severe * 4 + mild * 2)
        score -= penalty
        notes.append(f"{low_batteries} batteries are low (-{penalty})")
    if devices_without_area:
        penalty = min(10, max(1, devices_without_area // 5))
        score -= penalty
        notes.append(f"{devices_without_area} physical devices have no area (-{penalty})")
    if duplicates:
        penalty = min(5, max(1, duplicates // 10))
        score -= penalty
        notes.append(f"{duplicates} duplicate friendly names found (-{penalty})")
    ignored = len(analysis.get("ignored_unknown_unavailable", []))
    if ignored:
        notes.append(f"{ignored} system/service entities were ignored in Health Score")
    return max(0, min(100, score)), notes
