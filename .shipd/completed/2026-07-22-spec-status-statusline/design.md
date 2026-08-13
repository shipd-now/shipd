## Context

The homegrown engine owns the spec format end to end, so we can attach a
lifecycle to specs without fighting an external tool. The reference is the
shipd statusline (`integrations/statusline.sh` in shipd-now-old): a bash
script for Claude Code's `statusLine` setting that reads the session JSON on
stdin, inspects the workspace, and prints one ANSI-colored line. We reuse that
shape but point it at `am/spec/` and add an explicit "current spec" selection
plus a five-stage status pipeline.

## Goals / Non-Goals

**Goals:**
- A visible, explicit status on every change, kept honest by the pipeline.
- Explicit selection of the spec being worked on, in repo-local state.
- A fast, dependency-free statusline: `☢️ <change> · <status> · <done>/<total>`.
- Lint enforcement of the new proposal header so the ceremony stays uniform.

**Non-Goals:**
- No epic/initiative/theme segments (shipd concepts with no analogue here).
- No cross-repo workspace walking — the statusline reads the session cwd only.
- No archival/history of status transitions; the current value is enough.
- No enforcement of legal transition *order* (e.g. blocking ready→verified);
  the pipeline skills drive normal order, the CLI allows explicit overrides.

## Decisions

### D1 — Status lives in proposal.md, below a new mandatory title
`proposal.md` line 1 is `# <change-name>` (matching the directory slug);
the first non-blank line after it is `Status: <status>`. The engine never
parses proposal.md (lint and merge read only `specs/*/spec.md`), so this is
grammar-safe by construction; `spec_lint.py` gains an explicit check instead.
- *Why:* proposal.md is the change's face; a status file or delta-spec
  preamble would be invisible or engine-risky (metadata regex, base hashes).
- *Alternatives:* dedicated `status` file (rejected: fifth artifact, invisible
  in review); delta spec.md preamble (rejected: merge treats preamble as
  ignorable and the `id:`/`base:` grammar is strict).

### D2 — Five stages, pipeline-owned transitions, manual override
`draft` (authoring, may be incomplete) → `ready` (lint-clean, approved, not
started) → `active` (some tasks done or in progress) → `complete` (all tasks
done) → `verified` (verification passed). Ownership:
- plan emits `draft`; promotion to `ready` happens at the approval gate
  (plan's confirmation, or build's Phase 2 go-ahead when build authors).
- build sets `active` when it spawns teammates, `complete` when the
  coordinator shows `pending=0 in_progress=0`, `verified` when Phase 5
  verification passes — each via the CLI, before merge/archive.
- `sync` derives only within {ready, active, complete}: `done==total>0` →
  complete; `done>0 or in_progress>0` → active; else ready. It never touches
  `draft` (entering the pipeline is a human/orchestrator act) and never
  demotes `verified`. `set` may force any value explicitly.
- *Why:* derivable states stay derived (honest), judgment states stay
  explicit (draft, verified). Demotion complete→active via sync is correct
  when a task is released.

### D3 — CLI: `spec_status.py`, stdlib Python, beside the engine scripts
`plugins/s/skills/build/scripts/spec_status.py`, `#!/usr/bin/env python3`,
stdlib only, run from the repo root (like `spec_lint.py`; `--root` optional
override). Verbs, all defaulting `<change>` to the selected spec:
- `use <change>` — validate `am/spec/changes/<change>/` exists (archive
  excluded), write `.shipd/state.json` (`{"current_spec": "<change>"}`,
  created with `indent=2`), print the selection.
- `current` — print the selected change name, or nothing; always exit 0.
- `show [change]` — print `<change>: <status> (<done>/<total> tasks)`;
  status `?` when the header is missing/invalid; omit the task counts part
  when tasks.md is absent.
- `set <status> [change]` — validate the status value, rewrite the existing
  `Status:` line, or insert the `# <change>` + `Status:` header at the top if
  the proposal lacks one; print the new status.
- `sync [change]` — apply the D2 derivation; print the (possibly unchanged)
  resulting status.
Errors (unknown change, no selection when one is needed, bad status value,
missing proposal.md for set/sync) print `Error: ...` to stderr, exit 1.
- *Why Python over bash:* JSON state and header rewriting are awkward in bash;
  the unittest harness already exists. *Why not Go:* no toolchain in repo.

### D4 — Statusline: bash 3.2-safe, reads files directly, no Python spawn
`plugins/s/integrations/statusline.sh`, modeled on shipd's script: reads the
session JSON on stdin, extracts `workspace.current_dir` with sed (fallback
`$PWD`), and stays **silent (exit 0, no output)** when
`<dir>/am/spec/changes` does not exist. It never invokes Python — statuslines
render on every prompt, so it greps `.shipd/state.json`, `proposal.md`,
and `tasks.md` directly.
- Selection: `current_spec` from state.json; when unset, auto-select if
  exactly one non-archive change dir exists; when none exist print
  `☢️ no active specs`; when several print `☢️ <n> specs · none selected`.
  A selected-but-missing change dir falls back to the unselected logic.
- Render: `☢️ <name> · <status> · <done>/<total>` joined by ` · ` (the
  ` · ` separator uncolored; segments colored). Status missing/invalid → `?`.
  Task segment omitted when tasks.md is missing. Done counts `- [x]`; total
  counts `- [ ]`, `- [~]`, `- [x]`.
- ANSI colors: name light blue (`\033[94m`); status by value — draft
  `\033[90m`, ready `\033[94m`, active `\033[33m`, complete `\033[32m`,
  verified `\033[92m`, `?` `\033[90m`; counts default color; reset after each
  segment. macOS bash 3.2: no mapfile, no `$'\u…'`, no `set -u` reliance.
- Registration: `.claude/settings.json` gets
  `{"statusLine": {"type": "command", "command": "bash plugins/s/integrations/statusline.sh"}}`
  (project-relative — Claude Code runs the command from the project dir).

### D5 — Master library seeded as this change's pre-step
`am/spec/specs/` was seeded from the frozen `openspec/specs/` bootstrap
library (10 capabilities, 51 requirements): boilerplate dropped, a
`# <capability>` preamble added, `id:` slugs generated from titles. The
library lints clean. `openspec/` stays as frozen history; future deltas can
now MODIFY real masters with meaningful `base:` hashes.

### D6 — Lint scope for the proposal header
`spec_lint.py`'s change lint reports an **error** when `proposal.md` is
missing, when no `Status:` line appears in its first 5 non-blank lines, or
when the value is not one of the five statuses; and when line 1 is not
`# <change-name>` matching the change directory slug. Master/library lint is
untouched. The sample test fixture gains the header so existing tests stay
green.

## Risks / Trade-offs

- **Status drift** (file says active, work moved on) → the pipeline calls the
  CLI at every boundary and `sync` re-derives from checkboxes; the statusline
  reads live counts either way.
- **Statusline wrong dir in multi-repo sessions** → uses the session's
  `workspace.current_dir`, same mitigation as shipd; silent when the dir has
  no am/spec.
- **Lint break on pre-header changes** → only in-flight changes are linted;
  the only in-flight change is this one, which carries the header. Fixtures
  updated in the same change.
- **Emoji width quirks in terminals** → ☢️ includes a variation selector;
  rendering is the terminal's concern, the script just prints the bytes.
