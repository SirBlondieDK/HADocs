from src.hadocs.utils.normalize import (
    normalize_bool,
    normalize_dict,
    normalize_list,
    normalize_text,
    text_contains_any,
)


def test_normalize_text_handles_external_types():
    assert normalize_text(None) == ""
    assert normalize_text("") == ""
    assert normalize_text(123) == "123"
    assert normalize_text(12.5) == "12.5"
    assert normalize_text(True) == "true"
    assert normalize_text(False) == "false"
    assert normalize_text("  Fibaro  ") == "fibaro"


def test_normalize_bool_handles_external_types():
    assert normalize_bool(True) is True
    assert normalize_bool(False) is False
    assert normalize_bool(1) is True
    assert normalize_bool(0) is False
    assert normalize_bool("YES") is True
    assert normalize_bool("disabled") is False
    assert normalize_bool(None) is False
    assert normalize_bool("unexpected", default=True) is True


def test_normalize_list_handles_external_types():
    assert normalize_list(None) == []
    assert normalize_list([1, 2]) == [1, 2]
    assert normalize_list((1, 2)) == [1, 2]
    assert normalize_list("sensor.test") == ["sensor.test"]
    assert normalize_list(123) == [123]


def test_normalize_dict_handles_external_types():
    assert normalize_dict(None) == {}
    assert normalize_dict(123) == {}
    assert normalize_dict({"value": 1}) == {"value": 1}


def test_text_contains_any_handles_integer_values():
    assert text_contains_any(12345, ["234"])
    assert not text_contains_any(12345, ["fibaro"])


def test_text_contains_any_is_case_insensitive():
    assert text_contains_any("Fibaro System", ["fibaro"])
    assert text_contains_any("FIBARO", ["fibaro"])
    assert text_contains_any("fibaro", ["FIBARO"])


def test_text_contains_any_ignores_empty_patterns():
    assert not text_contains_any("fibaro", ["", None])
