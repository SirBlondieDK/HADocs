from __future__ import annotations

from types import SimpleNamespace

import hadocs.gui.app as app_module
import hadocs.gui.dialogs.first_run as first_run_module
from hadocs.gui.app import App
from hadocs.gui.config_persistence import (
    CONFIG_CALLBACK_ERROR,
    CONFIG_SAVE_ERROR,
    try_config_callback,
    try_save_config,
)
from hadocs.gui.dialogs.first_run import FirstRunWizard


class _Widget:
    def __init__(self) -> None:
        self.calls = []

    def config(self, **values) -> None:
        self.calls.append(values)


def test_shared_save_error_is_secret_free() -> None:
    secret = "secret-token-that-must-not-leak"

    saved, message = try_save_config(
        {"token": secret},
        save=lambda config: (_ for _ in ()).throw(RuntimeError(secret)),
    )

    assert saved is False
    assert message == CONFIG_SAVE_ERROR
    assert secret not in message


def test_shared_callback_error_is_secret_free() -> None:
    secret = "secret-callback-value"

    notified, message = try_config_callback(
        {"token": secret},
        callback=lambda config: (_ for _ in ()).throw(RuntimeError(secret)),
    )

    assert notified is False
    assert message == CONFIG_CALLBACK_ERROR
    assert secret not in message


def test_first_run_save_failure_keeps_wizard_open(monkeypatch) -> None:
    wizard = object.__new__(FirstRunWizard)
    wizard.step = 2
    wizard.cfg = {}
    wizard.url_var = SimpleNamespace(get=lambda: "https://ha.example")
    wizard.token_var = SimpleNamespace(get=lambda: "wizard-secret")
    wizard.project_var = SimpleNamespace(get=lambda: "Home")
    events = []
    wizard.on_finish = lambda config: events.append("finish")
    wizard.destroy = lambda: events.append("destroy")
    dialogs = []
    monkeypatch.setattr(
        first_run_module,
        "save_config",
        lambda config: (_ for _ in ()).throw(PermissionError("wizard-secret")),
    )
    monkeypatch.setattr(
        first_run_module.messagebox,
        "showerror",
        lambda title, message, **kwargs: dialogs.append((title, message)),
    )

    FirstRunWizard.next(wizard)

    assert events == []
    assert dialogs == [("HADocs setup", CONFIG_SAVE_ERROR)]
    assert "wizard-secret" not in dialogs[0][1]


def test_first_run_callback_failure_is_visible_and_keeps_wizard_open(
    monkeypatch,
) -> None:
    wizard = object.__new__(FirstRunWizard)
    wizard.step = 2
    wizard.cfg = {}
    wizard.url_var = SimpleNamespace(get=lambda: "https://ha.example")
    wizard.token_var = SimpleNamespace(get=lambda: "wizard-secret")
    wizard.project_var = SimpleNamespace(get=lambda: "Home")
    events = []
    wizard.on_finish = lambda config: (_ for _ in ()).throw(
        RuntimeError("wizard-secret")
    )
    wizard.destroy = lambda: events.append("destroy")
    dialogs = []
    monkeypatch.setattr(first_run_module, "save_config", lambda config: None)
    monkeypatch.setattr(
        first_run_module.messagebox,
        "showerror",
        lambda title, message, **kwargs: dialogs.append((title, message)),
    )

    FirstRunWizard.next(wizard)

    assert events == []
    assert dialogs == [("HADocs setup", CONFIG_CALLBACK_ERROR)]
    assert "wizard-secret" not in dialogs[0][1]


def test_first_run_success_notifies_and_closes_exactly_once(monkeypatch) -> None:
    wizard = object.__new__(FirstRunWizard)
    wizard.step = 2
    wizard.cfg = {}
    wizard.url_var = SimpleNamespace(get=lambda: "https://ha.example")
    wizard.token_var = SimpleNamespace(get=lambda: "wizard-secret")
    wizard.project_var = SimpleNamespace(get=lambda: "Home")
    events = []
    wizard.on_finish = lambda config: events.append("finish")
    wizard.destroy = lambda: events.append("destroy")
    monkeypatch.setattr(first_run_module, "save_config", lambda config: None)

    FirstRunWizard.next(wizard)

    assert events == ["finish", "destroy"]


def test_scan_save_failure_does_not_start_worker_and_returns_idle(monkeypatch) -> None:
    app = object.__new__(App)
    app.status_label = _Widget()
    app.run_btn = _Widget()
    metrics = []
    app.metric_status = object()
    app.set_metric = lambda metric, value: metrics.append(value)
    app.get_cfg = lambda: {"token": "scan-secret", "output_dir": "output"}
    dialogs = []
    starts = []
    saved_configs = []

    def fail_save(config):
        saved_configs.append(dict(config))
        raise PermissionError("scan-secret")

    monkeypatch.setattr(app_module, "save_config", fail_save)
    monkeypatch.setattr(
        app_module.messagebox,
        "showerror",
        lambda title, message, **kwargs: dialogs.append((title, message)),
    )
    monkeypatch.setattr(
        app_module.threading,
        "Thread",
        lambda *args, **kwargs: SimpleNamespace(start=lambda: starts.append(True)),
    )

    App.run(app)

    assert starts == []
    assert metrics == ["Idle"]
    assert app.status_label.calls[-1] == {"text": "Ready"}
    assert app.run_btn.calls[-1]["state"] == "normal"
    assert dialogs == [("HADocs", CONFIG_SAVE_ERROR)]
    assert "scan-secret" not in dialogs[0][1]
    assert saved_configs == [{"output_dir": "output"}]


def test_doctor_save_failure_is_visible_and_stops_before_output(monkeypatch) -> None:
    app = object.__new__(App)
    app.get_cfg = lambda: {"token": "doctor-secret", "output_dir": "output"}
    app.log = SimpleNamespace(
        delete=lambda *args: (_ for _ in ()).throw(AssertionError("continued"))
    )
    dialogs = []
    saved_configs = []

    def fail_save(config):
        saved_configs.append(dict(config))
        raise PermissionError("doctor-secret")

    monkeypatch.setattr(app_module, "save_config", fail_save)
    monkeypatch.setattr(
        app_module.messagebox,
        "showerror",
        lambda title, message, **kwargs: dialogs.append((title, message)),
    )

    App.run_doctor(app)

    assert saved_configs == [{"output_dir": "output"}]
    assert dialogs == [("HADocs", CONFIG_SAVE_ERROR)]
    assert "doctor-secret" not in dialogs[0][1]
