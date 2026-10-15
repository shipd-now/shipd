# drift-verb
Status: verified
Epic: autopilot-preflight
Theme: reliability

## Idea

Add `spec_status.py drift <change>` — with `--epic <slug>`, `--base`, and
`--json` — reporting from local git alone which of a gated plan's cited files
changed on `main` since its stamp, which cited symbols vanished, and which
delta bases went stale.

### Motivation

The autopilot's preflight and its pre-build drift step cannot tell whether a
`ready` plan still matches the code it was gated against, so a plan whose
cited files or symbols moved builds blind or stops to ask, and `/s:drift` has
no list of flagged members to put before a model.

### Details

- `drift [change]`: stamp from `sc.read_plan_stamp`, else the plan's last
  commit; findings `file-drift`, `symbol-gone`, `stale-base`; exit 0 clean,
  4 on findings, 1 error; keyed text header or one `--json` object.
- `drift --epic <slug>`: every stub member with a plan, measured from its
  hosting root; unmeasurable, unplanned, and archived members `skipped`.
- The gate's path-token rule moves into `spec_common` as `cited_paths` and
  gains a sibling `cited_symbols`; `spec_gate._check_task_paths` consumes it
  with unchanged behavior.
- `cmd_check_base` splits into `check_base_findings` plus printing so drift
  reuses the `stale-base` computation.

Affected capabilities: `spec-status` (added `drift-verb`, `drift-epic-mode`).
Impact: `plugins/s/skills/build/scripts/spec_status.py`, `spec_common.py`,
`spec_gate.py`, `plugins/s/skills/build/tests/test_spec_status.py`,
`test_spec_common.py`, `plugins/s/.claude-plugin/plugin.json`. No new
dependency.

### Non-goals

- No model, `/s:drift` skill, preflight rubric, or worktree sync — later
  members own those.
- No `Gated-hash` comparison: edited-after-gate is `spec_gate.py --check`'s
  finding (member gate-plan-stamp).
- No `missing-master` or `id-collision` in the drift report; `check-base`
  keeps them, per the epic's three finding kinds.
- No mtime comparison; no `docs/` page (a later `/s:document` pass).

## Implementation

- **Stamp** (`_drift_stamp(hosting_root, change)`): `sc.read_plan_stamp`'s
  `planned_at` → `("stamp", sha)`; else `git -C <hosting_root> log -1
  --format=%H -- <plan.md relpath>` → `("plan-commit", sha)`; empty → reason
  `no-stamp`; a stamp `git rev-parse --verify --quiet <sha>^{commit}` rejects
  → `unknown-stamp`. Git is anchored on the root hosting the change — the
  repository whose files the plan cites — through the existing `_git_capture`.
- **Base** (Q1): `--base` defaulting to `DEFAULT_AMEND_BASE`; resolved once
  per invocation with `rev-parse --verify --quiet`; failure is `StatusError`
  (exit 1) in both modes. Rejected: `origin/main`-first — contradicts the
  epic's `<stamp>..main` measurement.
- **Cited tokens in `spec_common.py`**: move `BACKTICK_RE` and
  `PATH_TOKEN_RE` from `spec_gate.py:70-76` (the gate rebinds them from
  `sc`); add `LINE_SUFFIX_RE` (`:\d+(?:-\d+)?$`), `CALL_SUFFIX_RE`
  (`\(.*\)$`), `SYMBOL_TOKEN_RE` (`^(?:--[A-Za-z][\w-]*|[A-Za-z_][\w.]*)$`),
  `VERSION_BUMP_EXEMPT_PATHS = ("plugins/s/.claude-plugin/plugin.json",)`,
  `cited_paths(text, strip_line_suffix=False)` (ordered, de-duplicated; skips
  tokens with `://` or no `/`), and `cited_symbols(text)` (call suffix
  stripped; path-shaped tokens excluded). Drift reads `plan.md`, `tasks.md`,
  and every `specs/*/spec.md`, strips line suffixes, and drops `artefacts/`
  tokens and the exempt paths (Q2). Every identifier counts: a prose word like
  `main` exists at both refs, so the present-then-absent rule leaves it inert.
