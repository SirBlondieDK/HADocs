import json
from src.hadocs.core.device_overrides import load_device_overrides, load_device_overrides_file

def test_load_dedicated_devices_format(tmp_path):
    path = tmp_path / "device_overrides.json"
    path.write_text(json.dumps({"version":1,"devices":[{"device_id":"abc","expected_offline":True,"reason":"PIR"}]}), encoding="utf-8")
    overrides = load_device_overrides_file(path)
    assert len(overrides) == 1
    assert overrides[0].device_id == "abc"
    assert overrides[0].expected_offline is True

def test_missing_dedicated_file_is_empty(tmp_path):
    assert load_device_overrides_file(tmp_path / "missing.json") == ()

def test_inline_overrides_take_priority(tmp_path):
    path = tmp_path / "device_overrides.json"
    path.write_text(json.dumps({"devices":[{"device_name":"Lamp","reason":"file"}]}), encoding="utf-8")
    overrides = load_device_overrides({
        "device_overrides_file": str(path),
        "device_overrides": [{"device_id":"abc","expected_offline":True,"reason":"inline"}],
    }, base_dir=tmp_path)
    assert overrides[0].device_id == "abc"
    assert overrides[1].device_name == "Lamp"
