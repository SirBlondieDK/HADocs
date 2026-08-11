from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "workflow_name",
    (
        "build-release.yml",
        "build-windows.yml",
    ),
)
def test_windows_workflows_run_pytest_as_python_module(workflow_name):
    workflow = (
        ROOT / ".github" / "workflows" / workflow_name
    ).read_text(encoding="utf-8")

    commands = {
        line.strip()
        for line in workflow.splitlines()
    }

    assert "run: python -m pytest" in commands
    assert "run: pytest" not in commands
