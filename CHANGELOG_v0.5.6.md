# Luclid-ii v0.5.6

Built from the v0.5.5 Gmail hotfix source.

- Preserves the Gmail AI draft model-selection hotfix and review-before-send workflow.
- Web search results now go into the prompt before local generation, with explicit instructions to use recent source evidence, cite sources, and disclose uncertainty.
- Adds a targeted safeguard for a contradictory outdated US-president answer when the official White House result supports the current answer. This safeguard is narrow, not a general factual verifier.
- Expands system_info with read-only hardware diagnostics and cross-platform fallbacks. Windows uses PowerShell CIM read-only queries; macOS and Linux have limited GPU fallback.

Run setup_windows.bat on first install, then run_windows.bat. Requires Windows testing with Ollama and live web search.
