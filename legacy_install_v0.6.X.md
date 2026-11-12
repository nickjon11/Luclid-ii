# Legacy installation guides — v0.6.x

Historical instructions, retained for reference. For v0.7.0 use INSTALL.md.


---

## INSTALL_v0.6.4.md

# Installation — v0.6.4

Windows: install Python 3.11+ with Tk support, then double-click `Launch Luclid-ii.bat` or run `py -3 "Luclid-ii-Setup.py"`.

macOS: install Python 3.11+ with Tk support; open Terminal in the extracted folder and run `python3 "Luclid-ii-Setup.py"`, or `chmod +x "Launch Luclid-ii.command" && ./"Launch Luclid-ii.command"`.

Linux (terminal only): `chmod +x launch-linux.sh && ./launch-linux.sh`. For Debian package building, see `DEPLOYMENT_v0.6.3.md`.

The setup wizard installs Luclid-ii's Python dependencies into a local virtual environment. Ollama installation is opt-in: it opens the official download page, not an unverified executable. Optional model downloads require a working Ollama command. Existing/remote Ollama URL is saved to `~/.luclid-ii/installer.json` but is not yet wired into all application API calls.

Note: A `.py` file may not be double-clickable on every Mac or Windows Python installation; the included `.command` / `.bat` entry points are the reliable alternatives.


---

## INSTALL_v0.6.5.md

# Luclid-ii v0.6.5 Setup

Windows (PowerShell): `py -3 "Luclid-ii-Setup.py"`

macOS (Terminal): `python3 "Luclid-ii-Setup.py"`

Linux remains terminal-only: `./launch-linux.sh` or build the `.deb` using the packaging scripts.

Choose Automatic Setup to detect/install Ollama and download the model, Connect to Existing Ollama Server to save a URL, or Save for Later to defer AI setup. The model can require several GB of space. The setup log displays installation command output.


---

## INSTALL_v0.6.6.md

# Luclid-ii v0.6.6 setup

Windows PowerShell: `py -3 "Luclid-ii-Setup.py"`

macOS Terminal: `python3 "Luclid-ii-Setup.py"`

Linux remains terminal-only: `./launch-linux.sh`

Python 3.11+ with Tkinter is required for the GUI wizard. Choose Automatic Setup, Connect to Existing Ollama Server, or Save for Later. Model downloads can require several gigabytes.

