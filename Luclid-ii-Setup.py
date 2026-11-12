#!/usr/bin/env python3
"""Luclid-ii setup wizard: Windows 98-inspired / classic Mac-inspired."""
import json
import re
import urllib.request
import urllib.error
import time
import os
import platform
import queue
import shutil
import subprocess
import sys
import threading
import venv
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def release_version():
    version_file = ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    from local_muse.version import APP_VERSION
    return APP_VERSION

APP_VERSION = release_version()
CONFIG = Path.home() / ".luclid-ii" / "installer.json"
SYSTEM = platform.system()
if SYSTEM == "Linux":
    raise SystemExit("Linux uses terminal-only installation: run ./launch-linux.sh or build a .deb package.")
if SYSTEM not in ("Windows", "Darwin"):
    raise SystemExit("Supported GUI setup platforms: Windows and macOS.")
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required. Install Python, then rerun this file.")
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    raise SystemExit("Python Tk support is missing. Install a Python distribution with Tkinter, then retry.")

MAC = SYSTEM == "Darwin"
BG = "#dedede" if MAC else "#c0c0c0"
ACCENT = "#5555aa" if MAC else "#51218a"
DARK = "#242035"

def discover_python():
    """Prefer a well-supported interpreter, independent of the wizard's Python."""
    candidates = []
    for version in ("3.13", "3.12", "3.14", "3.11"):
        if SYSTEM == "Windows":
            candidates.append((["py", f"-{version}"], version))
        else:
            candidates.append(([f"python{version}"], version))
    for command, version in candidates:
        try:
            result = subprocess.run(command + ["-c", "import sys; print(sys.executable)"],
                                    capture_output=True, text=True, timeout=8)
            if result.returncode == 0:
                executable = result.stdout.strip().splitlines()[-1]
                if executable and Path(executable).is_file():
                    return executable, version
        except (OSError, subprocess.TimeoutExpired, IndexError):
            pass
    # Core application can still use a newer interpreter; optional voice cannot.
    return sys.executable, f"{sys.version_info.major}.{sys.version_info.minor}"


