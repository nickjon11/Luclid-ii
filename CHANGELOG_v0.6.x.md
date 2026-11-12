# Luclid-ii v0.6.x — Consolidated Changelog

All prior per-release entries are preserved below.


---

## CHANGELOG_v0.6.0

# Luclid-ii v0.6.0

- New LinkedIn Job Explorer: blank initial state, job filters, browser-based LinkedIn search, import accessible HTTPS job URLs, inspect descriptions, save jobs and update application statuses.
- AI Resume Match: choose a local resume and prepare an evidence-based comparison in local Ollama Chat; never fabricates a fit score or claims to have applied.
- Google: simplified **Sign in with Google** button and an Advanced toggle for personal OAuth credentials. App-owner client ID can be provided through `LUCLID_GOOGLE_CLIENT_ID` or `google_oauth_public.json` in the project root.
- Public OAuth client ID is not a secret. A real Google Cloud project and required Google verification are still necessary before unrestricted public use.
- Existing v0.5.7.1 features and styling retained.

## Limitations

LinkedIn blocks many automated requests. Search opens the real LinkedIn website in a browser, and the in-app explorer only imports descriptions from accessible public URLs. This release does **not** claim direct LinkedIn API search or auto-apply capability. OAuth cannot work for general users until the application owner configures a real client ID and completes any required Google verification.


---

## CHANGELOG_v0.6.1

# Luclid-ii v0.6.1

- Redesigned Google Account into connection, status and permission cards; developer OAuth settings moved into a separate dialog.
- Kept existing Gmail and Calendar functionality, including local AI drafting and confirmation.
- Expanded Automatic Search / Job Agent UI with job criteria, resume controls, empty result/detail panels, and Start/Stop controls.
- Search opens accessible LinkedIn browser results; automatic scraping and direct discovery are not implemented. Import real public URLs in the existing explorer.
- Public Google sign-in requires an app owner-provided OAuth client ID and any required Google verification.


---

## CHANGELOG_v0.6.2

# Luclid-ii v0.6.2 — targeted fixes

- AI Resume Match now sends resume and selected job text directly to the local Ollama API, asynchronously, instead of placing the resume in Chat where automatic web research could send it to DuckDuckGo.
- The AI Resume Match result appears inside the job explorer. Errors are shortened to avoid displaying private text or giant URLs.
- Automatic web research refuses long or resume-like queries; short public questions remain available.
- Imported job descriptions receive lightweight cleanup of common LinkedIn navigation labels for AI comparison.
- Wallpaper loading resolves old bundled relative paths after upgrades or folder moves.
- GIF wallpaper rendering now initializes the first frame, refreshes on frame changes, and pauses while hidden; static JPG/PNG support and the 50% opacity limit remain.
- The two bundled files named `animated_01.gif` and `animated_02.gif` each contain **one frame**, so they display as static GIFs. To test animation, choose a genuine multi-frame GIF.
- Existing v0.6.1 Google/LinkedIn interface and Windows launcher scripts retained.

## Validation

Python syntax compilation and ZIP integrity are checked. The Windows PySide6 GUI, local Ollama, Google authorization, and live LinkedIn pages require testing on the user's machine.


---

## CHANGELOG_v0.6.3

# Luclid-ii v0.6.3 — Cross-platform deployment foundation

- Added one-step source launchers for Windows, macOS, and Linux; first run creates an isolated virtual environment and installs dependencies automatically.
- Added PyInstaller native build tooling and a GitHub Actions workflow for Windows, macOS, and Ubuntu build artifacts.
- Added Debian package builder that installs the Linux executable under `/opt/luclid-ii`, a `/usr/bin/luclid-ii` command, and a desktop entry.
- Updated Python package version to 0.6.3.
- Retained the desktop features from v0.6.2 and adjusted bundled wallpaper lookup for packaged builds.

**Not yet included:** A signed GitHub Pages APT repository, public `apt install` bootstrap, signed macOS application, or prebuilt native executables. These require publishing and platform testing.


---

## CHANGELOG_v0.6.4

# Luclid-ii v0.6.4 — Platform-aware setup wizard

