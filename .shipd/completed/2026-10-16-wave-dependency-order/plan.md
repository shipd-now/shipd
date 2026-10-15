# wave-dependency-order
Status: verified
Epic: autopilot-preflight

## Idea

Make the epic's `After` column the order build waves and the detached drive
honor, with a dependency satisfied only once its change has merged into
`main`, and make an `After` cycle an epic lint error that the waves mode
refuses rather than serialises.

### Motivation

`/s:autopilot` cannot run an epic unattended while `compute_waves` packs
`ready` members by capability disjointness alone, so a member builds beside
or before the member its `After` cell names and a dependency cycle silently
collapses into waves of one. The epic's success criterion — a member never
builds before every `After` member has merged into `main` — needs the waves
mode, the detached order, and the lint to enforce it.

### Details

- `spec_common.find_after_cycle(after_map)` returns the first cycle, in
  table order, as a slug path (`[a, b, a]`), or `[]`.
- `spec_lint._check_epic_changes` errors on a cycle, naming the path.
- `autopilot.select_and_order` raises `AutopilotError` on a cycle and
  returns `unplanned` members in dependency-layer order (flattened
  `_plan_layers`, risk-ascending then table order within a layer) — a no-op
  without an `After` column.
- `autopilot.compute_waves` admits a `ready` member to the build-wave packing
  only once every `After` dependency is merged into the base branch; the
  rest land in a new top-level `blocked` list with their `waiting_on` slugs.
- Merged-ness is a git ref check: the base branch's tree holds an archived
  entry for the dependency.
- The autopilot skill documents the `blocked` output, fetches the base
  branch before re-running `--waves`, and reports blocked members when no
  wave remains.

