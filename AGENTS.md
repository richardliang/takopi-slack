# Repository Guidelines

## Project Structure & Module Organization
- `src/takopi_slack_plugin/`: core Slack transport (bridge, client, config, engine, outbox, thread sessions).
- `src/takopi_slack_plugin/commands/`: slash/shortcut command parsing and dispatch.
- `docs/`: operator guidance (gating examples).
- `dist/`: build artifacts (ignore in reviews).
- No `tests/` directory yet.

## Build, Test, and Development Commands
- `uv build`: build sdist and wheel via `uv_build`.
- `pip install -e .` (or `uv pip install -e .`): install editable package for local dev.
- `takopi --transport slack`: run takopi using this transport once installed.
- Tests: no automated suite configured; add `pytest` if introducing tests.

## Coding Style & Naming Conventions
- Python with 4-space indentation and PEP 8-ish formatting; keep imports grouped.
- Naming: `snake_case` for functions/modules, `PascalCase` for classes, `UPPER_CASE` for constants.
- Type hints are used throughout; keep new code typed.
- No formatter/linter wired; match existing style in `src/takopi_slack_plugin/`.

## Testing Guidelines
- No testing framework or coverage target is defined.
- If adding tests, place them in `tests/` and name files `test_*.py`; run with `pytest`.

## Commit & Pull Request Guidelines
- Commit messages are short and imperative; prefixes like `docs:`, `chore:`, and `release:` are common. Version bumps use `Bump version to x.y.z`.
- PRs should include a clear summary, linked issues if applicable, and test notes (or "not run").
- If behavior or config changes (Slack scopes, tokens, `takopi.toml`), update `README.md` and mention it in the PR. Screenshots only for doc/UI changes.

## Security & Configuration Tips
- Do not commit Slack tokens or local state. Configuration lives in `~/.takopi/takopi.toml` and thread state in `~/.takopi/slack_thread_sessions_state.json`.
