## Context

`spec_status.py` (spec-status capability) currently exposes `use`, `current`,
`show`, `set`, `sync`. `set` is a raw write. The lint logic that knows whether
a change is structurally valid lives in `spec_lint.py` (`lint_change`). This
change moves transition honesty into the binary and adds the interactive
override flow as a skill, keeping the model out of the checking logic.

## Goals / Non-Goals

**Goals:**
- One setter, guarded by default; overrides are explicit (`--force`) and, via
  the skill, always user-consented.
- Deterministic, testable guards in the Python binary — the skill only
  orchestrates prompts, it never re-implements checks.
- Scriptable additions: `validate` and bare `status`.

**Non-Goals:**
- No transition-*order* enforcement (any target is reachable if its guards
  pass — e.g. draft→verified with everything checked is allowed).
- No changes to `sync` (its derivation rules already have their own window).
- No git/repo-state checks (uncommitted work etc.) in guards.

## Decisions

### D1 — Verb surface: `set` becomes guarded `set-status`; add `validate`, `status`
`set` is removed, not kept alongside — two setters would make the guarded path
optional and the API ambiguous. `set-status <status> [change] [--force]` is
the only way to write a status. `validate [change]` runs change-scoped
structural validation. `status [change]` prints the bare value (exit 0; `?`
when missing/invalid), complementing the human `show`. `use`/`current`/`show`/
`sync` are unchanged. The old name disappears in the same change that updates
every caller (plan/build SKILL.md), so nothing references `set` afterwards.

### D2 — Guard matrix (evaluated in the binary, not the skill)
For `set-status <target>`:
- target `draft` — no guards (demoting to draft is always allowed; a draft
  may legitimately be structurally incomplete).
- target `ready` or `active` — the change must **validate**: `lint_change`
  (imported from `spec_lint.py`, same-directory import like `spec_common`)
  returns no errors.
- target `complete` or `verified` — validate as above **and** the task
  checklist is finished: `tasks.md` exists, has at least one checkbox, and
  shows nothing pending (`- [ ]`) or in progress (`- [~]`).
`--force` bypasses all guards. It never bypasses status-*value* validation
(an unknown status word is always an `Error`, exit 1).

### D3 — Refusal contract (machine-readable, distinct from errors)
A guard refusal: writes nothing, prints one or more lines to stderr — the
first beginning exactly `Refused: ` with a human reason including concrete
counts (e.g. `Refused: setting complete requires all tasks done (7/10 done,
1 in progress)`), followed by the individual validation errors when structure
was the problem — and exits with code **3**. Exit codes: 0 success, 1 error
(unknown change/status, missing proposal, no selection), 2 usage, 3 refusal.
The skill distinguishes "ask about override" (3) from "real error" (1) by
exit code alone.

### D4 — The `am:status` skill is a thin interactive wrapper
New skill at `plugins/s/skills/status/SKILL.md` (invoked `/s:status`),
running on the session model with no teammates. Its argument grammar:
- `/s:status` or `/s:status status [change]` → run `status` (and `show` for
  the friendly line), report.
- `/s:status validate [change]` → run `validate`, report OK or the errors.
- `/s:status set-status <status> [change]` → run `set-status`; on exit 3,
  show the `Refused:` reason and AskUserQuestion with exactly two options —
  "Override anyway" (re-run with `--force`) and "Leave unchanged" — defaulting
  to leave. The skill SHALL never pass `--force` on its own initiative; only
  after the user picks the override option. On exit 1, report the error (no
  question).
The skill resolves `${CLAUDE_PLUGIN_ROOT}` and runs the CLI from the repo
root, mirroring the build skill's conventions.

### D5 — Pipeline call sites move to the guarded verb
`plan/SKILL.md` (`set ready`) and `build/SKILL.md` (`set ready`, `set active`,
`set verified`) switch to `set-status`. Each call site already sits behind the
exact gate its guard checks (lint-clean at ready/active; tasks done at
verified), so no `--force` appears anywhere in the pipeline docs. If a
pipeline call is ever refused, that is a real inconsistency that should stop
the build — the refusal surfaces it.

## Risks / Trade-offs

- **Import coupling to spec_lint** → `lint_change` is a stable, tested
  function in the same directory; the existing sibling-import pattern
  (`spec_lint` → `spec_common`) is reused. Tests cover the import path via
  subprocess like all other CLI tests.
- **Exit-code 3 as API** → documented in the CLI help and the skill; tests pin
  it. Existing callers used exit 0/1 only, and no caller of `set` remains
  after D5.
- **`set` removal breaks muscle memory / old docs** → archived changes retain
  historical references only; live docs are all updated in this change.