def environment_python_version(python_path):
    try:
        result = subprocess.run([str(python_path), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                                capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


class Wizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Luclid-ii Setup v{APP_VERSION}")
        self.root.geometry("820x550")
        self.root.minsize(760, 550)
        self.root.maxsize(1100, 850)
        self.root.configure(bg=BG)
        self.icon_image = tk.PhotoImage(file=str(ROOT / "src" / "local_muse" / "assets" / "lii_icon.png"))
        self.icon_small = self.icon_image.subsample(16, 16)
        self.icon_medium = self.icon_image.subsample(8, 8)
        self.root.iconphoto(True, self.icon_small)
        if SYSTEM == "Windows":
            try: self.root.iconbitmap(str(ROOT / "src" / "local_muse" / "assets" / "lii_icon.ico"))
            except tk.TclError: pass
        self.step = 0
        self.events = queue.Queue()
        self.running = False
        self.install_warnings = []
        self.ai_mode = tk.StringVar(value="automatic")
        self.server = tk.StringVar(value="http://127.0.0.1:11434")
        self.launch_after = tk.BooleanVar(value=True)
        self.model = tk.StringVar(value="qwen2.5:7b")
        self.extra_qwen3 = tk.BooleanVar(value=False)
        self.extra_qwen35 = tk.BooleanVar(value=False)
        self.extra_deepseek = tk.BooleanVar(value=False)
        self.voice_addon = tk.BooleanVar(value=False)
        self.selected_python, self.selected_python_version = discover_python()
        self.detected_models = set()
        self.scan_message = tk.StringVar(value="Not scanned yet")
        self.status = tk.StringVar(value="Ready")
        self.steps = ["Welcome", "System Check", "AI Setup", "Ready to Install", "Installing", "Finish"]
        # The original 512px logo must never determine Tk geometry.
        # Mac gets a subtle brushed-metal title strip; Windows gets a Win98 purple strip.
        self.titlebar = tk.Frame(self.root, bg="#c9c9ce" if MAC else ACCENT, height=64 if MAC else 62)
        self.titlebar.pack(fill="x")
        self.titlebar.pack_propagate(False)
        if MAC:
            strip = tk.Canvas(self.titlebar, height=62, highlightthickness=0, bd=0)
            strip.pack(fill="both", expand=True)
            for y in range(62):
                shade = 231 - int(y * .30) + (1 if y % 3 == 0 else 0)
                shade = max(180, min(240, shade))
                strip.create_line(0,y,1600,y,fill=f"#{shade:02x}{shade:02x}{min(255,shade+3):02x}")
            strip.create_image(22,31,image=self.icon_small,anchor="w")
            strip.create_text(67,31,text=f"Luclid-ii Setup v{APP_VERSION}",anchor="w",font=("Helvetica",17,"bold"),fill="#242035")
        else:
            tk.Label(self.titlebar,image=self.icon_small,bg=ACCENT).pack(side="left",padx=(16,8),pady=12)
            tk.Label(self.titlebar,text=f"Luclid-ii Setup v{APP_VERSION}",bg=ACCENT,fg="white",font=("Arial",17,"bold")).pack(side="left")
        # Reserve footer space BEFORE packing the expandable content. Tk's packer
        # otherwise allows long pages to consume the footer's available height.
        self.footer = tk.Frame(self.root, bg=BG, height=55)
        self.footer.pack(side="bottom", fill="x", padx=15, pady=(0, 12))
        self.footer.pack_propagate(False)
        self.body = tk.Frame(self.root, bg=BG)
        self.body.pack(side="top", fill="both", expand=True, padx=14, pady=12)
        self.sidebar = tk.Frame(self.body, bg="#d3d2d8" if MAC else "#e1d5ef", width=170, relief="groove" if not MAC else "flat", bd=2 if not MAC else 1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        # Scroll only the center page; the sidebar, header and navigation stay fixed.
        self.page_host = tk.Frame(self.body, bg=BG)
        self.page_host.pack(side="left", fill="both", expand=True, padx=(17, 0))
        self.page_canvas = tk.Canvas(self.page_host, bg=BG, bd=0, highlightthickness=0)
        self.page_scroll = ttk.Scrollbar(self.page_host, orient="vertical", command=self.page_canvas.yview)
        self.page_canvas.configure(yscrollcommand=self.page_scroll.set)
        self.page_scroll.pack(side="right", fill="y")
        self.page_canvas.pack(side="left", fill="both", expand=True)
        self.main = tk.Frame(self.page_canvas, bg=BG)
        self.page_window = self.page_canvas.create_window((0, 0), window=self.main, anchor="nw")
        self.main.bind("<Configure>", lambda event: self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all")))
        self.page_canvas.bind("<Configure>", lambda event: self.page_canvas.itemconfigure(self.page_window, width=event.width))
        self.root.bind_all("<MouseWheel>", self._wheel, add="+")
        self.root.bind_all("<Button-4>", self._wheel, add="+")
        self.root.bind_all("<Button-5>", self._wheel, add="+")
        self.back = tk.Button(self.footer, text="Go Back" if MAC else "< Back", width=11, command=self.go_back)
        self.next = tk.Button(self.footer, text="Continue" if MAC else "Next >", width=13, command=self.go_next, default="active")
        self.cancel = tk.Button(self.footer, text="Cancel", width=10, command=self.close)
        self.cancel.pack(side="right", padx=(8,0), pady=9)
        self.next.pack(side="right", padx=4, pady=9)
        self.back.pack(side="right", padx=4, pady=9)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self.poll)
        self.draw()

    def _wheel(self, event):
        # Avoid hijacking scrolling inside the installation log.
        if self.step == 4:
            return
        if getattr(event, "num", None) == 4:
            amount = -1
        elif getattr(event, "num", None) == 5:
            amount = 1
        else:
            amount = -int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
        self.page_canvas.yview_scroll(amount, "units")

    def scan_models(self):
        url = self.server.get().strip() if self.ai_mode.get() == "connect" else "http://127.0.0.1:11434"
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/api/tags", timeout=4) as response:
                data = json.load(response)
            self.detected_models = {item.get("name", "") for item in data.get("models", [])}
            self.scan_message.set(f"Detected {len(self.detected_models)} installed model(s) on {url}")
        except (OSError, ValueError, urllib.error.URLError) as exc:
            self.detected_models = set()
            self.scan_message.set("Ollama not reachable; model scan unavailable")
        self.draw()

    def model_installed(self, name):
        return name in self.detected_models or any(m.split(":")[0] == name.split(":")[0] and name.endswith(":latest") for m in self.detected_models)

    def clear(self, frame):
        for child in frame.winfo_children(): child.destroy()

    def label(self, text, font=None, fg=DARK, **kw):
        w=tk.Label(self.main, text=text, bg=BG, fg=fg, justify="left", anchor="w", wraplength=510, font=font or ("Helvetica" if MAC else "Arial", 11), **kw)
        w.pack(fill="x", pady=6)
        return w

    def draw(self):
        self.clear(self.main); self.clear(self.sidebar)
        self.page_canvas.yview_moveto(0)
        tk.Label(self.sidebar, image=self.icon_medium, bg=self.sidebar["bg"]).pack(pady=(20,10))
        tk.Label(self.sidebar, text="Luclid-ii", bg=self.sidebar["bg"], fg=DARK, font=("Arial", 15, "bold")).pack(pady=(0,14))
        for i,name in enumerate(self.steps):
            tk.Label(self.sidebar, text=("● " if i==self.step else "○ ")+name, anchor="w", bg=self.sidebar["bg"], fg=ACCENT if i==self.step else "#555", font=("Arial", 10, "bold" if i==self.step else "normal"), padx=12).pack(fill="x", pady=6)
        self.back.config(state="normal" if self.step in (1,2,3) else "disabled")
        self.next.config(state="disabled" if self.step==4 else "normal", text=("Finish" if self.step==5 else "Install" if self.step==3 else "Continue" if MAC else "Next >"))
        if self.step==0:
            self.label("Welcome to Luclid-ii Setup", ("Arial", 20, "bold"))
            self.label("This wizard will prepare Luclid-ii for your computer. The same Python installer works on Windows and macOS.")
            self.label("Setup detects your operating system and prepares the application for it.")
            self.label("Ollama and the AI model are optional. Nothing system-wide is installed without your choice.")
        elif self.step==1:
            self.label("System Detection", ("Arial", 20, "bold"))
            values=[("Operating system",platform.platform()),("Architecture",platform.machine()),("Python",sys.version.split()[0]),("Ollama executable",shutil.which("ollama") or "Not found")]
            for k,v in values: self.label(f"{k}:  {v}")
        elif self.step==2:
            self.label("AI Setup", ("Arial", 20, "bold"))
            self.label("Choose how Luclid-ii should access its AI assistant.")
            choices = [
                ("automatic", "Automatic Setup (Recommended)", "Detect Ollama, install it if missing, and offer to download the AI model."),
                ("connect", "Connect to Existing Ollama Server", "Use an Ollama server running locally or on another computer."),
                ("later", "Save for Later", "Install Luclid-ii without configuring AI right now."),
            ]
            for val, title, desc in choices:
                tk.Radiobutton(self.main, text=title, value=val, variable=self.ai_mode,
                               command=self.draw, bg=BG, fg=DARK, anchor="w",
                               font=("Arial", 11, "bold"), selectcolor=BG).pack(fill="x", pady=(9, 0))
                self.label(desc, font=("Arial", 9), fg="#444444")
            if self.ai_mode.get() != "later":
                self.label("Installed Ollama models", ("Arial", 13, "bold"))
                self.label(self.scan_message.get(), font=("Arial", 9))
                tk.Button(self.main, text="Rescan Models", command=self.scan_models).pack(anchor="w", pady=4)
                for name in sorted(self.detected_models):
                    self.label("✓ " + name, font=("Arial", 9), fg="#225d35")
            if self.ai_mode.get() == "connect":
                self.label("Ollama server URL:")
                tk.Entry(self.main, textvariable=self.server).pack(fill="x")
                self.label("Model name:")
                tk.Entry(self.main, textvariable=self.model).pack(fill="x")
        elif self.step==3:
            self.label("Ready to Install", ("Arial", 20, "bold"))
            self.label(f"Platform: {SYSTEM} ({platform.machine()})")
            self.label("Python environment:")
            self.label(str(ROOT / ".venv"), font=("Arial", 9))
            self.label(f"Environment Python: {self.selected_python_version} ({self.selected_python})", font=("Arial", 9))
            if self.selected_python_version == "3.15":
                self.label("Python 3.15 detected: offline voice recognition requires Python 3.11–3.14. Install Python 3.13 to enable it.", fg="#a44b00")
            self.label(f"AI setup: {self.ai_mode.get().replace('_', ' ').title()}")
            if self.ai_mode.get() == "connect": self.label(f"Ollama server: {self.server.get()}")
            if self.ai_mode.get() == "automatic": self.label("Ollama installation and model download may require permission and several GB of disk space.")
            if self.ai_mode.get() == "automatic":
                self.label("Optional AI Model Add-ons", ("Arial", 14, "bold"))
                self.label("Keep Qwen2.5 7B as the default. Select any additional models to download:", font=("Arial", 10))
                tk.Checkbutton(self.main, text="Qwen3 8B (qwen3:8b) — about 5.2 GB" + (" [Installed]" if self.model_installed("qwen3:8b") else ""), variable=self.extra_qwen3,
                               bg=BG, fg=DARK, anchor="w", selectcolor=BG).pack(fill="x", pady=3)
                tk.Checkbutton(self.main, text="Qwen3.5 9B (qwen3.5:9b) — vision / screenshots, approx. 6–8 GB" + (" [Installed]" if self.model_installed("qwen3.5:9b") else ""), variable=self.extra_qwen35,
                               bg=BG, fg=DARK, anchor="w", selectcolor=BG).pack(fill="x", pady=3)
                tk.Checkbutton(self.main, text="DeepSeek-R1 8B (deepseek-r1:8b) — about 5.2 GB" + (" [Installed]" if self.model_installed("deepseek-r1:8b") else ""), variable=self.extra_deepseek,
                               bg=BG, fg=DARK, anchor="w", selectcolor=BG).pack(fill="x", pady=3)
                self.label("EXPERIMENTAL: DeepSeek-R1 may produce repeated text, timeouts, or generation failures on some systems.", font=("Arial", 9), fg="#8a4b00")
                self.label("Selected add-ons download only if Ollama is available. They won't replace your default model.", font=("Arial", 9))
            self.label("Optional Add-ons", ("Arial", 14, "bold"))
            tk.Checkbutton(self.main, text="Offline Voice Recognition (microphone + Whisper)", variable=self.voice_addon,
                           bg=BG, fg=DARK, anchor="w", selectcolor=BG).pack(fill="x", pady=4)
            self.label("Adds sounddevice, faster-whisper and numpy. The Whisper Tiny transcription model is downloaded during setup so voice works offline afterward.", font=("Arial", 9))
            self.label("Click Install to create a private Python environment and install Luclid-ii's dependencies.")
            self.label("An internet connection is required for first-time Python dependency installation.",fg=ACCENT)
        elif self.step==4:
            self.label("Installing Luclid-ii", ("Arial", 20, "bold"))
            self.label("Please wait. This may take several minutes on the first run.")
            self.progress=ttk.Progressbar(self.main,mode="indeterminate"); self.progress.pack(fill="x",pady=12); self.progress.start(15)
            tk.Label(self.main,textvariable=self.status,bg=BG,fg=ACCENT,anchor="w",wraplength=460).pack(fill="x")
            log_frame = tk.Frame(self.main, bg="#000000", bd=2, relief="sunken")
            log_frame.pack(fill="both", expand=True, pady=(12, 0))
            self.log_widget = tk.Text(log_frame, bg="#000000", fg="#00ff39", insertbackground="#00ff39",
                                      font=("Courier New", 10), state="disabled", wrap="word", relief="flat")
            scroll = tk.Scrollbar(log_frame, command=self.log_widget.yview)
            self.log_widget.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            self.log_widget.pack(side="left", fill="both", expand=True)
            self.append_log(f"Luclid-ii Setup v{APP_VERSION}\nPreparing installation...\n")
        elif self.step==5:
            self.label("Installation Complete", ("Arial", 20, "bold"))
            self.label("Luclid-ii installation has completed.")
            self.label("If Ollama is unavailable, you can still launch the app and configure AI later.")
            tk.Checkbutton(self.main,text="Launch Luclid-ii now",variable=self.launch_after,bg=BG).pack(anchor="w",pady=12)

    def go_back(self):
        if self.step in (1,2,3): self.step-=1;self.draw()
    def go_next(self):
        if self.step==5:
            if self.launch_after.get():
                py=ROOT/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
                try: subprocess.Popen([str(py.with_name('pythonw.exe') if SYSTEM=='Windows' and py.with_name('pythonw.exe').exists() else py),'-m','local_muse.app'],cwd=str(ROOT),**({'creationflags':subprocess.CREATE_NO_WINDOW} if SYSTEM=='Windows' else {}))
                except OSError as exc: messagebox.showerror("Launch failed",str(exc))
            self.root.destroy();return
        if self.step==3:
            self.step=4;self.running=True;self.draw()
            threading.Thread(target=self.install,daemon=True).start();return
        self.step+=1;self.draw()
    def append_log(self, line):
        if not hasattr(self, "log_widget") or not self.log_widget.winfo_exists(): return
        self.log_widget.config(state="normal")
        self.log_widget.insert("end", line.rstrip("\n") + "\n")
        self.log_widget.see("end")
        self.log_widget.config(state="disabled")

    def run_logged(self, command, *, check=True):
        self.events.put(("log", "$ " + " ".join(map(str, command))))
        proc = subprocess.Popen(command, cwd=str(ROOT), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1, **({"creationflags":subprocess.CREATE_NO_WINDOW} if SYSTEM=="Windows" else {}))
        from collections import deque
        recent = deque(maxlen=16)
        for line in proc.stdout:
            clean = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line).rstrip("\n\r")
            if clean.strip():
                recent.append(clean)
                self.events.put(("log", clean))
        code = proc.wait()
        if check and code:
            details = "\n".join(recent)
            raise RuntimeError(f"Command failed (exit {code}): {' '.join(map(str, command))}\n{details}")
        return code

    def ollama_available(self, url):
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/api/tags", timeout=4) as response:
                return response.status == 200
        except (OSError, urllib.error.URLError):
            return False

    def _installed_models_at(self, url):
        try:
            with urllib.request.urlopen(url.rstrip('/') + '/api/tags', timeout=5) as response:
                return {item.get('name', '') for item in json.load(response).get('models', [])}
        except (OSError, ValueError, urllib.error.URLError):
            return set()

    def install(self):
        try:
            env=ROOT/'.venv'
            py=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
            self.events.put(('log', f'Operating system: {SYSTEM} ({platform.machine()})'))
            self.events.put(('log', f'Python: {sys.version.split()[0]}'))
            target_python, target_version = discover_python()
            self.events.put(('log', f'Selected environment interpreter: Python {target_version} ({target_python})'))
            # A preexisting environment may have been created with Python 3.15.
            # Never reuse it with another interpreter: preserve it as a backup.
            if py.exists():
                existing_version = environment_python_version(py)
                if existing_version != target_version:
                    backup = ROOT / f'.venv-python{(existing_version or "unknown").replace(".", "")}-backup'
                    suffix = 1
                    while backup.exists():
                        backup = ROOT / f'.venv-python{(existing_version or "unknown").replace(".", "")}-backup-{suffix}'
                        suffix += 1
                    self.events.put(('log', f'Preserving existing Python {existing_version or "unknown"} environment at {backup.name}'))
                    env.rename(backup)
            if not py.exists():
                self.events.put(('status','Creating isolated Python environment...'))
                self.events.put(('log',f'Creating virtual environment using Python {target_version}...'))
                self.run_logged([target_python, '-m', 'venv', str(env)])
            if self.voice_addon.get() and target_version not in ('3.11', '3.12', '3.13', '3.14'):
                self.install_warnings.append('Offline voice recognition requires Python 3.11–3.14; install Python 3.13 and rerun setup to enable it.')
                self.events.put(('log', 'WARNING: Skipping voice add-on because no compatible Python 3.11–3.14 interpreter was found.'))
            self.events.put(('status','Installing Luclid-ii dependencies...'))
            self.run_logged([str(py),'-m','pip','install','--disable-pip-version-check','-e',str(ROOT)])
            voice_installed = False
            if self.voice_addon.get() and target_version in ('3.11', '3.12', '3.13', '3.14'):
                try:
                    self.events.put(('status', 'Installing offline voice recognition add-on...'))
                    self.run_logged([str(py), '-m', 'pip', 'install', '--disable-pip-version-check', '--only-binary=:all:', 'sounddevice', 'faster-whisper', 'numpy'])
                    self.events.put(('status', 'Caching Whisper Tiny for offline transcription...'))
                    self.run_logged([str(py), '-c', 'from faster_whisper import WhisperModel; WhisperModel("tiny", device="cpu", compute_type="int8")'])
                    voice_installed = True
                except (RuntimeError, OSError) as exc:
                    warning = f'Optional offline voice add-on was not installed: {exc}'
                    self.install_warnings.append(warning)
                    self.events.put(('log', 'WARNING: ' + warning))
                    self.events.put(('log', 'Core Luclid-ii installation will continue. Voice can be installed later with a compatible Python version.'))
            (env/'.luclid-installed-version').write_text(APP_VERSION)
            mode=self.ai_mode.get()
            config={'ollama_server':self.server.get().strip() if mode=='connect' else 'http://127.0.0.1:11434',
                    'model':self.model.get().strip(), 'ai_setup_mode':mode,
                    'voice_addon': voice_installed, 'optional_models': ([name for enabled,name in [(self.extra_qwen3.get(),'qwen3:8b'),(self.extra_qwen35.get(),'qwen3.5:9b'),(self.extra_deepseek.get(),'deepseek-r1:8b')] if enabled] if mode=='automatic' else [])}
            CONFIG.parent.mkdir(parents=True,exist_ok=True)
            CONFIG.write_text(json.dumps(config,indent=2))
            if mode=='automatic':
                if self.ollama_available('http://127.0.0.1:11434'):
                    self.events.put(('log','Ollama server detected and responding.'))
                else:
                    exe=shutil.which('ollama')
                    if not exe:
                        self.events.put(('status','Checking Ollama installation options...'))
                        self.events.put(('log','Ollama is not installed.'))
                        if SYSTEM=='Windows' and shutil.which('winget'):
                            self.events.put(('log','Installing Ollama using winget...'))
                            self.run_logged(['winget','install','--id','Ollama.Ollama','--exact','--accept-source-agreements','--accept-package-agreements'])
                        elif MAC and shutil.which('brew'):
                            self.events.put(('log','Installing Ollama using Homebrew...'))
                            self.run_logged(['brew','install','--cask','ollama'])
                        else:
                            self.events.put(('log','No supported automated Ollama installer found. Visit https://ollama.com/download'))
                            self.events.put(('status','Ollama needs manual installation.'))
                    exe=shutil.which('ollama')
                    if exe and not self.ollama_available('http://127.0.0.1:11434'):
                        self.events.put(('log','Starting Ollama server...'))
                        try:
                            kwargs={'creationflags': subprocess.CREATE_NO_WINDOW} if SYSTEM=='Windows' else {}
                            subprocess.Popen([exe,'serve'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**kwargs)
                        except OSError as exc: self.events.put(('log',f'Ollama start failed: {exc}'))
                        for _ in range(12):
                            if self.ollama_available('http://127.0.0.1:11434'): break
                            time.sleep(1)
                if self.ollama_available('http://127.0.0.1:11434'):
                    self.events.put(('log','Ollama server is available.'))
                    exe=shutil.which('ollama')
                    if exe:
                        self.events.put(('status','Downloading AI model (may take several GB)...'))
                        already = self._installed_models_at('http://127.0.0.1:11434')
                        if self.model.get().strip() in already:
                            self.events.put(('log', f'Default model already installed: {self.model.get().strip()}; skipping download.'))
                        else:
                            self.run_logged([exe,'pull',self.model.get().strip()])
                        for optional_model in config['optional_models']:
                            if optional_model == self.model.get().strip():
                                continue
                            if optional_model in already:
                                self.events.put(('log', f'Already installed: {optional_model}; skipping download.'))
                                continue
                            self.events.put(('status',f'Downloading optional model {optional_model}...'))
                            self.events.put(('log',f'Optional AI add-on: {optional_model}'))
                            try:
                                self.run_logged([exe,'pull',optional_model])
                            except (RuntimeError, OSError) as exc:
                                self.events.put(('log',f'Optional model {optional_model} could not be installed: {exc}'))
                    else: self.events.put(('log','Ollama command not found in PATH. Model download can be done later.'))
                else: self.events.put(('log','Ollama server unavailable; AI setup can be completed later.'))
            elif mode=='connect':
                url=self.server.get().strip()
                if not url.startswith(('http://','https://')): raise ValueError('Ollama server URL must start with http:// or https://')
                self.events.put(('log',f'Using existing Ollama server: {url}'))
                if not self.ollama_available(url): self.events.put(('log','Server not reachable now; check its address and network access later.'))
            else: self.events.put(('log','AI setup saved for later.'))
            self.events.put(('log','Luclid-ii application setup completed.'))
            if self.install_warnings:
                self.events.put(('log', 'Completed with optional add-on warnings:'))
                for warning in self.install_warnings:
                    self.events.put(('log', warning))
            self.events.put(('done',None))
        except Exception as exc:
            self.events.put(('log',f'ERROR: {exc}'))
            self.events.put(('error',str(exc)))
    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='status':self.status.set(value)
                elif kind=='log': self.append_log(value)
                elif kind=='done':
                    self.running=False;self.step=5;self.draw()
                    if self.install_warnings:
                        messagebox.showwarning('Installed with optional feature warnings', '\n\n'.join(self.install_warnings)[:1800])
                elif kind=='error':
                    self.running=False;self.step=3;self.draw();messagebox.showerror('Installation failed',value)
        except queue.Empty: pass
        self.root.after(100,self.poll)
    def close(self):
        if self.running: messagebox.showinfo('Installation running','Please wait for installation to finish before closing.')
        else:self.root.destroy()

if __name__=='__main__': Wizard().root.mainloop()
