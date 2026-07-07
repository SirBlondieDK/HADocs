from src.hadocs.utils.display import display_area


def test_area_report_display_formatter_is_available():
    assert display_area("_uden_område") == "No Area Assigned"
