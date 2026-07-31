from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import textwrap
import tomllib

import pytest

from hadocs.application.operational_database import (
    OperationalDatabaseOperation,
    OperationalDatabasePersistenceState,
    initialize_operational_database_identity,
    persist_operational_database,
)
from hadocs.core.models import InstallationModel
from hadocs.hask_database import CredentialStoreSecretProvider


FROZEN_SCHEMA_SHA256 = (
    "623d0fed0f626eea698c87d62af611ce2c90b5d4ae470cb576def99ad39a9673"
)


def model(*, extra_entity: bool = False) -> InstallationModel:
    entities = {
        "sensor.private-person": "private-entity-one",
        "device_tracker.private-phone": "private-entity-two",
    }
    if extra_entity:
        entities["sensor.conflicting-count"] = "private-entity-three"
    return InstallationModel(
        areas={"private-bedroom": "private-area"},
        devices={
            "AA:BB:CC:DD:EE:FF": "private-device-one",
            "private-serial-number": "private-device-two",
        },
        entities=entities,
        integrations={"private-integration-id": "private-integration"},
        config={
            "ha_url": "https://192.0.2.10:8123",
            "token": "SUPER-SECRET-TOKEN",
            "project_name": "Private Person's Home",
        },
        states=[{"entity_id": "sensor.private-person", "state": "occupied"}],
        services=[],
        labels=[{"name": "Private Location"}],
        raw={
            "hask_matches": ["private-hask-match"],
            "findings": ["private-finding"],
            "recommendations": ["private-recommendation"],
            "health_score": 73,
            "hudd": {"device": "private-hudd-device"},
        },
    )


class MemorySecretBackend:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def write(self, handle: str, value: bytes) -> None:
        self.values[handle] = bytes(value)

    def read(self, handle: str) -> bytes | None:
        return self.values.get(handle)

    def delete(self, handle: str) -> bool:
        return self.values.pop(handle, None) is not None


def enabled_identity(
    path: Path,
) -> tuple[dict[str, object], CredentialStoreSecretProvider]:
    config: dict[str, object] = {
        "hask_database_enabled": True,
        "hask_database_path": str(path),
        "hask_database_installation_ref": "synthetic-installation-001",
    }
    provider = CredentialStoreSecretProvider(
        MemorySecretBackend(), secret_factory=lambda length: b"\xa5" * length
    )
    _, initialized = initialize_operational_database_identity(
        config,
        secret_provider=provider,
        uuid_factory=lambda: "123e4567-e89b-42d3-a456-426614174000",
    )
    return initialized, provider


def operation(suffix: str = "one") -> OperationalDatabaseOperation:
    return OperationalDatabaseOperation(
        identity=f"synthetic-operation-{suffix}",
        started_at=f"2026-07-27T12:0{0 if suffix == 'one' else 1}:00Z",
        terminal_at=f"2026-07-27T12:0{0 if suffix == 'one' else 1}:01Z",
    )


def table_counts(path: Path) -> dict[str, int]:
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "logical_installation",
                "installation_context",
                "scan_run",
                "observation",
                "scan_capability_outcome",
                "audit_record",
                "audit_subject_link",
                "audit_evidence_link",
                "entity",
                "relationship",
            )
        }
    finally:
        connection.close()


def test_disabled_mode_creates_no_database_and_imports_no_database_package(tmp_path):
    database_path = tmp_path / "must-not-exist.sqlite"
    source_root = Path(__file__).resolve().parents[1] / "src"
    script = textwrap.dedent(
        """
        import os
        from types import SimpleNamespace
        import sys
        from hadocs.application.operational_database import persist_operational_database

        target = os.environ["HADOCS_DISABLED_TEST_PATH"]
        model = SimpleNamespace(areas={}, devices={}, entities={}, integrations={})
        result = persist_operational_database(
            model,
            {"hask_database_enabled": False, "hask_database_path": target},
        )
        assert result.state.value == "disabled"
        assert "hadocs.hask_database" not in sys.modules
        assert not os.path.exists(target)
        """
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source_root)
    environment["HADOCS_DISABLED_TEST_PATH"] = str(database_path)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert not database_path.exists()