- One Python setup wizard for Windows and macOS, with classic Windows 98-inspired or classic Mac-inspired styling chosen by the detected OS. No simulated Finder desktop.
- Steps: Welcome, System Check, Components, Ready to Install, Installing, Finish.
- Creates private `.venv` and installs Python dependencies. Optional official Ollama download page and optional model pull.
- Linux remains terminal-only through `launch-linux.sh` or Debian package scripts.
- Saves chosen Ollama endpoint/model as installer preferences (application runtime integration is a future task).
- Does not silently install Ollama, set up a system service, or guarantee working AI chat.
- No native binaries, signed installers, or published APT repository included.


---

## CHANGELOG_v0.6.5

# Luclid-ii v0.6.5 — Installer Refinement

- Uses the original application Lii icon in the setup window, sidebar, and Windows taskbar.
- Removes the unnecessary installer theme label.
- Replaces component checkboxes with Automatic Setup, Connect to Existing Ollama Server, and Save for Later.
- Adds a scrolling green-on-black live installation log with pip and Ollama command output.
- Automatic Setup checks for Ollama, attempts installation with winget on Windows or Homebrew on macOS, starts Ollama if available, and downloads the selected model. Requires network and can use several GB.
- Preserves the existing desktop application and terminal-only Linux deployment.

## Limitations
- The Windows/macOS GUI setup still requires Python 3.11+ with Tkinter.
- Ollama installation depends on winget/Homebrew availability and permissions.
- The application may require a separate update to honor the saved installer server preference.
- Not tested on actual Windows/macOS in this build environment.


---

## CHANGELOG_v0.6.6-model-addons

# Luclid-ii v0.6.6 — Optional model add-ons

- Added opt-in Qwen3 8B (`qwen3:8b`) and DeepSeek-R1 8B (`deepseek-r1:8b`) downloads to the Ready to Install screen when Automatic Setup is selected.
- Preserved `qwen2.5:7b` as the default model.
- Selected add-ons download using the local Ollama CLI after the base model; failures are logged without aborting the entire installation.
- Model selections are recorded in `~/.luclid-ii/installer.json`.
- Selecting an add-on does not itself change the desktop application's model dropdown. Ollama models can be discovered via `ollama list`; desktop UI integration is a separate enhancement.


---

## CHANGELOG_v0.6.6

# Luclid-ii v0.6.6

- Fixed Windows and macOS installer oversized logo and clipped sidebar by displaying bounded 32px/64px versions of the original Lii icon.
- Redesigned macOS installer with a compact brushed-metal header and a clean sidebar; Windows retains its purple Windows 98 wizard.
- Adjusted installer window size and typography while preserving the working v0.6.5 installation and Ollama workflows.
- Preserved the three AI setup choices and green-on-black live installation log.

Note: Native Windows and macOS GUI validation remains necessary.


---

## CHANGELOG_v0.6.7

# Luclid-ii v0.6.7 — Local AI interaction update

- Consistent version display in application, About, installer, and package metadata.
- Screenshot attachments via Ctrl+V / Cmd+V, right-click Paste, or image file selection. Images are passed to local Ollama in the request only; vision-capable model required.
- Local voice-to-text microphone button: records eight seconds and transcribes locally using optional `sounddevice`, `faster-whisper`, and `numpy`. User reviews transcription before sending. First use downloads Whisper tiny model unless already cached.
- Active model name is provided in the model's system instructions.
- Maximum response token setting to reduce runaway generation; does not fix a malfunctioning DeepSeek runtime.

## Known limitations
- Voice dependencies and Whisper Tiny can now be installed as an optional add-on in the GUI installer; installation requires internet the first time. Existing installations may still need the add-on installed.
- No automatic vision model installation/switching. Select an Ollama vision-capable model before sending images.
- No streaming responses, stop-generation control, mathematical rendering, or full DeepSeek runtime fix in this build.
- Graphical tests on Windows/macOS/Linux and live Ollama inference still required.

