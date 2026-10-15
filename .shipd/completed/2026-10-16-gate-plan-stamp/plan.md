# gate-plan-stamp
Status: verified
Epic: autopilot-preflight
Theme: reliability

## Idea

Make `spec_gate.py` stamp every passing plan with the `main` commit it was
gated against and a hash of the content it approved, and add a read-only
`--check` mode that runs the same checks without writing anything.

### Motivation

The autopilot's preflight and the drift verb need a deterministic anchor per
plan — which commit the plan saw and what content the gate approved — and the
gate records neither today, so a plan edited after gating or stale against
moved code looks exactly like a fresh one and the unattended run stops to ask.

### Details

- `spec_gate.py <change>` on a pass writes `Planned-at: <sha>` and
  `Gated-hash: <hash>` into the plan header, after any existing metadata line.
- `spec_gate.py <change> --check` runs every gate check (plus a `Gated-hash`
  mismatch check on a stamped plan) and exits as the gate would, writing
  nothing and moving no status.
- The header grammar accepts hyphenated keys; the linter and `show` recognize
  the two stamp keys and validate their hex shape.

Affected capabilities: `context-gate` (modified, two added requirements),
`shipd-spec-format` and `shipd-spec-lint` (modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py`, `spec_gate.py`,
`spec_lint.py`, their test suites, `.shipd/README.md`,
`plugins/s/.claude-plugin/plugin.json`. No new dependency.

### Non-goals

- No drift detection, preflight rubric, or wave ordering — later members.
- No skill text changes: every caller invokes the gate positionally today.
- No stamp verification inside the writing gate: a mismatch is only ever a
  `--check` finding, because the writing gate rewrites the stamp on pass.
- No file-timestamp comparison anywhere (epic non-goal).

## Implementation

- **Stamp helpers live in `spec_common.py`**, not `spec_gate.py`: the drift
  verb (member `drift-verb`) lives in `spec_status.py`, which `spec_gate.py`
  imports, so the helpers must sit below both. Add `STAMP_KEYS =
  ("Planned-at", "Gated-hash")`, `PLANNED_AT_RE` (`^[0-9a-f]{7,40}$`),
  `GATED_HASH_RE` (`^[0-9a-f]{12}$`, from `HASH_LENGTH`), extend
  `METADATA_KEYS` with both keys (so `show` prints them through its existing
  filter), and three functions: `read_plan_stamp(text) -> (planned_at,
  gated_hash)` (each `None` when absent), `plan_gated_hash(text) -> str`, and
  `write_plan_stamp(text, planned_at, gated_hash) -> str`.
- **Widen `METADATA_LINE_RE`** to `^([A-Za-z][A-Za-z0-9-]*):\s*(.*?)\s*$`.
  Today a hyphenated key ends the block silently: a `Planned-at:` line placed
  before `Epic:` makes `parse_plan_metadata` return `[]` while lint passes.
  Widened, such a line is a recognized key on plans and an unrecognized key
  on epics, briefs, and PRDs — the loud failure a hand-written stamp deserves.
- **The hash.** `plan_gated_hash` drops the first `Status:` line and every
  header-block stamp line, then returns `content_hash` of the rest — the
  engine's one normalized 12-hex rule, so a whitespace-only edit is not a
  change. Callers pass text with the `## Context insufficient` section
  stripped (gone on a pass; `--check` strips before hashing). Rejected:
  hashing only `## Idea`/`## Implementation` — the ledger and attestation are
  what a re-plan edits, so they must count.
- **Placement.** `write_plan_stamp` replaces existing stamp lines in place,
  else appends `Planned-at` then `Gated-hash` as the last lines of the
  metadata block (directly after `Status:` when no block exists). A `None`
  `planned_at` writes no `Planned-at` line and removes a stale one, so the
  plan falls back to the epic's documented last-commit rule.
- **`Planned-at` resolution.** `git -C <plan dir> merge-base HEAD <base>`,
  `--base` defaulting to `main`, anchored on the plan's directory exactly as
  `spec_status.cmd_epic_amend_check` anchors on the epic's — correct in the
  main checkout, a linked worktree, and an external store. Rejected:
  `rev-parse main` — in a worktree, local `main` may be ahead of the commit
  the branch's code is based on, under-reporting drift. Any git failure (no
  git, no work tree, unresolvable ref) yields `None` plus one stderr `note:`
  line, never a gate error: the gate's verdict is about context.
- **Pass path order.** Strip the gate section → resolve the sha →
  `write_plan_stamp(text, sha, plan_gated_hash(text))` → write the file →
  `ss.write_status(root, change, "ready")` (unchanged) → `store_autocommit`
  as today. Print the existing `PASS:` line, then `stamp: Planned-at
  <sha|none> Gated-hash <hash>`. The reject path is untouched and leaves any
  existing stamp lines as they are.
