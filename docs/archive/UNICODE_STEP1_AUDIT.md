# Unicode Step 1: Audit

This step only adds an audit tool.

It does not change runtime behavior.

## Run

```powershell
py -3.14 tools/audit_unicode_encoding.py
notepad docs\UNICODE_ENCODING_AUDIT.md
py -3.14 -m pytest
```

## Goal

Find where HADocs may still write or display mojibake such as:

```text
ÔÇö
K├©kken
Sovev├ªrelse
h├©jttaler
```

before making any code changes.
