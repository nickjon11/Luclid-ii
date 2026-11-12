# Luclid-ii v0.6.3 deployment

## Source ZIP (one-step startup)

- Windows: double-click `Launch Luclid-ii.bat` (Python 3.11+ must already be installed).
- macOS: open `Launch Luclid-ii.command` (Python 3.11+ required; macOS may require granting execute permission to downloaded scripts).
- Debian/Linux: run `./launch-linux.sh` (requires Python 3.11+, python3-venv, internet for first-run Python dependencies, and Qt runtime libraries).

First run installs the project in `.venv` and starts the GUI. Future runs skip installation unless VERSION changes. Playwright Chromium is optional and is **not** automatically downloaded; browser-based job features may require `python -m playwright install chromium` inside the venv.

## Native builds

On each target OS, run:

```sh
python -m pip install -e . pyinstaller
python packaging/build_native.py
```

The application appears under `dist/Luclid-ii/`. Native builds must be made and tested separately on Windows, macOS, and Linux. On Linux with dpkg tools:

```sh
python packaging/linux/build_deb.py
sudo apt install ./luclid-ii_0.6.3_amd64.deb  # replace architecture with your build output
```

GitHub Actions workflow `.github/workflows/build-releases.yml` creates native artifacts on tagged releases or manual runs. Artifacts appear in the workflow run; **publishing a signed GitHub APT repository is a separate step**. Until it is set up, `sudo apt install luclid-ii` without a local .deb or configured repo will not work.

## Security and requirements

Ollama must be installed and configured separately. The launcher does not automatically download or start AI models. Do not run the source launcher with sudo. Review GitHub Actions artifacts on actual machines before a public release. macOS Gatekeeper and Windows SmartScreen may warn about unsigned binaries. GitHub workflow currently builds Intel/AMD runner architectures only; ARM and Apple Silicon builds require their own runners and tests. The Debian control file uses a placeholder maintainer address; replace it before publishing publicly.
