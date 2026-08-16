# shipd constitution

This file is **optional**. When it is present, the planning and build flows load
it and treat every rule below as a **binding constraint** on designs, emitted
artifacts, and implementations — a rule here is not a suggestion. When the file
is absent, all tooling behaves exactly as it otherwise would; nothing warns or
errors about a missing constitution.

These are this repository's non-negotiable engineering rules.

## Technology constraints

- **The spec engine is stdlib-only Python 3, with two named exceptions.**
  Every script under `plugins/s/skills/build/scripts/` uses only the Python 3
  standard library — no third-party imports, no network access — except:
  `dashboard.py`'s `tui` rendering, which may import the pinned `textual`
  (`requirements.txt`, installed in CI only for the `tests_textual` suite);
  and declared-pipeline validation, which may lazily import the pinned
  `pydantic` (`requirements.txt`) on that path only. Every other engine
  script, including the rest of `dashboard.py` and the delivery engine
  `autopilot.py` depends on, stays stdlib-only and importable without
  `textual` installed; and every engine script, `dashboard.py` included, stays
  importable without `pydantic` installed.
- **`statusline.sh` stays POSIX-compatible.** The status line targets the
  bash 3.2 that ships with macOS: no `mapfile`, no `set -u`, no associative
  arrays, no `$'\uXXXX'` escapes. No Python or Node is spawned from it.

## Testing standards

- **Every engine change carries tests.** Any change to the engine scripts or
  the status line lands with matching tests under
  `plugins/s/skills/build/tests/`.

## Workflow discipline

- **Never commit or push to `main` directly.** Every change ships as an
  auto-merging PR from its `change/<name>` branch, gated by the `ci` status
  check — no exceptions, including the orchestrator's own merges.
- **One change = one worktree = one branch = one PR.** A change is developed in
  `.worktrees/<name>` on branch `change/<name>`, and its whole lifecycle
  (plan → build → merge/archive) runs there so artifacts, implementation, and
  applied specs travel in a single PR.
- **Report PRs with the full URL.** Any status update or completion report that
  references a PR gives its full clickable URL, never just the number.
- **Durable conventions are checked in.** Workflow rules and conventions live in
  `AGENTS.md` or the specs, never recorded only in an assistant's private
  memory.
- **Refresh the plugin snapshot from the main checkout after the PR merges.**
  The plugin runs from a cached snapshot whose marketplace source points at the
  main checkout, so after a change touching `plugins/s/` merges and main is
  pulled, run `claude plugin update s@shipd` (or press `u` in the
  `/plugin` UI) there so the updated skills load in the next session.
- **Completed changes are immutable.** Changes under
  `.shipd/completed/` are never edited or re-merged once applied.
