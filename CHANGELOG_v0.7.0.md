# Luclid-ii v0.7.0 — Native Release Candidate

- Centralized application and installer version in `VERSION` / `local_muse.version`.
- Consolidated historical v0.6.x changelog and installation documentation.
- Native GUI builds for Windows, macOS, and Linux via GitHub Actions; no console window on Windows.
- Windows `.bat` launcher retained as a manual fallback for source installations.
- v0.6.25 v3 user interface and features carried forward without functional redesign.

**Status:** Release candidate; native binaries must be built and smoke-tested on their target platforms.

### Native one-time installation
- Windows: GitHub Actions builds a versioned Inno Setup `.exe` that installs the compiled application, creates Start Menu and optional Desktop shortcuts, and supports uninstallation. The installed application launches without rerunning setup.
- macOS: GitHub Actions creates a drag-and-drop `.dmg` containing `Luclid-ii.app` and an Applications shortcut.
- Debian Linux: existing `.deb` installs an application-menu launcher; portable archives remain available.
- `.bat` launcher remains a backup for source/developer installations only.
