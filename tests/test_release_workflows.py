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
def test_windows_workflows_delegate_to_the_canonical_python_314_build(workflow_name):
    workflow = (
        ROOT / ".github" / "workflows" / workflow_name
    ).read_text(encoding="utf-8")

    assert 'python-version: "3.14.3"' in workflow
    assert "installer/build_windows.ps1" in workflow
    assert '-PythonExecutable "$env:pythonLocation\\python.exe"' in workflow
    assert "-SkipDependencies" not in workflow
    assert "-SkipTests" not in workflow
    assert "pip install" not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "releases: write" not in workflow
    assert "gh release" not in workflow.lower()
    assert "action-gh-release" not in workflow.lower()


def test_general_python_tests_remain_separate_from_release_build_pin():
    workflow = (
        ROOT / ".github" / "workflows" / "tests.yml"
    ).read_text(encoding="utf-8")

    assert 'python-version: "3.14"' in workflow
    assert 'python-version: "3.14.3"' not in workflow


def test_tagged_release_artifact_keeps_the_triggering_ref_name():
    workflow = (
        ROOT / ".github" / "workflows" / "build-release.yml"
    ).read_text(encoding="utf-8")

    assert "HADocs-${{ github.ref_name }}-win64" in workflow
    assert "uses: actions/checkout@v4" in workflow
    assert "ref:" not in workflow
