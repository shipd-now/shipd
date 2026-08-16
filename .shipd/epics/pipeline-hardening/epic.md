# pipeline-hardening
Status: active
Theme: reliability

## Introduction

The named-pipelines epic shipped the full machinery — pydantic-validated
entry schema, named presets, per-stage options honored by both drivers —
but a post-ship audit found the seams where the machinery and its
surroundings disagree. The worst is behavioral: the in-session autopilot
drive (the default mode) hardcodes the four-stage loop and never honors
`skip`, `replace`, `tools`, or `custom` entries, so the shipped `basic`
preset skips the gate under the detached driver but silently still runs
it in-session. Around that sit reliability gaps the same audit surfaced:
`shipd doctor` reports missing pydantic as a warn even in repos where a
declared pipeline makes it a hard stop, and cannot see a malformed
pipeline at all; `worktree.sh` silently adopts stale local branches
(which mis-derived an epic status this very day, with ~30 merged local
`change/*` branches left loaded); the interactive skills parse
`pipeline-show`'s human-rendered labels because no `--json` view exists;
and the format-authority docs still describe the pre-epic grammar, so a
user cannot hand-author what `--expand eco` prints.

This epic closes those gaps: the in-session drive honors every entry
form, the doctor preflights the pipeline, worktree branch reuse becomes
loud and prunable, `pipeline-show` gains a machine-readable contract that
both skills consume, and the documentation sweep brings every surface to
the shipped grammar. Success: `"autonomous-pipeline": "basic"` behaves
identically under both drivers; `shipd doctor` fails a repo whose
declared pipeline cannot run; a stale-branch reuse is impossible to miss;
and the `.shipd/README.md` grammar alone suffices to hand-author a valid
pipeline with options.

### Non-goals

- No new pipeline semantics: no new stages, options, presets, or grammar
  forms — this epic makes existing semantics honored, visible, and
  documented.
- No install-flow CI smoke test — guarding `shipd.now/install`
  continuously is a worthwhile standalone change outside this epic's
  pipeline scope.
- No eco field trial: running a real delivery under the eco preset is an
  operational validation, not a change.
- No renderer unification: the human-facing `pipeline-show` and dry-run
  label styles may keep their differences; machine consumers move to
  JSON instead.

## Decisions

- **The in-session drive mirrors the detached driver's entry contract.**
  Skipped entries are not run, `replace` commands run in the worktree in
  place of the built-in, `custom` commands run at their position, and
  `tools` bindings are conveyed in stage instructions — same semantics,
  sub-agent execution. The `epic-autopilot` spec's in-session
  requirements gain the same entry-form coverage the detached ones have.
  The audit's orchestration frictions land here too: the build/autopilot
  skills state the sub-agent → orchestrator reporting contract (a stage
  sub-agent that cannot message its parent ends its turn with the report
  as its final text; the orchestrator grades from the repository, never
  from summaries — already the rule — and never depends on a sub-agent's
  own background watch completing).
- **Doctor gains a `pipeline` check; the `pydantic` check becomes
  context-aware.** A new read-only check resolves the effective pipeline
  at the working directory: ok when it resolves (naming provenance),
  `fail` when a declared pipeline cannot resolve — malformed entries or
  missing pydantic both surface here with the CLI's own error line. The
  standalone `pydantic` check stays warn-level when no pipeline is
  declared and escalates to `fail` when one is. Remedy table rows follow
  the existing consent-gated shapes.
- **Branch reuse becomes loud; merged branches become prunable.**
  `worktree.sh` printing "Created worktree" over a reused branch is the
  bug: reusing an existing branch SHALL print an explicit reuse notice
  with the branch's ahead/behind counts against the base branch. A new
  guarded `prune-branches` verb deletes local `change/*` branches whose
  content is merged into the base (never the current or checked-out
  ones), listing what it deleted. Epic-close derivations always start
  from a fresh branch: a `--fresh` flag errors if the branch already
  exists unless it is merged (then deletes and recreates it) — and the
  build/autopilot skills' epic-close steps use it. Rejected: refusing
  all branch reuse — resuming an in-flight change's branch after
  worktree removal is legitimate and must stay.
