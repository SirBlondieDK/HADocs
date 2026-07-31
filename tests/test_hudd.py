from hadocs.hudd import find_device, search_organizations
from hadocs.hudd.database import connect
from hadocs.hudd.matcher import normalize


def test_hudd_database_integrity():
    with connect(read_only=True) as con:
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert con.execute("SELECT COUNT(*) FROM organizations").fetchone()[0] > 0
        assert con.execute("SELECT COUNT(*) FROM devices").fetchone()[0] >= 2


def test_hudd_organization_lookup():
    assert search_organizations("Aqara")


def test_exact_model_and_manufacturer_match():
    result = find_device(manufacturer="Aqara", model="RTCGQ11LM")
    assert result.device is not None
    assert result.device.hudd_id == "HUDD-DEV-000001"
    assert result.level == "probable"
    assert result.confidence >= 0.80
    assert "model" in result.matched_fields


def test_identifier_match_for_tuya_oem():
    result = find_device(
        manufacturer="_TZ3210_mja6r5ix",
        model="TS0505B",
        identifiers={"zigbee_manufacturer": "_TZ3210_mja6r5ix"},
    )
    assert result.device is not None
    assert result.device.hudd_id == "HUDD-DEV-000002"
    assert result.level == "exact"
    assert result.confidence >= 0.95


def test_unknown_device_is_not_forced_to_match():
    result = find_device(manufacturer="Example Vendor", model="DOES-NOT-EXIST")
    assert result.device is None
    assert result.level == "unknown"


def test_normalize_handles_home_assistant_identity_noise():
    assert normalize(" _TZ3210-mja6r5ix ") == "tz3210mja6r5ix"
