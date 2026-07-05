from src.hadocs.core.history import load_history


def test_empty_history(tmp_path):
    cfg = {"output_dir": str(tmp_path / "output")}
    assert load_history(cfg) == []
