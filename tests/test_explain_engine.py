from src.hadocs.explain.engine import explain_key


def test_explain_mqtt():
    explanation = explain_key("mqtt")
    assert "MQTT" in explanation.title
    assert explanation.what_to_try_first


def test_explain_unknown_key():
    explanation = explain_key("something_unknown")
    assert explanation.title
    assert explanation.what_to_try_first