Affected capabilities: `epic-autopilot` (modified: `member-wave-scheduling`,
`member-selection-and-order`, `targeted-member-drive`), `shipd-spec-lint`
(modified: `epic-structural-validation`). Impact:
`plugins/s/skills/build/scripts/{autopilot,spec_common,spec_lint}.py`, their
tests, `plugins/s/skills/autopilot/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No preflight verb, overlap check, or drift detection — later members.
- No syncing of a dependent's worktree onto `main`; the build's own merge
  reconciliation and the drift members own that.
- No change to plan-wave layering or to `/s:epic-grill`'s use of plan waves.
- No `gh` call in the waves mode; it stays on-disk and deterministic.

## Implementation

- **Cycle finder lives in `spec_common.py`** as `find_after_cycle(after_map)`:
  a depth-first walk over `after_map` keys in insertion (table) order,
  following only edges to keys of the map, returning the first closed path
  including its repeated head (`[a, b, a]`; a self-edge yields `[a, a]`).
  Both `spec_lint.py` and `autopilot.py` import it, so neither imports the
  other. Rejected: a private copy in each — two definitions of one rule.
- **Lint error text:** `epic.md stub table After column has a dependency
  cycle: a -> b -> a`, appended after the per-slug checks in
  `_check_epic_changes` (`spec_lint.py:629-644`), only when the header
  carries `After`. The master's "SHALL NOT error on a cycle" clause and its
  scenario are reversed (`Dropped:` in the delta).
- **The waves mode refuses a cycle** (Q2): `select_and_order` calls
  `find_after_cycle({m.slug: m.after})` first and raises
  `AutopilotError("After column has a dependency cycle: x -> y -> x; fix
  the stub table (spec_lint.py --epic <epic>)")`, so `--waves`, the dry
  run, and a run all exit 1 through `main`'s existing handler.
  `_plan_layers` drops its trailing "pending members form waves of one"
  fallback; pending can no longer remain. Rejected: keep serialising — the
  epic names that silence as a gap.
- **Detached order follows `After`** (Q4): `select_and_order` returns
  `to_drive` as the flattened layers of `_plan_layers(unplanned,
  max(len(unplanned), 1))`; without `After` every member sits in one layer
  and the order is today's risk-ascending one. The dry-run label becomes
  `Member order (After, then risk ascending):`; the autopilot skill's
  mention of the old label follows. Rejected: leave it risk-ascending —
  the epic's own `drift-skill` (low) would build before `drift-verb`.
- **Merged-ness is a base-branch tree check** (Q1): new
  `_merged_into_base(command_fn, root, slug)` in `autopilot.py` picks the
  first ref of `origin/main`, `main` that `git rev-parse --verify --quiet
  <ref>` accepts (run in `root`), then runs `git ls-tree --name-only <ref>
  -- <content-dir>/completed/` and returns True when an entry's basename
  matches `^[0-9][0-9-]*-<slug>$` (the date or sequence prefix, then the
  slug; a suffix-only match such as `room-schema` for `schema` is no
  match). Any non-zero git exit is "not merged". The branch name is
  `spec_status.DEFAULT_AMEND_BASE` (`main`), the engine's existing base.
  Rejected: `gh pr view` (network, breaks "on-disk state alone") and the
  derived `archived` state (fires in the dependency's own unmerged
  worktree).
- **`compute_waves(root, epic, parallel, command_fn=None)`** — `command_fn`
  defaults to `_run_command` and is the only seam the tests inject; results
  are cached per dependency slug within one call. Walking `ready` members
  risk-ascending: `waiting_on = [d for d in member.after if not merged(d)]`;
  a non-empty list sends the member to `blocked` and it joins no wave,
  otherwise the capability packing runs unchanged. The result gains
  `"blocked": [{"member", "waiting_on"}]` (always present, `[]` when none);
  `skipped` keeps its meaning. `_print_waves` adds one `blocked: <slug>
  (waiting on <dep>, ...)` line per entry before the `skipped:` lines (Q3).
- **Autopilot skill text** (`plugins/s/skills/autopilot/SKILL.md`): the
  `--waves --json` shape shows `after` and `blocked`; the paragraph after it
  defines `blocked`; "Running a wave" step 6 runs `git fetch origin main`
  (best effort, from the main checkout) before re-running `--waves` so the
  tree check sees fresh refs, and when the mode returns no wave but a
  non-empty `blocked`, the drive names each blocked member and its
  `waiting_on` in the run summary and stops; the Phase 2 confirmation
  mentions the `blocked:` lines; the two "risk-ascending order" phrases
  describing the detached run become "`After`, then risk-ascending order".
- **Version bump:** `plugins/s/.claude-plugin/plugin.json` to the next patch
  above `main` at build time (`0.6.292` when planned); a sibling member in
  the same wave bumps too, so re-bump after rebasing if it lands first.

Risks: a stale `origin/main` under-reports merges (blocks, never over-admits;
the fetch in step 6 bounds it); an archive under a non-numeric prefix would
never read as merged — every engine archive uses a date prefix, and the
tests use `001-`.

## Questions and answers

### Q1: How is "merged into main" decided for a build dependency?
- **Question:** Options: (1) `gh pr view change/<dep>` reporting `MERGED`
  via the `_pr_url` seam; (2) a git ref check that the base branch's tree
  (`origin/main`, else `main`) holds `completed/*-<dep>` via `git ls-tree`;
  (3) the derived `archived` state. Recommendation at the time: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 2. `member-wave-scheduling` binds `--waves` to on-disk
  state and determinism for a given tree, which a network call violates,
  and the derived `archived` state is probed across worktrees, so it fires
  while the dependency's PR is still open. Only the base-branch tree check
  satisfies both standing positions.
- **Cited:** verified/epic-autopilot, epic/autopilot-preflight, verified/spec-status

### Q2: What does the waves mode do on an After cycle?
- **Question:** Options: (1) refuse — raise `AutopilotError` naming the
  cycle, removing the serialise-into-waves-of-one fallback; (2) keep
  serialising and leave the cycle to the lint and the preflight.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: `--waves` refuses an `After` cycle
  with `AutopilotError` naming the cycle (`x -> y -> x`), exits 1, and prints
  no wave.
- **Queued:** q-autopilot-waves-cycle-behavior
- **Relied on by:** autopilot-preflight-verb

### Q3: How is a ready member with an unmerged dependency reported?
- **Question:** Options: (1) a top-level `blocked` array of
  `{"member", "waiting_on"}` plus a `blocked:` text line, `skipped` kept for
  non-drivable states; (2) fold into `skipped` with state `blocked`.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: a top-level `blocked` array of
  `{member, waiting_on}` plus a `blocked: <m> (waiting on <dep>)` text line;
  `skipped` is unchanged.
- **Queued:** q-waves-blocked-member-reporting
- **Relied on by:** autopilot-unattended-run

### Q4: Does the detached driver's order also follow After?
- **Question:** Options: (1) yes — `select_and_order` returns dependency
  layers flattened, risk-ascending within a layer, a no-op without `After`;
  (2) no — keep risk-ascending only.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The epic's criterion covers every build and names
  `After` as the single source of order; a risk-ascending detached run
  would build `drift-skill` before `drift-verb`. The
  `member-selection-and-order` requirement must be restated accordingly.
- **Cited:** epic/autopilot-preflight, verified/epic-autopilot

## Readiness attestation

### Problem and motivation

`compute_waves` packs build waves by capability disjointness only and
serialises cycles silently, so the autopilot cannot honor `After`.

Evidence:

- `plugins/s/skills/build/scripts/autopilot.py:242-253` packs `ready`
  members by capability alone; `:176-202` serialises a cycle.
- Epic `autopilot-preflight` Decisions: "`After` is the single source of
  order" and "A cycle is an epic lint error".

### Scope and non-goals

The change covers the waves mode, the detached order, the cycle finder, the
lint, and the skill text; preflight, drift, and worktree syncing stay out.

Evidence:

- In scope: `autopilot.py:176-265` and `:1342-1365`, `spec_lint.py:629-644`,
  `spec_common.py:3122-3147`, `plugins/s/skills/autopilot/SKILL.md:97-106`
  and `:130-238`.
- Out of scope: the epic's `autopilot-preflight-verb`, `drift-verb`, and
  `autopilot-unattended-run` rows own the preflight, drift, and sync steps.

### Affected capabilities and files

Two capabilities and five source or doc files plus three test modules.

Evidence:

- Capability `epic-autopilot`: `member-wave-scheduling` (base
  75133e80b898), `member-selection-and-order` (base b42006f07a0d),
  `targeted-member-drive` (base 0da56359f2eb).
- Capability `shipd-spec-lint`: `epic-structural-validation` (base
  e09b7063f324).
- Files: `plugins/s/skills/build/scripts/autopilot.py`,
  `plugins/s/skills/build/scripts/spec_common.py`,
  `plugins/s/skills/build/scripts/spec_lint.py`,
  `plugins/s/skills/autopilot/SKILL.md`,
  `plugins/s/.claude-plugin/plugin.json`,
  `plugins/s/skills/build/tests/test_autopilot.py`,
  `plugins/s/skills/build/tests/test_spec_common.py`,
  `plugins/s/skills/build/tests/test_spec_lint.py`.
- Runnable premise: `autopilot.py autopilot-preflight --waves --parallel 3`
  → exit 0, four plan waves, no build wave.
- Runnable premise: `spec_lint.py --epic autopilot-preflight` → `OK`, exit 0.
- Runnable premise: `git rev-parse --verify --quiet origin/main` → exit 0;
  `git ls-tree --name-only origin/main -- .shipd/completed/` lists
  `.shipd/completed/2026-10-15-room-schema`.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/build/tests -p test_autopilot.py` → 119 tests OK.

### No open task-shaping decision

Four decisions existed; all are settled.

Evidence:

- Merge detection (base-branch tree check): oracle, Q1.
- Cycle handling in the waves mode (refuse): PLANNER default, Q2.
- Blocked-member reporting (`blocked` array): PLANNER default, Q3.
- Detached order follows `After`: oracle, Q4.
