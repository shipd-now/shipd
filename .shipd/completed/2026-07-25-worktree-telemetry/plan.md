# worktree-telemetry
Status: verified
Profile: lite
Theme: developer-experience

## Idea

Since the one-change-one-worktree workflow landed, every build runs inside
`.worktrees/<change>` — but `build_report.py` derives the transcript directory
from its working directory's path slug. The session transcript lives under the
slug of the directory the session was launched from (the main checkout), so
every worktree build reports `Tokens: unavailable (transcripts not found)` and
logs entries with no token data.

This change makes transcript discovery worktree-aware:

- Resolve a linked git worktree to its main checkout root when the working
  directory's own transcript slug does not exist, and use the main checkout's
  transcript directory instead.
- Bump the plugin to 0.1.7 so the snapshot refresh picks the fix up.

### Non-goals

- No backfill of past `builds.jsonl` entries that logged without tokens.
- No change to the `--project-dir`, `--session`, or `--transcript` overrides.
- No `git` subprocess dependency — resolution stays pure-stdlib file reading.

Affected capabilities: `build-telemetry` (modified). Impact:
`plugins/s/skills/build/scripts/build_report.py`,
`plugins/s/skills/build/tests/test_build_report.py`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Resolve via the worktree's `.git` file, not `git rev-parse`.** A linked
  worktree's `.git` is a *file* whose first line reads
  `gitdir: <main>/.git/worktrees/<name>`. A new
  `resolve_project_root(project_dir)` in `build_report.py` reads it
  (stdlib-only, per the constitution) and returns
  `<main>` when the gitdir path's last two parents are `worktrees` inside
  `.git`; a relative `gitdir:` path is resolved against `project_dir`. On any
  other shape, unreadable file, or a normal `.git` directory it returns the
  absolute `project_dir` unchanged. Rejected: shelling out to
  `git rev-parse --git-common-dir` — adds a runtime git dependency to a tool
  that must degrade gracefully anywhere.
- **Prefer the directory's own transcript dir; fall back only when absent.**
  Discovery first tries the slug of `project_dir` itself (a session launched
  *inside* the worktree keeps working exactly as today); only when that
  directory does not exist does it try the resolved main-checkout slug. If
  neither exists, behavior is unchanged: graceful degradation with the
  existing sentinel.
- Risk: an exotic gitdir layout (submodule `.git` files point at
  `.git/modules/...`) must not be mis-resolved — the `worktrees` parent check
  rules those out, and a unit test pins it.
