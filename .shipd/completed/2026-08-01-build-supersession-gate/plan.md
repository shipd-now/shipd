# build-supersession-gate
Status: verified

## Idea

Give `/s:build` a mechanical supersession gate: a read-only `check-base` verb
that compares a planned change's delta specs against the current master
library, wired into Phase 0 so build stops and asks instead of executing a
plan whose substance already merged.

### Motivation

The autopilot's throughput means a planned change can be superseded within
hours — PR #69 had already implemented an entire planned change before its
build started, and the builder only caught it by improvising an unmechanized
comparison against the base branch.

### Details

- Add a `check-base [change]` verb to `spec_status.py` reporting, per delta
  entry: `stale-base` (MODIFIED/REMOVED `base:` hash no longer matches the
  master), `missing-master` (MODIFIED/REMOVED id or capability master absent),
  and `id-collision` (ADDED id already present in the master).
- Extend the build skill's Phase 0 already-planned short-circuit: after
  adopting a linted change, run `check-base`; findings force a
  drift-vs-superseded classification, and a superseded plan stops the build
  for a user decision.
- Bump the plugin version (0.6.14 → 0.6.15).

Affected capabilities: `spec-status` (added verb), `build-context-gate` (added
gate requirement). Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/build/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No CI version-bump guard — that is the second observation, planned as its
  own separate change.
- No automatic abandonment or re-planning of a superseded change — the gate
  stops and asks; the human decides.
- No change to merge-time semantics: `spec_merge.py` keeps its take-newer
  stale-base warning exactly as is.

## Implementation

- **Verb shape.** `check-base [change]` on `spec_status.py`, defaulting to the
  currently selected change via the existing `_resolve_change` path, like the
  other verbs. Strictly read-only: no writes, no git, no model, no network.
- **Reuse the merge engine's primitives, don't re-derive them.**
  `spec_status.py` already puts its own directory on `sys.path` and imports
  `spec_common as sc`; the verb additionally does `import spec_merge` and
  reuses `spec_merge.master_path(root, capability)` for master resolution and
  `sc.content_hash(requirement)` for the base comparison — the exact function
  `spec_merge._check_base` uses, so pre-build and merge-time checks can never
  disagree. Deltas parse with `sc.parse_delta`, masters with `sc.parse_spec`.
  Rejected: duplicating the hash/path logic in `spec_status.py` — drift
  between the two checks would make the gate lie.
- **Finding kinds.** For each delta spec under the change's `specs/<cap>/`:
  MODIFIED/REMOVED entry with `base:` ≠ current master hash → `stale-base`
  (report expected and actual hashes); MODIFIED/REMOVED entry whose id — or
  whose whole capability master file — is absent → `missing-master`; ADDED
  entry whose id already exists in the master → `id-collision` (the strongest
  supersession signal: the plan adds a requirement main already has).
- **Output and exit codes.** One line per finding —
  `<capability>/<id>: <kind>` plus hash detail for `stale-base` — then a
  summary line. Exit 0 with a `clean` summary when nothing is found; exit 4
  when findings exist, distinct from the CLI's general errors (1) and guard
  refusals (3) so callers can tell "signal present" from "crash". Rejected:
  exit 0 with findings — a gate the caller must parse prose to trip is not a
  gate.
- **Gate placement.** Build `SKILL.md` Phase 0, step 1 (the already-planned
  short-circuit): after adopting a linted change and before any execution
  phase, run `check-base`. Clean → proceed as today. Findings → read the
  affected masters and recent main history, then classify: content drift
  (masters moved but the substance is still unbuilt) → proceed, carrying the
  findings into the plan review; superseded (the plan's substance is already
  merged on the base branch) → stop, report, and ask the user whether to
  abandon or re-scope — never spawn sub-agents on a superseded plan. Rejected:
  prose-only judgment with no verb — that is exactly the improvisation the #69
  incident showed should be mechanized.
- **Risk.** A clean `check-base` cannot prove non-supersession (a superseding
  merge may not have touched the same requirement ids), so the skill prose
  keeps Phase 1's discovery read as the judgment backstop; the verb turns the
  common case — spec deltas colliding with moved masters — into a mechanical
  trip-wire.
