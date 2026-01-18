# AGENTS.example.md

Example policy for `~/.codex/AGENTS.md` if you want opinionated gating.

## Worktree sync policy
- Before creating or checking out a worktree for a new prompt, sync `origin/main`:
  - Run `git fetch origin main`.
  - Prefer basing the worktree on `origin/main`: `git worktree add -b <branch> <path> origin/main`.
  - Only run `git pull --ff-only origin main` when on `main` with a clean tree.

## Opinionated gating
- Require `/project` for new root tasks.
- Require `@branch` when a task will create, edit, or delete files, or otherwise
  change repo state.
- If directives are missing, ask the user to rerun with `/project` and `@branch`
  instead of proceeding.
- Allow read-only requests with `/project` but without `@branch`.
