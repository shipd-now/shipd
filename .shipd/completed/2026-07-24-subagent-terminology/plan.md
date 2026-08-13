# subagent-terminology
Status: verified

## Idea

The build skill and its surrounding docs call execution agents "teammates" —
terminology that predates the cutover to standard Claude Code vocabulary. The
user wants "teammates" renamed to "sub-agents" in all of the skills and
documentation, so the plugin's language matches the platform's.

In scope: every live file using the term — `plugins/s/skills/build/SKILL.md`
(30 occurrences), `plugins/s/skills/build/references/teammate-prompt.md`
(renamed to `subagent-prompt.md`, plus its content), the header comments of
`plugins/s/skills/build/scripts/claim_task.sh`, the root `README.md`, and the
four master capabilities whose requirements use the word (`build-spec-lifecycle`,
`build-context-gate`, `build-telemetry`, `build-task-coordination`) — those are
updated via the MODIFIED deltas in this change, applied by the merge engine,
never edited by hand.

Out of scope: `am/spec/changes/archive/` and `openspec/` (immutable archives),
and this change's own artifacts, which necessarily mention the old word.

Capabilities modified: `build-spec-lifecycle`, `build-context-gate`,
`build-telemetry`, `build-task-coordination` (terminology-only content
rewrites of eight requirements; no behavioral change).

## Implementation

- **Word mapping:** `teammate` → `sub-agent`, `teammates` → `sub-agents`,
  `Teammate` → `Sub-agent` (and `Execution Teammate` → `Execution Sub-agent`
  in the prompt title). Words containing "team" but not "teammate" (e.g.
  "Execution Team") are left alone unless a sentence reads oddly.
- **File rename:** `references/teammate-prompt.md` →
  `references/subagent-prompt.md` via `git mv`; the only inbound references
  are in `plugins/s/skills/build/SKILL.md` (paths list and Phase 3), updated
  in the same pass. Filename uses `subagent` (no inner hyphen) as the slug of
  "sub-agent".
- **Master specs change only through deltas.** The eight requirement rewrites
  ride the `specs/` deltas with `base:` hashes; `spec_merge.py` applies them
  at merge time (design rule inherited from the format: sub-agents never edit
  `am/spec/specs/`).
- **Drift fix bundled:** `build-updates-spec-status`'s scenario still said
  "the proposal's status line" — corrected to "the plan's status line" while
  its content is being rewritten anyway (leftover from the lean-spec-format
  cutover).
- **Snapshot discipline:** editing `plugins/s/` requires a plugin version
  bump (cache is keyed by version — learned on the previous build), so the
  change bumps `plugins/s/.claude-plugin/plugin.json` to `0.1.2` and
  refreshes the snapshot as its final task.
- **Risk:** near-zero — no code paths change; `claim_task.sh` edits are
  comments only. Verification greps for surviving live occurrences and runs
  the full test suite.