def test_disabled_adapter_preserves_the_normalized_and_analytical_model(tmp_path):
    installation = model()
    before = deepcopy(installation)
    result = persist_operational_database(
        installation,
        {
            "hask_database_enabled": False,
            "hask_database_path": str(tmp_path / "disabled.sqlite"),
        },
    )

    assert result.state is OperationalDatabasePersistenceState.DISABLED
    assert installation == before


def test_enabled_persistence_is_private_complete_and_restart_idempotent(tmp_path):
    from hadocs.hask_database import (
        HaskDatabaseConfig,
        HaskSQLiteConnectionFactory,
        schema_sha256,
    )

    path = tmp_path / "operational.sqlite"
    config, provider = enabled_identity(path)
    installation = model()
    before = deepcopy(installation)
    first = persist_operational_database(
        installation, config, operation=operation(), secret_provider=provider
    )
    first_counts = table_counts(path)
    replay = persist_operational_database(
        installation, config, operation=operation(), secret_provider=provider
    )

    assert first.state is OperationalDatabasePersistenceState.COMPLETED
    assert first.replay_state == "new_running"
    assert replay.replay_state == "existing_terminal"
    assert replay.installation_id == first.installation_id
    assert replay.context_id == first.context_id
    assert replay.scan_run_id == first.scan_run_id
    assert replay.observation_ids == first.observation_ids
    assert replay.capability_outcome_ids == first.capability_outcome_ids
    assert replay.completion_audit_id == first.completion_audit_id
    assert table_counts(path) == first_counts == {
        "logical_installation": 1,
        "installation_context": 1,
        "scan_run": 1,
        "observation": 1,
        "scan_capability_outcome": 1,
        "audit_record": 3,
        "audit_subject_link": 1,
        "audit_evidence_link": 1,
        "entity": 0,
        "relationship": 0,
    }
    assert installation == before

    with HaskSQLiteConnectionFactory(
        HaskDatabaseConfig(enabled=True, path=path, expected_user_version=8)
    ).connect() as connection:
        observation_row = connection.execute(
            "SELECT observation_key,normalized_payload_json,privacy_class,"
            "retention_policy FROM observation"
        ).fetchone()
        assert observation_row is not None
        assert observation_row[0] == "hadocs.normalized-counts.v1"
        payload = json.loads(observation_row[1])
        assert payload == {
            "areas": 1,
            "devices": 2,
            "entities": 2,
            "integrations": 1,
        }
        assert set(payload) == {"areas", "devices", "entities", "integrations"}
        assert all(type(value) is int for value in payload.values())
        assert observation_row[2:] == (
            "LOCAL_ONLY",
            "RETAIN_UNTIL_SUPERSEDED",
        )
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 8
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert schema_sha256(connection) == FROZEN_SCHEMA_SHA256

    serialized = path.read_bytes()
    for prohibited in (
        b"SUPER-SECRET-TOKEN",
        b"192.0.2.10",
        b"occupied",
        b"Private Person",
        b"Private Location",
        b"private-bedroom",
        b"private-serial-number",
        b"AA:BB:CC:DD:EE:FF",
        b"sensor.private-person",
        b"private-hask-match",
        b"private-finding",
        b"private-recommendation",
        b"private-hudd-device",
        b"health_score",
    ):
        assert prohibited not in serialized


def test_new_operation_creates_a_new_scan_without_new_installation(tmp_path):
    path = tmp_path / "new-operation.sqlite"
    config, provider = enabled_identity(path)
    first = persist_operational_database(
        model(), config, operation=operation("one"), secret_provider=provider
    )
    second = persist_operational_database(
        model(), config, operation=operation("two"), secret_provider=provider
    )

    assert second.scan_run_id != first.scan_run_id
    assert second.installation_id == first.installation_id
    assert second.context_id == first.context_id
    counts = table_counts(path)
    assert counts["logical_installation"] == 1
    assert counts["installation_context"] == 1
    assert counts["scan_run"] == 2
    assert counts["observation"] == 2
    assert counts["scan_capability_outcome"] == 2


