# HADocs v1.0.0 draft release notes

> [!NOTE]
> Internal release draft. Do not publish it until the release scope has been verified. Use the public [roadmap](../../../ROADMAP.md) for committed project direction.

HADocs is a local-first **Home Assistant Analysis Platform** for understanding installation health, investigating root causes, and prioritizing improvements.

## Highlights

- Modern Windows desktop GUI
- Dashboard Engine with Health Score and Potential Health Score
- Root Cause Analysis
- Smart Recommendations
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
- User-controlled Knowledge Pack exports only

## Recommended workflow

1. Start HADocs.
2. Enter Home Assistant URL.
3. Paste Long-Lived Access Token.
4. Run an analysis from **Overview**.
5. Review the Dashboard Engine or Explorer.

## Release checklist

- [ ] `py -3.14 -m pytest`
- [ ] Build Windows executable
- [ ] Verify GUI opens
- [ ] Verify Dashboard opens
- [ ] Verify Explorer opens
- [ ] Verify Doctor passes
- [ ] Complete repository cleanup
- [ ] Tag `v1.0.0`
- [ ] Create GitHub Release
- [ ] Upload Windows executable