- **file-drift**: per cited path, `git log --format=%h <stamp>..<base> --
  <path>`; a non-empty list is a finding `(path, commits)`. A path that never
  existed yields no commits, so no existence check is needed.
- **symbol-gone**: `present(ref, symbols)` = the set of literals from `git
  grep -o -h -w -F -e s1 -e s2 ... <ref>` (exit 1 → empty set; other failures
  raise). Grep the base for every symbol first, then the stamp for the missing
  ones only — two calls per change; `gone` keeps citation order. Both greps
  exclude the change's own directory (`-- . ':(exclude)<content-dir>/planned/
  <change>'`): a `plan-commit` stamp's tree contains the plan, which names
  every symbol it introduces, so without the exclusion every introduced
  symbol would read as present at the stamp and absent at the base.
- **stale-base**: `check_base_findings(root, change)` returns the tuple list
  `cmd_check_base` builds today; drift keeps `kind == "stale-base"`. The
  hosting root's master library is what that checkout's `check-base` sees.
- **Text shape** (single): `change:`, `root:`, `planned-at: <sha> (<source>)`,
  `base: <ref> <sha>`, then `file-drift <path> <n> (<sha>, ...)`,
  `symbol-gone <name>`, `stale-base <cap>/<id> (expected a, actual b)`, then
  `drift: N finding(s).` or `drift: clean (no findings).` — the check-base
  summary grammar.
- **JSON shape**: `{"change","root","planned_at","stamp_source","base":
  {"ref","sha"},"findings":[{"kind":"file-drift","path","commits"},
  {"kind":"symbol-gone","symbol"},{"kind":"stale-base","capability","id",
  "expected","actual"}]}`; printed with `json.dumps` like `locate`.
- **`--epic`** (Q3): epic via `_epic_hosting_root`; members via `_epic_rows`
  in table order; `_member_state_with_root` gives the hosting root; states
  `unplanned`/`archived` and reasons `no-stamp`/`unknown-stamp` go to
  `skipped` (`skipped: <slug> (<reason>)`; JSON `{"member","reason"}`), never
  a finding. Blocks separated by one blank line, skipped lines, one summary.
  JSON: `{"epic","base","members":[...],"skipped":[...]}`. Exit 4 when any
  member has a finding. `change` and `--epic` together: `parser.error`
  (exit 2); neither: `_resolve_change`. Rejected: counting an unmeasurable
  member as drift — the preflight already fails non-`ready` members.
- **Single-change unmeasurable** (Q3): `StatusError` "change '<c>' has no
  Planned-at stamp and its plan.md has no commit; gate it with spec_gate.py
  <c>" (or naming the unknown sha), exit 1 like `epic-amend-check`.
- **Docstrings**: add `drift` to the `spec_status.py` verb list and to its
  exit-code paragraph (4 findings); update `spec_gate.py`'s check-3 note.
- **Version bump**: `plugins/s/.claude-plugin/plugin.json` to the next patch
  above `main` at build time (`0.6.292` when planned); re-bump after a rebase
  if a wave sibling lands first.

Risks: a removed symbol still named in prose at the base is not reported —
the epic's rule, accepted; `git grep` on prose-word symbols prints many
literals, bounded by `-o -h` and read in-process.

## Questions and answers

### Q1: Which ref does drift measure against?
- **Question:** Options: (1) `main` through `--base` defaulting to `main`,
  the shape `spec_gate.py --base` and `epic-amend-check --base` use; (2)
  `origin/main` when it resolves, else `main`, as wave-dependency-order's
  merged check does. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The epic defines drift as `git log <stamp>..main`
  and handles a stale local `main` by syncing the dependent's worktree before
  its drift check, not by swapping the ref.
