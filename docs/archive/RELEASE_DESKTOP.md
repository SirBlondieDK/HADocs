# Desktop Release Checklist

- [ ] Run `py -3.14 -m pytest`
- [ ] Run `py -3.14 main.py`
- [ ] Update README
- [ ] Update CHANGELOG
- [ ] Update `src/hadocs/version.py`
- [ ] Run `powershell -ExecutionPolicy Bypass -File installer/build_windows.ps1`
- [ ] Test `dist/HADocs/HADocs.exe`
- [ ] Compile `installer/HADocs.iss`
- [ ] Upload installer to GitHub Release
