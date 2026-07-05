from src.hadocs.knowledge.exporter import build_health, build_inventory, build_manifest


class Executive:
    score = 67
    status = "NEEDS ATTENTION"
    potential_score = 85
    estimated_repair_minutes = 37
    main_cause = "Mobile App devices"


def test_manifest_ai_compatible_not_connected():
    manifest = build_manifest()
    assert manifest["privacy"]["ai_compatible"] is True
    assert manifest["privacy"]["ai_connected"] is False
    assert manifest["privacy"]["ai_calls"] is False


def test_build_health():
    health = build_health(Executive())
    assert health["health_score"] == 67
    assert health["potential_score"] == 85


def test_inventory_none():
    inventory = build_inventory(None)
    assert inventory["areas"] == 0
