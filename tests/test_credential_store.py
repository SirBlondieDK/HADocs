def test_credential_store_exports():
    from src.hadocs.security.credential_store import (
        CREDENTIAL_TARGET,
        inject_token_into_runtime_config,
        migrate_plaintext_token_from_config,
    )

    assert CREDENTIAL_TARGET == "HADocs/HomeAssistantToken"
    assert callable(inject_token_into_runtime_config)
    assert callable(migrate_plaintext_token_from_config)


def test_migrate_plaintext_token_removes_token(monkeypatch):
    from src.hadocs.security import credential_store

    stored = {}

    def fake_store(token: str) -> bool:
        stored["token"] = token
        return True

    monkeypatch.setattr(credential_store, "set_home_assistant_token", fake_store)

    clean = credential_store.migrate_plaintext_token_from_config(
        {"ha_url": "http://ha.local:8123", "token": "secret-token"}
    )

    assert clean == {"ha_url": "http://ha.local:8123"}
    assert stored["token"] == "secret-token"


def test_inject_token_into_runtime_config(monkeypatch):
    from src.hadocs.security import credential_store

    monkeypatch.setattr(credential_store, "get_home_assistant_token", lambda: "secure-token")

    runtime = credential_store.inject_token_into_runtime_config({"ha_url": "http://ha.local:8123"})

    assert runtime["ha_url"] == "http://ha.local:8123"
    assert runtime["token"] == "secure-token"
