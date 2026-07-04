def calculate_health_score(analysis: dict) -> tuple[int, list[str]]:
    score = 100
    notes = []

    unavailable = analysis["counts"]["unavailable"]
    unknown = analysis["counts"]["unknown"]
    low_batteries = len(analysis["low_batteries"])
    critical = len(analysis["offline_critical"])
    devices_without_area = len(analysis["devices_without_area"])

    if critical:
        penalty = min(40, critical * 10)
        score -= penalty
        notes.append(f"{critical} kritiske entities er unknown/unavailable (-{penalty})")

    if low_batteries:
        penalty = min(15, low_batteries * 3)
        score -= penalty
        notes.append(f"{low_batteries} batterier er lave (-{penalty})")

    if unavailable:
        penalty = min(20, unavailable // 10)
        score -= penalty
        notes.append(f"{unavailable} unavailable states (-{penalty})")

    if unknown:
        penalty = min(15, unknown // 25)
        score -= penalty
        notes.append(f"{unknown} unknown states (-{penalty})")

    if devices_without_area:
        penalty = min(10, devices_without_area // 10)
        score -= penalty
        notes.append(f"{devices_without_area} enheder uden rum (-{penalty})")

    score = max(0, min(100, score))
    return score, notes
