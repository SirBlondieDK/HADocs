from src.hadocs.analyzers.health import calculate_health_score


def test_health_score_ignores_system_entities_note():
    analysis = {
        "offline_critical": [],
        "real_unavailable": [],
        "real_unknown": [],
        "low_batteries": [],
        "devices_without_area": [],
        "duplicate_names": {},
        "ignored_unknown_unavailable": [1, 2, 3],
    }

    score, notes = calculate_health_score(analysis)

    assert score == 100
    assert any("ignored" in note.lower() for note in notes)


def test_health_score_penalizes_critical_entities():
    analysis = {
        "offline_critical": [1],
        "real_unavailable": [],
        "real_unknown": [],
        "low_batteries": [],
        "devices_without_area": [],
        "duplicate_names": {},
        "ignored_unknown_unavailable": [],
    }

    score, notes = calculate_health_score(analysis)

    assert score == 88
    assert notes
