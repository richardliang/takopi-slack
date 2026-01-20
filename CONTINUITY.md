Goal (incl. success criteria):
- Prepare and push a PR with the Slack onboarding fix and slash-command UX improvements; success is a branch pushed with relevant commits.

Constraints/Assumptions:
- Follow AGENTS instructions (ledger updates, worktree sync policy, allow edits on main but never commit).
- Must avoid destructive commands (reset/clean, rm) unless user explicitly requests or approves (higher-priority instruction).
- Use ASCII unless existing files require Unicode.

Key decisions:
- Use `questionary.ask_async()` in async onboarding to avoid nested `asyncio.run()`.
- Support dedicated slash commands by mapping `/takopi-<command>` or `/takopi_<command>` to plugin commands.

State:
- Changes implemented; preparing commit/branch for PR.

Done:
- Updated onboarding to use async questionary prompts.
- Added `/takopi-<command>` alias handling and usage note in Slack bridge.
- Updated README with slash-command guidance.

Now:
- Create branch, commit changes, and push for PR.

Next:
- Share PR branch and any follow-up UX notes.

Open questions (UNCONFIRMED if needed):
- Preferred slash command names and desired behavior (e.g., open modal vs. ephemeral message)? (UNCONFIRMED)

Working set (files/ids/commands):
- CONTINUITY.md
- src/takopi_slack_plugin/onboarding.py
- src/takopi_slack_plugin/bridge.py
- README.md
