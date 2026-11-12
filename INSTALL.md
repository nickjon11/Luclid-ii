# Luclid-ii v0.7.0 — Installation

Download the OS-specific release asset.

- **Windows (recommended):** Download `Luclid-ii-Setup-v0.7.0-Windows.exe` and run it **once**. It installs Luclid-ii to your user profile, creates a Start Menu shortcut, optionally creates a Desktop shortcut, and offers to launch the application. **Afterward, open Luclid-ii from Start or the Desktop; do not rerun Setup.** Windows Settings > Installed apps can uninstall it. A portable `luclid-ii-windows.zip` is also available, and `run_windows.bat` is retained for developers. Unsigned setup files may prompt SmartScreen; verify the release source before proceeding.
- **macOS (recommended):** Open `Luclid-ii-v0.7.0-macOS.dmg` **once** and drag `Luclid-ii.app` to Applications. Eject the disk image; launch Luclid-ii from Applications or Launchpad thereafter. A portable `luclid-ii-macos.zip` is also available. Unsigned builds may be blocked by Gatekeeper; code signing and notarization are not yet configured.
- **Linux (recommended for Debian/Ubuntu):** Install the `luclid-ii_0.7.0_amd64.deb` package once using your package manager; it registers an application-menu entry. Launch Luclid-ii from the application menu thereafter. Alternatively extract `luclid-ii-linux.zip` and run the portable `Luclid-ii/Luclid-ii`. Linux builds may require host GUI libraries.

Ollama and model downloads are optional and not bundled. Google OAuth requires valid credentials and appropriate permissions.

## Developer / backup launch

Install Python 3.12, then run `python -m pip install -e .` in a virtual environment. On Windows use `run_windows.bat` as a fallback. The Python GUI setup wizard is `Luclid-ii-Setup.pyw` (Windows) or `python3 Luclid-ii-Setup.py` (macOS).

## Release workflow

Push a `v0.7.0` tag to trigger GitHub Actions on Windows, macOS, and Linux. Native artifacts and a Debian package are attached to the GitHub release after successful builds. Version checks run before packaging.

## Installation versus everyday use

The setup executable is **not** the app launcher. Use it once to install, then run the installed native application directly from the OS shortcut. Re-running setup is only necessary for reinstalling or upgrading. The installer does not silently install Ollama or download AI models; those remain optional separate setup steps. Windows `.bat` is backup/developer-only.
