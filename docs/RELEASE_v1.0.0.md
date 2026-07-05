# HADocs v1.0.0

HADocs is now a full local-first desktop tool for Home Assistant documentation and intelligence.

## Highlights

- Modern Windows desktop GUI
- Smart Dashboard with Health Score
- Root Cause Analysis
- Top Recommendations
- HTML Dashboard
- HTML Explorer
- Markdown documentation
- Knowledge Pack export
- Redacted Knowledge Pack export
- Doctor diagnostics
- Windows executable build support
- Local-first and privacy-first operation

## Privacy

HADocs runs locally.

- No telemetry
- No cloud upload
- No AI service calls
- AI-compatible export files only

## Recommended workflow

1. Start HADocs.
2. Enter Home Assistant URL.
3. Paste Long-Lived Access Token.
4. Click **Scan Home Assistant**.
5. Open Dashboard or Explorer.

## Release checklist

- [ ] `py -3.14 -m pytest`
- [ ] Build Windows executable
- [ ] Verify GUI opens
- [ ] Verify Dashboard opens
- [ ] Verify Explorer opens
- [ ] Verify Doctor passes
- [ ] Commit cleanup
- [ ] Tag `v1.0.0`
- [ ] Create GitHub Release
- [ ] Upload Windows executable
