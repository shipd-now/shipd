# grill-preflight-handoff
Status: verified
Epic: autopilot-preflight
Theme: reliability

## Idea

Make `/s:epic-grill`'s Ending run `autopilot.py <epic> --preflight` after
gating and print the `/s:autopilot <epic>` hand-off only when that rubric
is green, otherwise listing its `fail` lines.

### Motivation

The grill hands off to `/s:autopilot` unconditionally, so a user who launches
the run inherits an unplanned, edited, cyclic, or overlapping member and the
unattended run stops to ask a question nobody is there to answer.

### Details

- `plugins/s/skills/epic-grill/SKILL.md` `## Ending`: after the per-member
  summaries, run the preflight, relay its non-`ok` lines and summary line,
  and branch on its exit code.
- `plugins/s/harness/bodies/epic-grill.md` step 7: the same branch in the
  harness body's distilled form.
- `plugins/s/skills/build/tests/test_epic_grill_contract.py`: pin the new
  text on both surfaces.
- Frontmatter and body description: "hand off to /s:autopilot on a green
  preflight".

Affected capabilities: `shipd-epic-grill` (modified `epic-grill-amend-gate`).
Impact: the two skill surfaces, the contract test module,
`plugins/s/.claude-plugin/plugin.json`. No new dependency.

### Non-goals

- No change to the preflight verb, its checks, or its output: that is
  `autopilot-preflight-verb`, consumed here by its exit code and line format.
- No change to `/s:autopilot`'s own Phase 1 (`autopilot-unattended-run`).
- No change to how the grill plans, asks, amends, or gates; the preflight
  runs once, after the last gate, and never reopens a question round.
- No edit to `README.md`, `docs/`, or `AGENTS.md`: their one-line summaries
  of the grill stay true.

## Implementation

- **One run, after the last gate.** The Ending runs
  `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/autopilot.py" <epic>
  --preflight` from the repository root once every selected member has been
  gated, even when a member did not reach `ready` (the rubric's `members`
  line then names it). Rejected: skipping the run on a known-failed member;
  the rubric is the single, complete report the user acts on.
- **Text form, non-`ok` lines relayed.** The grill relays every `warn` and
  `fail` line and the closing `preflight:` line verbatim under a
  `## Preflight` heading; `ok` lines are not repeated, since the rubric
  carries one line per check plus every `shipd doctor` relay. Rejected:
  `--json`; the exit code already decides the branch and the user reads the
  lines, not an object.
- **Green is exit 0.** The verb exits non-zero exactly when a `fail` line
  exists, so the grill hands off on exit 0 and treats every `warn` line as
  information: a `warn drift —` line (the verb's Q1 default) or a `warn
  overlap-files —` line never blocks the hand-off. On any non-zero exit the
  Ending lists every `fail` line, states that the run is not launched, and
  prints no `/s:autopilot` line; when the exit is non-zero with no rubric
  line at all (a usage error, a missing epic, a snapshot without the flag),
  the stderr text is relayed in place of the `fail` lines. Rejected:
  attempting remedies in the grill; each `fail` detail already names its
  remedy (`/s:epic-grill <epic>`, `spec_gate.py <member>`, `/s:plan
  <member>`), and the epic's Non-goals keep the grill's flow unchanged.
- **The `## Summary` sentence states the verdict.** Its one sentence now
  also says whether the preflight is green; on red it is followed by the
  preflight command to re-run after the remedies, instead of the hand-off.
- **Harness body parity.** Step 7 of the body gains the same run, relay, and
  branch in two or three lines; the rendered body stays under the
  `body-content` ceiling (82 lines today).
- **Contract tests** in `test_epic_grill_contract.py` pin, on both surfaces,
  the `--preflight` invocation, the phrase `hand off only when the preflight
  exits 0`, and the phrase `list every `fail` line`, following the module's
  existing shipped-text pattern.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next patch
  above `main` at build time (`0.6.293` when planned; re-bump after a rebase
  if a sibling lands first).

Risk: the preflight's `overlap-files` check will `warn` on this member and
`drift-skill`, both citing `test_epic_grill_contract.py` without an `After`
edge; a `warn` never blocks, and `drift-skill` only reads that file as a
shape model.

## Readiness attestation

### Problem and motivation

The grill ends with an unconditional hand-off, so an unattended run can
inherit a member the launch should have refused.

Evidence:

- `plugins/s/skills/epic-grill/SKILL.md:230-242` prints `/s:autopilot
  <epic>` after the summaries with no check.
- Epic `autopilot-preflight`: Design "Orchestration layer" (`/s:epic-grill`
  ends by running the preflight; hand-off only on a green rubric) and the
  success criterion "runs to its end without asking a question".

### Scope and non-goals

Two skill surfaces, their contract tests, one delta, and the manifest bump;
the verb, `/s:autopilot`, and the grill's question flow stay as they are.

Evidence:

- Epic `## Changes` rows `autopilot-preflight-verb` (the verb) and
  `autopilot-unattended-run` (`/s:autopilot` Phase 1); epic Non-goals "No
  change to how `/s:plan` or `/s:epic-grill` ask their questions".
- `plugins/s/harness/bodies/epic-grill.md:80-82` is the only other grill
  surface; `README.md:274` and `docs/cheatsheet.md:64` need no change.

### Affected capabilities and files

One capability and four files: the SKILL.md Ending, the body's step 7, the
contract test module, and the manifest.

Evidence:

- `shipd-epic-grill`: requirement `epic-grill-amend-gate` (base
  `85fcbec50a05` from `spec_status.py base-hash`).
- `plugins/s/skills/epic-grill/SKILL.md:8` (description), `:230-242`
  (Ending); `plugins/s/harness/bodies/epic-grill.md:1` (description marker),
  `:80-82` (step 7); `plugins/s/skills/build/tests/test_epic_grill_contract.py:23-80`
  (shipped-text test pattern); `plugins/s/.claude-plugin/plugin.json`.
- Consumed contract: `autopilot-preflight-verb`'s delta
  `specs/epic-autopilot/spec.md` (`launch-preflight`): `ok|warn|fail <check>
  — <detail>` lines, `preflight: ok|<n> problem(s)`, exit non-zero exactly
  on a `fail` line, `--preflight --json` one object.
- Runnable: `python3 plugins/s/skills/build/scripts/autopilot.py
  autopilot-preflight --preflight` on `main` today → `error: unrecognized
  arguments: --preflight`, exit 2, no rubric line — the rubric-less
  non-zero case the Ending must treat as red.
- Runnable: `python3 -m unittest
  plugins.s.skills.build.tests.test_epic_grill_contract` → passes on `main`
  (the module the new tests extend).

### No open task-shaping decision

Four decisions existed; all are settled.

Evidence:

- Green means no `fail` line (exit 0), `warn` allowed: epic Design and the
  verb's `launch-preflight` exit contract; builds on
  `autopilot-preflight-verb` Q1 (drift is `warn`).
- Run once after the last gate, even with a failed member: epic Design
  ("ends by running the preflight"), investigation.
- Red prints the `fail` lines and no hand-off, rubric-less errors relay
  stderr: epic Design ("otherwise lists the failing lines"), the runnable
  premise above.
- Text form over `--json`: investigation (exit code decides the branch).
