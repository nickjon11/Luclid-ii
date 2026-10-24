# Luclid-ii - AI Agent v0.4.0

Windows-first, local Ollama-powered assistant developed by Jonathan Lachman. The local model and conversation history do not require a cloud AI provider.

## Install

From the directory containing `pyproject.toml`:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m local_muse.app
```

Install and start Ollama separately, then run `ollama pull qwen2.5:7b` if needed. Choose your installed model from the dropdown.

## v0.4.0 changes

- Rebranded to Luclid-ii - AI Agent; About credits Jonathan Lachman.
- Added a + button left of the chat input for PDF, DOCX, TXT, Markdown, and code attachments. Text is extracted locally and included in the next message. Maximum 8 MB per file and 18,000 extracted characters per file.
- GitHub account connection window with fine-grained token stored in the OS credential vault via `keyring`. Public and authorized private repository metadata lookup. No repository writes.
- LinkedIn entry opens the official website in your browser. No LinkedIn password collection, OAuth token exchange, or unsupported scraping.
- Local resume-to-job-description comparison: import resume and paste a job listing, then ask the local model to compare them. No automated job search or applications yet.
- Single +/- App Resources collapse toggle, no close button.

## Security and limitations

Online integrations require internet. LinkedIn official job search and application APIs are not generally available to arbitrary personal apps; this version does not claim to connect to your LinkedIn data. A browser visit is not an OAuth connection. No automatic applications are submitted. Do not paste account passwords into chat.

Document contents are sent only to local Ollama at 127.0.0.1:11434 by the app, but are included in local SQLite chat history. Only attach documents you are comfortable storing in chat history. PDF extraction does not perform OCR. The context window of the model can limit how much attachment text it uses.

GitHub token is stored through OS keyring rather than a plain text config file. The GitHub lookup uses the official HTTPS API. This app does not upload resume data to LinkedIn or GitHub.

Existing conversation history remains in `%LOCALAPPDATA%\LocalMuseAgent\history.sqlite3`. Back it up before upgrades.

## Application icon
The retro Lii icon is included in `src/local_muse/assets/` as transparent PNG and Windows ICO. The application and taskbar use this icon. If packaging with PyInstaller, use `--icon src/local_muse/assets/lii_icon.ico` and include the PNG as package data.


## v0.4.0 changes
- GitHub username repository browser with default-browser links. Public repositories do not require a token. Saved tokens remain in OS keyring.
- LinkedIn Job Assistant: saved resume selection, multi-URL paste with newline insertion, opt-in web retrieval, numbered results, and local LLM comparison.
- LinkedIn may restrict automated reading. The app reports inaccessible links and supports pasted descriptions instead.
- URL retrieval is online and not part of the offline LLM. Keyword overlap is only a rough heuristic, not a validated hiring score.
- Remote writes and pushes are not implemented in this version.

## v0.4.0: job form assistance (optional)
The Job Assistant has **Auto-fill a job application**. Select a saved resume, supply an HTTPS employer application URL, and explicitly approve opening a browser. The assistant fills only clearly labeled name, email, and telephone fields when these are present in the resume. It does **not** submit applications, answer eligibility questions, bypass sign-in, or guarantee compatibility with all job boards. Review every field before submitting manually.

The browser helper is optional and uses a separate local Chromium window. Install once:

```powershell
.\.venv\Scripts\python.exe -m pip install playwright
.\.venv\Scripts\python.exe -m playwright install chromium
```

The job-analysis worker now sends results to a GUI-thread Qt slot, rather than updating QTextDocument from a background thread. The About dialog credits Jonathan Lachman.

## v0.4.0 — Job Agent workspace

The Integrations panel now has **LinkedIn · Manual Search** and **LinkedIn · Automatic Search**. Automatic Search opens a local-first Job Agent workspace with saved role, location, work arrangement and salary preferences, a LinkedIn browser search shortcut, and an SQLite application tracker. Paste multiple direct job links to save them; open listings in your default browser and update their status. LinkedIn sign-in and search results remain in your browser. **This version does not autonomously scrape LinkedIn, monitor email, or submit applications.** Use Manual Search to retrieve accessible job descriptions, compare a saved resume with Ollama, and launch optional reviewed Playwright autofill. The existing chat input now displays its working state as placeholder text while Ollama is processing. GitHub's optional token field no longer triggers an empty-token warning when Enter is pressed.

The Job Agent database is stored in `~/.luclid-ii/job_agent.sqlite3`. No job preferences or tracking data are uploaded by Luclid-ii itself. Browser search and public job retrieval do require internet access. All application submissions remain manual.

## v0.4.1 updates
- Separate SQLite-backed conversation tabs. Right-click a tab to rename it. Closing a tab asks for confirmation and deletes its stored messages; the last tab cannot be closed.
- Each assistant message has a small floppy-disk Word export control. Word exports preserve headings, basic bold text and lists.
- `github_repo` tool now accepts a GitHub username and lists public repositories (up to 100). Private repositories are still accessible through the separate GitHub integration browser with an authorized token.
- Previous v0.4.0 conversation history is retained as Chat 1. Back up `%LOCALAPPDATA%\\LocalMuseAgent\\history.sqlite3` before upgrading.
- Windows GUI still requires testing on Windows. Android is not included.


## v0.5.6 Google Account integration (initial build)

The Integrations sidebar now has **Google Account · Calendar and Email**. The dialog provides OAuth sign-in, permission selection, upcoming events, event creation, inbox previews, email reading and confirmed email sending. The rest of the existing v0.4.1 features are retained.

### Google Cloud setup (required)

1. In Google Cloud Console create or select a project. Enable **Google Calendar API** and **Gmail API**.
2. Configure the OAuth consent screen (Google Auth Platform), add your Google account as a test user if in Testing mode, and request the appropriate Calendar/Gmail scopes. Google may require verification for public distribution and sensitive scopes.
3. Create an OAuth client of type **Desktop app**. Copy its **Client ID** (not a client secret).
4. Open Luclid-ii > Google Account · Calendar and Email. Paste the Desktop client ID, select the minimum required permissions, then click Connect. Your browser opens Google's sign-in and consent page. The temporary callback uses a loopback localhost port.
5. After authorization, test Refresh events and Refresh inbox. Grant Calendar event write or Gmail send permissions explicitly if needed. Reconnect to add permissions.

OAuth tokens are stored using your operating system keyring, not in the SQLite chat history. Disconnect removes the locally stored token; to revoke the grant at Google as well, visit your Google Account's third-party access settings. Calendar and Gmail content is sent to Google's APIs only for the actions you request. The app does not automatically upload your chat history. Network requests require internet.

**Limitations:** This first integration build uses a list-based upcoming-events view and Gmail inbox, not the full week-grid illustration. It supports create events but not editing/deleting them. Gmail drafts and autonomous job-email scheduling are not implemented. This package has been syntax-checked, but Google OAuth/API calls require testing with your own configured Google Cloud project and account.


### OAuth token exchange troubleshooting (v0.5.6 hotfix)
If Google approves access but Luclid-ii reports a 400 token error, copy both the Desktop OAuth Client ID and the Desktop OAuth Client Secret from your private Google Cloud credentials into the Connect tab. The secret is stored with OAuth credentials in the operating system keyring, not in the project source. Do not publish the JSON, secret, or saved tokens. This build also shows Google's error code and description when token exchange fails.

## v0.5.6 preview features

- Compact retro animated globe in the right end of the File/View/Tools/Help menu bar, with an activity label. Google API operations drive the indicator; other providers will be connected to the activity hook in later updates.
- Service navigation shortcuts for Chat, GitHub, LinkedIn and Google above the existing workspace/chat layout.
- Google Calendar date picker, month navigation and start/end time selectors (local time); upcoming events are filtered to the selected date.
- Gmail inbox now has separate Sender, Subject and local Received columns.
- Compact conversation headers, timestamps on new messages, saved display-name support for `call me ...`, and double-click agent tools. Historical messages without saved timestamps show a display-time timestamp until database migration.

Google access requires the user's own OAuth credentials and explicit authorization. The app has not been live-tested against Google APIs in this environment.


## v0.5.6 additions
- Google and GitHub credential status is shown in the main status bar (GitHub means a token is stored, not that it has been verified).
- Retro globe remains visible at the far right of the menu and animates during Google API requests.
- Existing conversation messages show their saved creation timestamps where available.
- Gmail includes AI Read / Draft Reply, using the locally selected Ollama model. Replies require manual review and explicit confirmation before sending.
- Run `setup_windows.bat` to install Python dependencies and the Playwright Chromium browser. Browser downloads require an internet connection.

Live Google, Playwright and Windows GUI functionality require testing on the target machine.


## v0.5.6 changes
- Online globe scaled to 30px with a wider activity label.
- Gmail AI reply prompts use the current local date when relevant, request concise plain text, and use one Best regards signature.
- Drafts remain editable and require explicit confirmation before sending.


## v0.5.6 integrated workspace layout update

- LinkedIn Automatic Search uses a split workspace: saved search preferences on the left and **real saved job links** on the right. The job table is not a live LinkedIn search-results feed; Search LinkedIn opens a browser. No fictitious jobs are displayed.
- Google Gmail uses a folder sidebar, inbox table, and selected-message preview. Switching folders retrieves messages with the corresponding Gmail label; Gmail permissions still apply.
- The selected message is fetched from Google and displayed as plain text. AI Draft Reply continues to use the local Ollama workflow and requires user confirmation to send.
- Existing Google Calendar, authentication, and other integrations are preserved.

These changes passed Python syntax checks but have not been tested with a live PySide6 Windows GUI or Google account.


## Launching v0.5.6 on Windows
Run `setup_windows.bat` once on a new installation (or when dependencies change), then double-click `run_windows.bat` to launch. You do not need to manually execute Python source files. The BAT launcher uses the virtual environment and still runs the Python application; it is not a standalone EXE.


## Optional current web research (v0.5.6)
Under **Tools > Web Research (optional)** choose Offline only, Ask before online research (default), or Automatically research current questions. Questions mentioning current dates, news, or current officeholders can trigger a search; `/research your question` requests it explicitly. The app searches DuckDuckGo's public HTML results, supplies short snippets to the locally running Ollama model, and includes source links. This is not retraining or a guarantee of correctness. Results may be incomplete, unavailable, or stale; verify primary sources. In Ask mode the current question is transmitted only after approval. Auto mode transmits matching current questions automatically. Offline mode blocks web research. Existing Google/LinkedIn features have their own permissions.

## v0.5.7.1 wallpapers
Choose **View → Customize Wallpapers…**. Set a universal wallpaper, or switch to individual mode and override individual sections. Sample images are included in `wallpapers/`. Wallpaper opacity defaults to 20%. Gmail AI-generated replies now begin with a local-time greeting.