- **`--check` is read-only by construction.** It runs `collect_findings`
  and, when `read_plan_stamp` finds a `Gated-hash`, adds a finding when
  `plan_gated_hash` of the stripped text differs: `gated-hash mismatch:
  plan.md was edited after it was gated (stamp <a>, content <b>); re-gate
  with spec_gate.py <change>`. It never calls `write_status`, writes no file,
  runs no autocommit, records no flow snapshot. Output mirrors the gate with
  a `(check)` marker: `PASS (check): ...` exit 0, `REJECTED (check): ... (n
  finding(s)):` plus dot-points exit 2, general errors exit 1. An unstamped
  plan gets no mismatch finding, so every pre-feature plan stays checkable.
- **Lint.** `check_plan_metadata` validates a stamp key's value against its
  own regex instead of `KEBAB_RE`, naming the value; nothing else changes.
  The linter never recomputes the hash.
- **Risk:** a later member edits the stamp lines by hand. Guard: the
  `--check` mismatch finding and the lint hex-shape check make that loud.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next patch
  above `main` at build time (`0.6.293` when revised; re-bump after a rebase
  if a sibling lands first), per AGENTS.md.

## Questions and answers

### Q1: Does `--check` report a `Gated-hash` mismatch?
- **Question:** Should read-only `spec_gate.py --check` itself report a
  finding when a stamped plan's content no longer matches its `Gated-hash`,
  so the preflight gets the edited-after-gate signal from one call? Options:
  (1) `--check` reports a `gated-hash mismatch` finding and exits 2, while
  the writing gate never does because it rewrites the stamp; (2) `--check`
  runs only the existing checks and the preflight verb compares the hash
  through a `spec_common` helper. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: `--check` reports a `gated-hash
  mismatch` finding and exits 2; the preflight reads it from the one `--check`
  call it already makes and never recomputes the hash.
- **Queued:** q-gate-check-gated-hash-mismatch
- **Relied on by:** autopilot-preflight-verb, autopilot-unattended-run

## Readiness attestation

### Problem and motivation

The gate records neither the commit a plan was gated against nor the content
it approved, so the preflight and drift members have no deterministic anchor.

Evidence:

- Epic `autopilot-preflight`: Decisions "The plan stamp" and
  "Edited-after-gate fails the preflight"; Design "Stamp layer".
- `plugins/s/skills/build/scripts/spec_gate.py:376-390` — the pass path
  writes only the stripped section and `Status: ready`.

### Scope and non-goals

The change touches the gate, the header grammar, lint, and `show`; drift,
preflight, waves, and skill prose stay with later members.

Evidence:

- Epic `## Changes` row `gate-plan-stamp` with an empty `After` cell.
- Positional callers: `autopilot.py:347-352`, `skills/plan/SKILL.md:781`,
  `skills/epic-grill/SKILL.md:220`.

### Affected capabilities and files

Three capabilities and five code files: the stamp needs a grammar change
(`spec_common`), a writer and a check mode (`spec_gate`), and recognition
(`spec_lint`, `show`).

Evidence:

- `context-gate` `context-gate-verb` base `9851e28d228d`;
  `shipd-spec-format` `plan-header-metadata-lines` base `e2fd4dd62f30`;
  `shipd-spec-lint` `plan-metadata-validation` base `1e4c19b3a03a`.
- `spec_common.py:86` `METADATA_KEYS`, `:117` `METADATA_LINE_RE`,
  `:3013-3038` `parse_plan_metadata`, `:3178-3192` `content_hash`;
  `spec_lint.py:378-437`; `spec_status.py:643-644` (`show` filter),
  `:2483-2500` `_git_capture`, `:2545-2600` `cmd_epic_amend_check`.
- Runnable: `spec_gate.py x --root <tmp>` on a non-git root → exit 2,
  `REJECTED:` line, `Status: rejected`.
- Runnable: `Planned-at: abc` then `Epic: e` under `Status:` →
  `spec_lint.py x` exit 0 and `parse_plan_metadata` returned `[]`.
- Runnable: `git merge-base HEAD main` in the worktree → `076a9ef…`, equal
  to `rev-parse main`; `test_spec_gate` → 25 tests OK.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Base resolution (merge-base, `--base main`): investigation.
- Helper placement (`spec_common.py`) and stamp placement (last in block):
  investigation, runnable premise above.
- `--check` mismatch finding: PLANNER default, Q1, oracle `INSUFFICIENT`.