## Installer and offline-first refinement (November 11, 2026)
- Scrollable center pages with mouse wheel and fixed footer/navigation.
- Detect installed Ollama models through `/api/tags`; manual Rescan Models action.
- Skip pulling models already installed on the local Ollama server.
- Label DeepSeek-R1 8B experimental due to observed generation problems.
- Optional Offline Voice Recognition add-on installs Python dependencies and caches Whisper Tiny for subsequent offline transcription.
- Existing Tools > Web Research setting already defaults to Ask before online research, with Offline Only and Automatic options; no new cloud AI dependency.
- Advanced Qwen models remain user-managed through Ollama, not automatically downloaded.
- GUI and model inference still require testing on Windows and macOS.


---

## CHANGELOG_v0.6.8

# Luclid-ii v0.6.9 — Installer reliability update

- Bumped current app, installer and package version to v0.6.9.
- Installer now includes the failing command and recent output in dependency-installation errors.
- Optional offline voice recognition installation and Whisper model caching no longer abort the core app installation when they fail; an explicit warning is shown instead.
- Voice add-on is recorded as installed only after both dependencies and the transcription model are prepared.
- Warns that Python 3.15 may not yet be supported by all optional voice packages; recommends Python 3.13 or 3.14 for voice compatibility.
- Preserves offline-first web research, model detection, scrollbar, DeepSeek experimental warning and existing app features.

## Verification

Static Python compilation and ZIP integrity were checked. Windows/macOS GUI and full dependency installations still require testing on target machines. The previous failure's exact underlying package error remains unconfirmed.


---

## CHANGELOG_v0.6.9

# Luclid-ii v0.6.9

- Installer selects a compatible Python interpreter independently of the Python running the wizard; prefers Python 3.13, then 3.12, 3.14, 3.11.
- When switching Python versions, preserves the previous `.venv` as a named backup instead of deleting it.
- Optional offline voice recognition is skipped with a clear warning if only Python 3.15 is available.
- Voice dependencies are installed using precompiled wheels only to avoid PyAV/Cython source build failures.
- Existing v0.6.8 features and offline-first controls are retained.

## Windows testing
Run `py -3.13 --version` to check for Python 3.13. If missing, install Python 3.13 from python.org, then rerun `Luclid-ii-Setup.py`. The installer should report the chosen interpreter on Ready to Install. If the voice add-on is selected, verify that Whisper Tiny is downloaded and microphone input works.


---

## CHANGELOG_v0.6.10

# Luclid-ii v0.6.10

- Voice button toggles recording on first click and stops on second click.
- Live microphone input level bar displays audio activity during capture.
- Microphone closes before offline Whisper transcription starts.
- Voice recording stops automatically after five minutes as a safety limit.
- Existing optional voice installation, offline-first settings, and screenshot pasting are preserved.


---

## CHANGELOG_v0.6.11

# Luclid-ii v0.6.11

- Added **Tools → Install Offline Voice Recognition…**.
- Checks which voice packages are missing in the running Python environment.
- Requests permission before downloading optional packages.
- Installs with a nonblocking process and displays live pip output.
- Prevents unsupported Python 3.15 installs and explains bundled executable limitations.
- Voice error dialog points to the in-app Tools menu.
- Preserves toggle-to-record and live microphone meter from v0.6.10.
- Restart the application after installing voice dependencies.


---

## CHANGELOG_v0.6.12

# Luclid-ii v0.6.12 — Combined test build

- Includes v0.6.11 in-app Tools > Install Offline Voice Recognition, plus v0.6.10 toggle recording and live microphone meter.
- Adds an online research mode button next to the model selector, with Offline Only, Ask, and Automatic options. Local Ollama remains the model backend.
- Expands automatic online-research detection to stocks, stock quotes, tickers, market prices, exchange rates, weather, and explicit requests to look something up online.
- Offline Only now explains why a live-information question cannot be answered, instead of silently producing a stale answer.
- Separates online search failures from Ollama failures. Search snippets are not guaranteed to contain a live quote or timestamp; the model must acknowledge missing data.
- Bumps app, installer, and package version to 0.6.12.

## Test plan
1. Open Tools > Install Offline Voice Recognition, install add-on, restart; verify live meter and start/stop toggle.
2. Switch research mode using the new button next to Model. In Ask mode, request `Look up NVIDIA's current stock price online`; confirm permission dialog.
3. In Automatic mode, repeat; confirm research activity and source links, or a clear error if search fails.
4. In Offline Only mode, repeat; confirm explicit offline warning and no online request.
5. Check Help > About and installer title display v0.6.12.