- **`pipeline-show --json` is the machine contract; rendered labels
  become human-only.** The verb gains `--json` (resolved entries as the
  validated dicts plus provenance, for presets and custom lists alike;
  `--expand <preset> --json` likewise). The interactive `/s:build` and
  `/s:plan` pipeline-resolution steps and the in-session autopilot
  consume `--json` instead of parsing rendered labels; the label
  renderers stay for humans and drop their contract status. `/s:status`
  gains a `pipeline` argument routing to `pipeline-show`, giving preset
  discovery a skill surface.
- **The format authority is brought to the shipped grammar, everywhere.**
  `.shipd/README.md` documents the per-stage options, the `autopilot`
  namespace, the real exclusivity rule (skip excludes everything;
  `skip: false` is an error), strict typing, and the
  declared-list-requires-pydantic rule. Root `README.md`, the config
  example JSON, and `docs/quickstart.md` (doctor check list + a
  one-line eco opt-in mention) follow. Known small falsehoods die in the
  same sweep: the `pipeline_schema.py` docstring's dashboard claim, the
  `three-strike-parking` requirement title, and the archived epic
  table's `default` row divergence (corrected in the epic file, which is
  not an immutable artifact).
- **Every plugin-touching member bumps the plugin version** (standing
  convention, restated because all five members touch `plugins/s/`).

## Design

Five seams, matching the audit's fault lines. The **drive-fidelity**
member is skill-and-spec work: `autopilot/SKILL.md`'s in-session section
gains the entry-form table (skip → not run, replace/custom → worktree
command, tools → instruction suffix) plus the sub-agent reporting
contract, with matching `epic-autopilot` delta requirements. The
**doctor** member extends `bin/shipd` (one new check function, one
context-sensitive escalation) and the doctor skill's tables. The
**worktree** member is shell work in `worktree.sh` (reuse notice,
`--fresh`, `prune-branches`) plus the two skills' epic-close steps. The
**pipeline-show** member adds `--json` to `spec_status.py`, rewires the
three consuming skill surfaces, and adds the `/s:status` route. The
**docs** member touches no engine code path — pure documentation and
naming corrections across the repo's teaching surfaces.

Dependencies: the pipeline-show member should land before or with the
drive-fidelity member (the in-session drive consumes `--json`); the
doctor, worktree, and docs members are mutually independent and
independent of the other two. Risk-ascending delivery order:
docs sweep → doctor check → pipeline-show JSON → worktree hygiene →
in-session fidelity.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| pipeline-docs-sweep | Bring .shipd/README grammar, root README, config example, quickstart, docstrings, and stale requirement naming to the shipped pipeline grammar | low | low | low | low |
| doctor-pipeline-check | New read-only doctor `pipeline` check resolving the effective pipeline; `pydantic` check escalates to fail when a pipeline is declared; remedy rows | low | medium | low | low |
| pipeline-show-json | `pipeline-show --json` machine contract (custom lists included), skills consume JSON instead of rendered labels, `/s:status pipeline` route | medium | medium | low | low |
| worktree-branch-hygiene | Loud branch-reuse notice with ahead/behind counts, `--fresh` flag for epic-close derivations, guarded `prune-branches` verb for merged locals | medium | medium | medium | medium |
| insession-pipeline-fidelity | In-session autopilot honors skip/replace/tools/custom entries per the detached contract; sub-agent reporting contract in the build/autopilot skills | low | high | medium | medium |

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 58 | 21.1k |
| Edit | 11 | 6.5k |
| (no tool) | 0 | 5.5k |
| Read | 12 | 1.7k |
| Agent | 1 | 439 |
| **Total** | 82 | 35.2k |
