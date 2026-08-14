# guarded-status-skill
Status: verified

## Why

Status transitions are currently unguarded: `spec_status.py set` writes any of
the five values no matter what state the change is actually in — you can stamp
`complete` with half the tasks unchecked or `ready` on a spec that doesn't
lint. The pipeline stays honest only because the skills happen to call it at
the right moments. We want the honesty enforced in the binary: transitions are
checked (structure valid; for `complete`/`verified`, all tickets checked), and
overrides become an explicit, user-consented act — surfaced through a small
interactive skill that can ask before forcing.

## What Changes

- **BREAKING (CLI)**: `spec_status.py set` is replaced by a guarded
  `set-status <status> [change]`: it validates the change's structure and the
  transition's requirements before writing, refuses with a distinct exit code
  and a `Refused:` reason when guards fail, and accepts `--force` to bypass
  guards after the caller has obtained consent.
- New `validate [change]` verb: structural validation of a change (delta
  specs, proposal header, artifact presence) from the status CLI.
- New `status [change]` verb: prints the bare status value (scriptable
  companion to the human-oriented `show`).
- New `am:status` skill exposing `status`, `validate`, and `set-status`
  commands; on a guard refusal it asks the user (AskUserQuestion) whether to
  override and only then re-runs with `--force`.
- The plan and build skills switch their pipeline calls from `set` to
  `set-status` (their phase boundaries satisfy the guards naturally).

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `spec-status`: the status CLI verb surface changes (guarded `set-status`,
  new `validate` and `status` verbs, `set` removed); transition guards and the
  interactive status skill are added as new requirements.

## Impact

- Modified: `plugins/s/skills/build/scripts/spec_status.py`,
  `plugins/s/skills/build/tests/test_spec_status.py`,
  `plugins/s/skills/build/SKILL.md`, `plugins/s/skills/plan/SKILL.md`.
- New: `plugins/s/skills/status/SKILL.md` (the `am:status` skill).
- No changes to `spec_lint.py` (its change-lint functions are imported and
  reused), the statusline, or the merge engine.
