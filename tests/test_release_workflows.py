from pathlib import Path
import re

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
WINDOWS_WORKFLOWS = (
    "build-release.yml",
    "build-windows.yml",
)


def load_workflow(workflow_name: str) -> dict:
    workflow_path = ROOT / ".github" / "workflows" / workflow_name
    workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(workflow, dict)
    return workflow


def workflow_steps(workflow_name: str) -> list[dict]:
    workflow = load_workflow(workflow_name)
    return workflow["jobs"]["build-windows"]["steps"]


def step_using(steps: list[dict], action: str) -> dict:
    return next(step for step in steps if step.get("uses") == action)


def step_with_id(steps: list[dict], step_id: str) -> dict:
    return next(step for step in steps if step.get("id") == step_id)


@pytest.mark.parametrize(
    "workflow_name",
    WINDOWS_WORKFLOWS,
)
def test_windows_workflows_run_for_main_pull_requests_and_v_tags(workflow_name):
    triggers = load_workflow(workflow_name)["on"]

    assert triggers["pull_request"] == {"branches": ["main"]}
    assert triggers["push"] == {"tags": ["v*"]}


@pytest.mark.parametrize("workflow_name", WINDOWS_WORKFLOWS)
def test_windows_workflows_delegate_to_the_canonical_python_314_build(workflow_name):
    workflow = load_workflow(workflow_name)
    steps = workflow_steps(workflow_name)
    setup = step_using(steps, "actions/setup-python@v5")
    build = next(step for step in steps if "installer/build_windows.ps1" in step.get("run", ""))
    build_command = build["run"]

    assert workflow["jobs"]["build-windows"]["runs-on"] == "windows-latest"
    assert setup["with"]["python-version"] == "3.14.3"
    assert '-PythonExecutable "$env:pythonLocation\\python.exe"' in build_command
    assert "-SkipDependencies" not in build_command
    assert "-SkipTests" not in build_command
    assert "-SkipPackaging" not in build_command
    assert workflow["permissions"] == {"contents": "read"}

    workflow_text = (ROOT / ".github" / "workflows" / workflow_name).read_text(
        encoding="utf-8"
    )
    assert "releases: write" not in workflow_text
    assert "gh release" not in workflow_text.lower()
    assert "action-gh-release" not in workflow_text.lower()


@pytest.mark.parametrize("workflow_name", WINDOWS_WORKFLOWS)
def test_default_checkout_preserves_pr_merge_ref_and_pushed_tag(workflow_name):
    checkout = step_using(workflow_steps(workflow_name), "actions/checkout@v4")

    assert "ref" not in checkout.get("with", {})
    assert "merge ref or tag" in checkout["name"].lower()


@pytest.mark.parametrize("workflow_name", WINDOWS_WORKFLOWS)
def test_artifact_suffix_is_event_specific_and_rejects_path_characters(workflow_name):
    steps = workflow_steps(workflow_name)
    suffix_step = step_with_id(steps, "artifact-name")
    upload = step_using(steps, "actions/upload-artifact@v4")
    script = suffix_step["run"]

    assert suffix_step["env"] == {
        "EVENT_NAME": "${{ github.event_name }}",
        "PR_NUMBER": "${{ github.event.pull_request.number }}",
        "REF_TYPE": "${{ github.ref_type }}",
        "REF_NAME": "${{ github.ref_name }}",
        "RUN_ID": "${{ github.run_id }}",
    }
    assert '$Suffix = "pr-$env:PR_NUMBER"' in script
    assert '$Suffix = $env:REF_NAME' in script
    assert '$Suffix = "run-$env:RUN_ID"' in script
    assert "^[A-Za-z0-9][A-Za-z0-9._-]*$" in script
    safe_pattern = re.search(r"\$Suffix -notmatch '([^']+)'", script)
    assert safe_pattern is not None
    assert re.fullmatch(safe_pattern.group(1), "pr-52")
    assert re.fullmatch(safe_pattern.group(1), "v0.17.0-rc6")
    assert not re.fullmatch(safe_pattern.group(1), "52/merge")
    assert not re.fullmatch(safe_pattern.group(1), "../v0.17.0-rc6")
    assert "${{ steps.artifact-name.outputs.suffix }}" in upload["with"]["name"]
    assert "github.ref_name" not in upload["with"]["name"]
    assert "52/merge" not in upload["with"]["name"]


@pytest.mark.parametrize(
    ("workflow_name", "expected_paths"),
    (
        (
            "build-release.yml",
            {"dist/windows/portable/*.zip", "dist/windows/manifests/*.sha256"},
        ),
        (
            "build-windows.yml",
            {
                "dist/windows/staging/HADocs",
                "dist/windows/portable/*.zip",
                "dist/windows/manifests/*.sha256",
            },
        ),
    ),
)
def test_windows_artifacts_use_only_canonical_output_paths(workflow_name, expected_paths):
    upload = step_using(workflow_steps(workflow_name), "actions/upload-artifact@v4")
    paths = {line.strip() for line in upload["with"]["path"].splitlines() if line.strip()}

    assert paths == expected_paths
    assert all("${{" not in path and ".." not in path for path in paths)


@pytest.mark.parametrize("workflow_name", WINDOWS_WORKFLOWS)
def test_pr_build_reaches_staged_and_portable_runtime_gates(workflow_name):
    steps = workflow_steps(workflow_name)
    build = next(step for step in steps if "installer/build_windows.ps1" in step.get("run", ""))
    contract = (ROOT / "installer" / "build_windows.ps1").read_text(encoding="utf-8")

    assert "-SkipPackaging" not in build["run"]
    assert "Canonical staging executable smoke-test" in contract
    assert "Extracted portable executable smoke-test" in contract
    assert "Portable ZIP payload differs from canonical staging" in contract


def test_general_python_tests_remain_separate_from_release_build_pin():
    workflow = (
        ROOT / ".github" / "workflows" / "tests.yml"
    ).read_text(encoding="utf-8")

    assert 'python-version: "3.14"' in workflow
    assert 'python-version: "3.14.3"' not in workflow