- **Cited:** epic/autopilot-preflight, verified/spec-status

### Q2: Is the version-bump file exempt from file-drift?
- **Question:** Options: (1) exempt `plugins/s/.claude-plugin/plugin.json`
  through one `spec_common` constant the preflight overlap check reuses; (2)
  no exemption, leaving it to `/s:drift`'s judgment. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default:
  `plugins/s/.claude-plugin/plugin.json` is exempt from file drift through the
  shared `VERSION_BUMP_EXEMPT_PATHS` constant the preflight overlap check
  reuses; flagged for `/s:epic autopilot-preflight amend`, since the epic's
  drift Decision names no carve-out.
- **Queued:** q-drift-verb-plugin-json-exemption
- **Relied on by:** autopilot-preflight-verb, detached-drift-replan

### Q3: How is an unmeasurable plan reported?
- **Question:** Options: (1) single-change exit 1 error naming the remedy;
  `--epic` lists the member as `skipped` with its reason and counts no
  finding; (2) a drift finding (exit 4) in both modes. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: single-change mode exits 1 naming
  `spec_gate.py <change>` as the remedy; `--epic` lists `skipped: <slug>
  (no-stamp)` and counts no finding.
- **Queued:** q-drift-verb-unmeasurable-plan
- **Relied on by:** drift-skill, autopilot-unattended-run, detached-drift-replan

## Readiness attestation

### Problem and motivation

The engine has no verb measuring whether a gated plan still matches the code,
so the unattended run cannot detect drift before building.

Evidence:

- Epic `autopilot-preflight`: Decisions "Commits, not timestamps", "Cited
  files and symbols", "Drift packaging"; Design "Detection layer".
- `plugins/s/skills/build/scripts/spec_status.py:1289-1361` — `check-base`
  compares deltas only; no verb reads git history.

### Scope and non-goals

One verb in two modes, the shared token helpers, and a check-base refactor;
skill, preflight, sync, and hash comparison stay with other members.

Evidence:

- Epic `## Changes` rows `drift-skill`, `autopilot-preflight-verb`,
  `autopilot-unattended-run` (After: `drift-verb`).
- `gate-plan-stamp` plan: `--check` owns the `gated-hash mismatch` finding.

### Affected capabilities and files

One capability and three scripts, two test modules, and the manifest.

Evidence:

- `spec-status`: `check-base-verb` base `049772341863`, `json-output` base
  `9b1d10264a79` (neither modified; two requirements added).
- `spec_status.py:1289-1361` `cmd_check_base`, `:2483-2500` `_git_capture`,
  `:1467-1500` `_member_state_with_root`, `:1560-1580`
  `_epic_hosting_root`, `:869-930` `cmd_locate`, `:4707-4710` parser,
  `:4982` dispatch; `spec_gate.py:70-76`, `:293-328`; `spec_common.py:3013`;
  `test_spec_status.py:6738` `CheckBaseTest`, `:4568` `_init_git`;
  `test_spec_common.py:275`; `test_spec_gate.py:271`.
- Runnable: `git log --format=%h 35db51c..main -- plugins/s/.claude-plugin/
  plugin.json` → `076a9ef`; an untouched or nonexistent path → no output,
  exit 0; an unknown sha → exit 128; same from a linked worktree.
- Runnable: `git grep -o -h -w -F -e cmd_check_base -e nosuch -e --check
  main` → only the matched literals, exit 0; no match → exit 1.
- Runnable: `git rev-parse --verify --quiet main` → sha, exit 0; unknown ref
  → exit 1. `check-base gate-plan-stamp` → clean, exit 0.
- Runnable: token extraction over gate-plan-stamp's plan → 3 path tokens, 3
  `path:line` citations, 35 identifier tokens.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Base ref: oracle, Q1.
- `plugin.json` exemption: PLANNER default, Q2.
- Unmeasurable plan: PLANNER default, Q3.
- Helper placement, symbol rule, output shapes: investigation.
