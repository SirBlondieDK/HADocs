from __future__ import annotations

import re
from pathlib import Path

CONFIG = Path("src/hadocs/utils/config.py")
IMPORT_LINE = "from src.hadocs.security.credential_store import inject_token_into_runtime_config, migrate_plaintext_token_from_config\n"


def patch_config_py() -> None:
    if not CONFIG.exists():
        raise SystemExit("Run from the HADocs repository root. Missing src/hadocs/utils/config.py")

    text = CONFIG.read_text(encoding="utf-8")

    if "src.hadocs.security.credential_store" not in text:
        lines = text.splitlines(True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, IMPORT_LINE)
        text = "".join(lines)

    text = patch_load_config(text)
    text = patch_save_config(text)

    CONFIG.write_text(text, encoding="utf-8")
    print("Patched src/hadocs/utils/config.py")


def patch_load_config(text: str) -> str:
    if "inject_token_into_runtime_config(" in text:
        return text

    match = re.search(r"^def load_config\([^)]*\):\n", text, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("Could not find load_config()")

    start = match.end()
    next_def = text.find("\ndef ", start)
    end = next_def if next_def != -1 else len(text)
    body = text[start:end]

    body = re.sub(
        r"(?m)^([ \t]+)return ([A-Za-z_][A-Za-z0-9_]*)\s*$",
        r"\1return inject_token_into_runtime_config(\2)",
        body,
    )

    return text[:start] + body + text[end:]


def patch_save_config(text: str) -> str:
    if "migrate_plaintext_token_from_config(" in text:
        return text

    match = re.search(r"^def save_config\(([^,)]+)", text, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("Could not find save_config(...)")

    param = match.group(1).strip()
    insert_at = text.find("\n", match.end()) + 1

    injection = (
        f"    {param} = migrate_plaintext_token_from_config({param})\n"
        f"    {param} = dict({param} or {{}})\n"
    )

    return text[:insert_at] + injection + text[insert_at:]


def main() -> None:
    patch_config_py()
    print("")
    print("Now run:")
    print("  py -3.14 -m pytest")
    print("")
    print("Then open HADocs and save settings once.")
    print("After that, config.json should no longer contain token.")
    print("")
    print("Commit:")
    print("  git add src/hadocs/security/credential_store.py src/hadocs/security/__init__.py src/hadocs/utils/config.py docs/TOKEN_SECURITY_V101.md tests/test_credential_store.py tools/apply_v101_windows_credentials.py")
    print('  git commit -m "Store Home Assistant token in Windows Credential Manager"')
    print("  git push")


if __name__ == "__main__":
    main()
