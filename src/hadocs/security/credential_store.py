"""Secure token storage for HADocs.

On Windows, Home Assistant tokens are stored in Windows Credential Manager
using DPAPI-backed generic credentials. The token should not be stored in
config.json.
"""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

CREDENTIAL_TARGET = "HADocs/HomeAssistantToken"
CREDENTIAL_USERNAME = "HomeAssistantToken"

CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2


class CredentialStoreError(RuntimeError):
    pass


def is_windows_credential_manager_available() -> bool:
    return os.name == "nt"


if os.name == "nt":
    class FILETIME(ctypes.Structure):
        _fields_ = [
            ("dwLowDateTime", wintypes.DWORD),
            ("dwHighDateTime", wintypes.DWORD),
        ]


    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]


    PCREDENTIALW = ctypes.POINTER(CREDENTIALW)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

    CredWriteW = advapi32.CredWriteW
    CredWriteW.argtypes = [PCREDENTIALW, wintypes.DWORD]
    CredWriteW.restype = wintypes.BOOL

    CredReadW = advapi32.CredReadW
    CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(PCREDENTIALW)]
    CredReadW.restype = wintypes.BOOL

    CredDeleteW = advapi32.CredDeleteW
    CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    CredDeleteW.restype = wintypes.BOOL

    CredFree = advapi32.CredFree
    CredFree.argtypes = [ctypes.c_void_p]
    CredFree.restype = None


def _raise_last_error(action: str) -> None:
    error = ctypes.get_last_error()
    raise CredentialStoreError(f"Windows Credential Manager failed during {action}. WinError={error}")


def set_home_assistant_token(token: str) -> bool:
    if not token:
        return False

    if not is_windows_credential_manager_available():
        return False

    encoded = token.encode("utf-16-le")
    blob = ctypes.create_string_buffer(encoded)

    credential = CREDENTIALW()
    credential.Flags = 0
    credential.Type = CRED_TYPE_GENERIC
    credential.TargetName = CREDENTIAL_TARGET
    credential.Comment = "HADocs Home Assistant Long-Lived Access Token"
    credential.CredentialBlobSize = len(encoded)
    credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(wintypes.BYTE))
    credential.Persist = CRED_PERSIST_LOCAL_MACHINE
    credential.AttributeCount = 0
    credential.Attributes = None
    credential.TargetAlias = None
    credential.UserName = CREDENTIAL_USERNAME

    if not CredWriteW(ctypes.byref(credential), 0):
        _raise_last_error("write")

    return True


def get_home_assistant_token() -> str | None:
    if not is_windows_credential_manager_available():
        return None

    credential_ptr = PCREDENTIALW()
    if not CredReadW(CREDENTIAL_TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(credential_ptr)):
        return None

    try:
        credential = credential_ptr.contents
        if not credential.CredentialBlob or credential.CredentialBlobSize == 0:
            return None

        raw = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        return raw.decode("utf-16-le")
    finally:
        CredFree(credential_ptr)


def delete_home_assistant_token() -> bool:
    if not is_windows_credential_manager_available():
        return False
    return bool(CredDeleteW(CREDENTIAL_TARGET, CRED_TYPE_GENERIC, 0))


def has_home_assistant_token() -> bool:
    return bool(get_home_assistant_token())


def migrate_plaintext_token_from_config(config: dict) -> dict:
    clean = dict(config or {})
    token = clean.pop("token", None) or clean.pop("ha_token", None)

    if token:
        set_home_assistant_token(str(token))

    return clean


def inject_token_into_runtime_config(config: dict) -> dict:
    runtime = dict(config or {})
    token = get_home_assistant_token()
    if token:
        runtime["token"] = token
    return runtime