This release is source-checked only; GUI and live web search require testing on the target machine.


---

## CHANGELOG_v0.6.13

# Luclid-ii v0.6.13

- After successful in-app offline voice package installation, automatically dismiss the installer dialog and restart Luclid-ii using its current Python interpreter.
- Keep the log visible on failure and show a restart warning if relaunch fails.
- Avoid interrupting an active AI response; in that case, request a manual restart.
- Update application and setup version to 0.6.13.

Test on Windows, macOS and Linux before release.


---

## CHANGELOG_v0.6.14

# Luclid-ii v0.6.14 (test build)

- Optional Qwen3.5 9B vision model in installer, with installed-model detection.
- Multiple screenshot attachments (up to 8) with thumbnails, previews, removal, and per-model vision capability checks.
- Removed redundant top-right Workspace button; sidebar workspace remains.
- Permission-based `/open https://example.com` uses OS default browser, with installed-browser selection if default fails.
- Online research errors offer a browser fallback; this does not grant Luclid-ii browser page-reading or automated clicking.
- Web retrieval diagnostics and fallback search provider.
- Version consistency v0.6.14.

This build has not been GUI-tested on Windows/macOS/Linux.


---

## CHANGELOG_v0.6.15

# Luclid-ii v0.6.15

- Added Tools → Download Other Models with Qwen catalog, estimated sizes, confirmation, streaming Ollama progress, cancel and error logs.
- On successful model pull, the installer dialog closes and the model dropdown refreshes without restarting Luclid-ii.
- Simplified the initial setup model selection to Qwen3.5 9B and experimental DeepSeek-R1 8B.
- Existing installed models are never removed.
- Requires a running local Ollama server for in-app model downloads.


---

## CHANGELOG_v0.6.16

# Luclid-ii v0.6.17 — Development test build

- File → Saved Documents: local document library, import, search, open, rename and delete. Files stored under ~/.luclid-ii/saved-documents.
- File → AI Models: list installed Ollama models, actual reported storage, approximate runtime memory, download and confirmed uninstall.
- Automation & Tasks tab: persistent local tasks with optional reminder dates while the app is open.
- Terminal tab: user-entered shell commands with per-command approval and stop control.
- File → Open Workspace: native folder picker. Sidebar Browse Workspace now explains how to select a folder.
- Version updated to 0.6.17.

Limitations: web search and natural-language browser command routing remain unresolved; scheduled tasks do not run while Luclid-ii is closed; terminal is not sandboxed.


---

## CHANGELOG_v0.6.17

# Luclid-ii v0.6.17 — Automation & Tasks test build

- Right-click or double-click any task row to edit task name, due date and status.
- While app runs, due tasks trigger a reminder with Mark Complete, Snooze 10 min, or Dismiss.
- New AI Plan from Goal dialog uses the selected local Ollama model to draft subtasks and schedules.
- Individually select, edit, or remove proposed subtasks before approval; nothing saved without confirmation.
- Existing task storage remains at ~/.luclid-ii/tasks.json; old tasks stay readable.
- AI-generated tasks default to 9:00 AM local time on proposed dates, and can be edited before/after saving.
- Known limitations: AI dates and estimates require review; no OS-level background scheduling; prior browser/web research issues remain.


---

## CHANGELOG_v0.6.18

# Luclid-ii v0.6.18 — Development build

- AI Planner: inherit active model from main window, with an installed-model selector and refresh button.
- Planner: narrower default dialog and wrapped introductory text for better scaling.
- Tasks: compact default columns, user-resizable widths, and persistent widths.
- Terminal: transparent output viewport for application wallpaper.
- Wallpapers: section overrides for Tasks, Terminal, Saved Documents and AI Task Planner, scrollable settings, and existing animated GIF support.

Note: Saved Documents and AI Task Planner are separate dialogs; wallpaper selection for these dialogs is exposed but full dialog background rendering remains a follow-up.


---

## CHANGELOG_v0.6.19

