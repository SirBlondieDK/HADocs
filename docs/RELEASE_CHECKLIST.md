# Release Checklist

Before every release:

## Code

- [ ] Tests pass
- [ ] GUI tested
- [ ] HTML dashboard tested
- [ ] Markdown output tested
- [ ] No secrets committed
- [ ] Generated output not committed
- [ ] `.pytest_tmp/` cleaned or ignored

## Documentation

- [ ] README updated
- [ ] CHANGELOG updated
- [ ] ROADMAP updated
- [ ] Docs updated
- [ ] Screenshots updated if UI changed
- [ ] TESTING.md updated if test workflow changed

## Security and privacy

- [ ] No new cloud calls
- [ ] No telemetry
- [ ] No AI provider calls
- [ ] Redaction checked if export changed
- [ ] Sensitive files ignored

## GitHub

- [ ] Commit created
- [ ] Push completed
- [ ] GitHub Actions green
- [ ] Release notes written
- [ ] Tag created
