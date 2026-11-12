# Luclid-ii v0.5.x — Consolidated Changelog

All prior per-release entries are preserved below.


---

## CHANGELOG_v0.5.6

# Luclid-ii v0.5.6

Built from the v0.5.5 Gmail hotfix source.

- Preserves the Gmail AI draft model-selection hotfix and review-before-send workflow.
- Web search results now go into the prompt before local generation, with explicit instructions to use recent source evidence, cite sources, and disclose uncertainty.
- Adds a targeted safeguard for a contradictory outdated US-president answer when the official White House result supports the current answer. This safeguard is narrow, not a general factual verifier.
- Expands system_info with read-only hardware diagnostics and cross-platform fallbacks. Windows uses PowerShell CIM read-only queries; macOS and Linux have limited GPU fallback.

Run setup_windows.bat on first install, then run_windows.bat. Requires Windows testing with Ollama and live web search.


---

## CHANGELOG_v0.5.7.1

# Luclid-ii v0.5.7.1 — Wallpaper visibility hotfix

- Wallpaper opacity is now limited to 0–50%, including previously saved values above 50%.
- Large content surfaces (scroll areas, repository lists, tree views and page backgrounds) are configured to let the wallpaper show through rather than cover it with a solid fill.
- Input fields and buttons keep their opaque styling for readability.
- The View → Customize Wallpapers menu, universal/individual modes, GIF controls, and existing features remain available.
- The purple menu gradient remains unchanged.

Validation: Python syntax compilation and ZIP integrity passed. PySide6 was unavailable in the build environment; live Windows UI/GIF behavior still requires testing.


---

## CHANGELOG_v0.5.7

# Luclid-ii v0.5.7

- View → Customize Wallpapers: universal wallpaper or individual per-section overrides (Chat, GitHub, LinkedIn, Google, System Info).
- Custom images: PNG/JPG/BMP/WEBP/GIF, opacity 0–50% (as of v0.5.7.1) (20% default), fill/fit/stretch, reset, persistent preferences.
- Animated GIF support, with animation suspended when a wallpaper widget is hidden.
- Local-time greetings on AI-generated Gmail replies: Good Morning (05:00–11:59), Good Afternoon (12:00–16:59), Good Evening (17:00–04:59).
- Preserve Gmail model-selector hotfix, email review-before-send, web research, expanded system_info, and existing purple menu gradient.
- OAuth configuration unchanged; streamlined sign-in deferred to v0.6.0.

Testing: Python compilation and archive checks completed. Windows GUI, GIF playback, and live Google/Ollama integrations need user testing.