# Luclid-ii v0.6.19 — Development test build

- Planner: pass local date and time, require future deadlines, assign dates in Python, and validate schedules.
- Planner: request structured JSON from Ollama, increase response budget, and retry malformed JSON once.
- Terminal: Enter submits through the existing approval dialog; arrow-key history and Escape-to-clear.
- Light mode: improve wallpaper visibility and contrast in terminal/task surfaces; dark theme left unchanged.
- Existing tasks, settings, and Ollama models are not removed.

## Known limitations
- AI model output can still fail due to Ollama timeouts or model limitations.
- Terminal runs commands only after approval and is not sandboxed.
- GUI behavior has not been verified on Windows, macOS, or Linux.


---

## CHANGELOG_v0.6.20

# Luclid-ii v0.6.20 — Final v0.6.x development build

- Task calendar with day agenda and legend.
- AI planner start times, editable durations, local scheduling.
- Calendar export to ICS, CSV, and JSON.
- User-confirmed Google Calendar event creation, avoiding duplicate creations by tracking event IDs.
- Next milestone: v0.7.0 cross-platform GitHub Actions release.


---

## CHANGELOG_v0.6.21

# Luclid-ii v0.6.21 — Development patch

- Clickable HTTPS/HTTP links in AI chat, including Markdown links and numbered web search sources.
- Reject unsafe chat URL schemes; open links with the operating system browser.
- Context-aware query expansion for short CEO follow-ups and stricter web result relevance checks.
- Task importance markers, editable importance and custom colors, and colored calendar dates with task tooltips.
- More balanced adjustable task/calendar split and translucent calendar background.
- GIF wallpaper playback uses no full-frame cache to reduce memory usage.

Known limitations: QCalendarWidget date formatting supports one foreground color per date, not multiple distinct colored dots. Google Calendar sync remains one-way for new events. Changes require GUI testing on Windows/macOS/Linux.


---

## CHANGELOG_v0.6.22

# Luclid-ii v0.6.22

- Exact offline arithmetic calculator integrated with chat.
- Recognizes follow-ups such as “do the math” in the same conversation.
- Supports integers, decimals, parentheses, and bounded arithmetic operators.
- Restricted AST evaluation; no arbitrary Python execution.
- Bypasses Ollama and web search for recognized calculations.


---

## v0.6.23

- Workspace-aware terminal with persistent directory changes.
- Calendar wallpaper visibility refinements, event counts, and right-click agenda editing.
- Removed fixed legend while retaining task importance and custom colors.
- Added Windows windowless launch/setup entry points and suppressed subprocess console windows.
- Consolidated release notes for v0.5.x and v0.6.x.

## v0.6.24
- Workspace Explorer: 80/20 default Name/Type widths, manually resizable and remembered, with full-path tooltips.
- Automation & Tasks: transparent calendar grid, task list and daily agenda viewports so the existing wallpaper shows through.
- My Computer: Reset Workspace button beside Browse Workspace; clears the workspace and returns the terminal to the home directory without deleting files.
- Blocks workspace reset while a terminal command is running.

---

## Additional v0.6.25 revision notes

# Luclid-ii v0.6.25 — Wallpaper transparency corrections

- Removed opaque theme-colored backgrounds from descriptive text strips in GitHub, Automation & Tasks, and Terminal.
- Kept label text opaque and removed unnecessary padding.
- Made Automation & Tasks table and calendar viewports use transparent palette brushes, so the existing wallpaper overlay can show through.
- Prevented light-mode theme refresh from reintroducing an opaque task table background.
- Preserved task controls, date markers, and other v0.6.24 features.

Note: GUI rendering should be verified on Windows, macOS, and Linux; source compilation does not validate Qt compositing.

## Revision 2
- Shortened the sidebar button label from “Browse Workspace” to “Browse Space” to prevent clipping beside Reset. No behavior changed.

## Revision 3 — Light-mode text contrast
- Wallpaper description headings in Automation & Tasks, Terminal, and GitHub now use readable white text on dark transparent surfaces in light mode.
- GitHub token status text uses a transparent background and readable text.
- Preserved existing light-purple inputs, Google account status styling, and dark mode behavior.