def test_same_operation_with_changed_aggregate_intent_is_rejected(tmp_path):
    from hadocs.hask_database import IdempotencyConflictError

    path = tmp_path / "conflict.sqlite"
    config, provider = enabled_identity(path)
    persist_operational_database(
        model(), config, operation=operation(), secret_provider=provider
    )
    before = table_counts(path)

    with pytest.raises(IdempotencyConflictError, match="observation"):
        persist_operational_database(
            model(extra_entity=True),
            config,
            operation=operation(),
            secret_provider=provider,
        )

    assert table_counts(path) == before


def test_enabled_failure_is_visible_and_does_not_mutate_analytical_input(tmp_path):
    installation = model()
    before = deepcopy(installation)
    config, provider = enabled_identity(tmp_path)

    with pytest.raises(sqlite3.OperationalError):
        persist_operational_database(
            installation,
            config,
            operation=operation(),
            secret_provider=provider,
        )

    assert installation == before


def test_configuration_is_explicit_default_disabled_and_rejects_hudd(tmp_path):
    from hadocs.hask_database import HaskDatabaseApplicationConfig

    disabled = HaskDatabaseApplicationConfig.from_application_config({})
    assert disabled.database.enabled is False
    assert disabled.database.path is None
    assert disabled.installation_ref is None

    with pytest.raises(ValueError, match="explicit local database path"):
        HaskDatabaseApplicationConfig.from_application_config(
            {
                "hask_database_enabled": True,
                "hask_database_installation_ref": "synthetic-installation",
            }
        )
    with pytest.raises(ValueError, match="installation reference"):
        HaskDatabaseApplicationConfig.from_application_config(
            {
                "hask_database_enabled": True,
                "hask_database_path": str(tmp_path / "operational.sqlite"),
            }
        )
    with pytest.raises(ValueError, match="hudd.sqlite"):
        HaskDatabaseApplicationConfig.from_application_config(
            {
                "hask_database_enabled": True,
                "hask_database_path": str(tmp_path / "hudd.sqlite"),
                "hask_database_installation_ref": "synthetic-installation",
            }
        )


def test_generator_is_the_single_shared_cli_gui_and_web_boundary():
    root = Path(__file__).resolve().parents[1]
    generator = (root / "src/hadocs/reports/generator.py").read_text(encoding="utf-8")
    cli_application = (root / "src/hadocs/application/generate.py").read_text(
        encoding="utf-8"
    )
    gui = (root / "src/hadocs/gui/app.py").read_text(encoding="utf-8")
    web = (root / "src/hadocs/web/app.py").read_text(encoding="utf-8")

    assert generator.index("\n    model = build_model") < generator.index(
        "persist_operational_database(model, cfg)"
    ) < generator.index("\n    save_history_snapshot(")
    assert "generate_all(data, indexes, cfg)" in cli_application
    assert "generate_all(data, idx, cfg, log=self.log_msg)" in gui
    assert '"hadocs.cli.main"' in web
    assert '"generate"' in web


def test_packaging_declares_database_runtime_and_excludes_metadata_collector():
    root = Path(__file__).resolve().parents[1]
    configuration = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    setuptools = configuration["tool"]["setuptools"]

    assert "hadocs.hask_database*" not in setuptools["packages"]["find"]["exclude"]
    assert "hadocs.metadata_collector*" in setuptools["packages"]["find"]["exclude"]
    assert setuptools["package-data"]["hadocs.hask_database"] == ["sql/*.sql"]
    assert len(list((root / "src/hadocs/hask_database/sql").glob("*.sql"))) == 8
