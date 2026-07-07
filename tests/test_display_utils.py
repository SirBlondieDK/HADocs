from src.hadocs.utils.display import display_area, display_text, is_unassigned_area


def test_is_unassigned_area_detects_home_assistant_internal_values():
    assert is_unassigned_area("_uden_område")
    assert is_unassigned_area("_uden_omraade")
    assert is_unassigned_area("_uden_omr├Ñde")
    assert is_unassigned_area("")
    assert is_unassigned_area(None)


def test_display_area_uses_user_friendly_label():
    assert display_area("_uden_område") == "No Area Assigned"
    assert display_area("_uden_omraade") == "No Area Assigned"
    assert display_area("Køkken") == "Køkken"


def test_display_text_handles_none():
    assert display_text(None) == ""
    assert display_text("abc") == "abc"
