# Packaging and release engineering

## PyInstaller (sketch)

```bash
pip install pyinstaller
pyinstaller --name crawlix \
  --windowed \
  --paths src \
  -m crawlix.main
```

- **Playwright:** bundle browsers or document first-run `playwright install`; pin browser revisions in release notes.
- **Windows:** plan **Authenticode** signing for public binaries; CI should upload signed `.exe` when secrets are configured.
- **macOS / Linux:** unsigned early releases are acceptable with honest README warnings; **notarization** is a later milestone.

## Update channel

Binary updates: GitHub Releases assets + checksum sidecar; verify with `crawlix.services.updater.github_releases.verify_sha256` before launching the installer.

## SBOM

Generate a software bill of materials per release as a stretch goal (`pip freeze` / CycloneDX) and attach to Releases.
