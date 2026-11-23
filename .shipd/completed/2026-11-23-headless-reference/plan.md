# headless-reference
Status: verified
Planned-at: d93fff2f383fd537ed902e5a5342d40042a4cebb
Gated-hash: 84cfc96de952

## Idea

Hold the no-human ("headless") contract in one reference,
`plugins/s/skills/ask/references/headless.md`, point every inline copy at it,
and record a session's own default as `ASSUMPTION` instead of `USER`.

### Motivation

The contract — consult the oracle, adopt your default on `INSUFFICIENT`,
record it in the ledger, never open a dialog — sits copy-pasted in the
autopilot skill, the autopilot driver's prompts, and the epic-grill planner
instruction, and the copies disagree on the ledger label. The Claude engine
records its own default as `**Answered by:** USER`, so a ledger cannot tell a
person's answer from a planner's guess. An external harness needs one file it
can load, and it already records a low-impact default as `ASSUMPTION`.

### Details

- Add `skills/ask/references/headless.md` with four `##` parts: Codebase
  first, Oracle next, Default last, Never a dialog. Default last records
  `**Verdict:** INSUFFICIENT`, `**Answered by:** ASSUMPTION`, the options with
  the default first, a non-empty `**Answer:**`, and `**Queued:**` when filed.
- Replace the inline contract in the autopilot skill (plan, build, re-plan
  instructions) and in the driver's canned reply, build, enrichment, and
  re-plan prompts with a pointer to the file. The prompts keep the concrete
  `oracle-lookup` command, since the contract names it by placeholder.
- Keep epic-grill's `PLANNER` label as an explicit override of Default last,
  in its skill and its harness body.
- In `spec_gate.py`, reject an `ASSUMPTION` entry with no `**Verdict:**` or an
  empty `**Answer:**` (also empty after a `Proceeding on the recommendation:`
  prefix), and stop the placeholder check firing on a ledger `**Question:**`.
- In `evals/run.py`, require `ASSUMPTION` on every `INSUFFICIENT` entry in the
  `oracle-default` grader.
- Add `plugins/s/external-loaders.json` and a unit test that fails when a
  listed file or heading disappears; document it in `AGENTS.md`.
- Bump the plugin version.

Affected capabilities: `context-gate`, `epic-autopilot`, `skill-evals`,
`shipd-ask` (modified or extended), and the new `external-loaders`.

### Non-goals

- No paid eval run; the grader is unit-tested only.
- No change to epic-grill's `PLANNER` behaviour or to the gate's `PLANNER`
  finding.
- No change to the oracle contract itself.

## Implementation

- **One file, four stable headings.** External loaders read `headless.md` by
  heading, so the headings are listed in the manifest and a test pins them.
- **The driver prompts keep the lookup command.** `oracle-contract.md` names
  the command as `<STATUS_PY>`, so a driven session still needs the concrete
  path. The prompts therefore carry one note, built once in `autopilot.py`
  (`HEADLESS_NOTE`), naming the reference path and the lookup command, and no
  ledger label.
- **The build stage's sub-agent `QUESTION:` case also points at the file.**
  There the session answers a sub-agent, not a plan ledger; the contract's
  ledger part applies only where a plan is being written.
- **The gate parses the ledger by field.** A field's value runs from its line
  to the next field line, so a wrapped answer counts. The placeholder check
  drops the `**Question:**` field of each ledger entry before scanning.
- **The grader accepts only `ASSUMPTION`.** `USER` is now refused, since a
  session's guess is not a person's answer; `PLANNER` and `ORACLE` stay refused.
- **The manifest lives beside the plugin manifest** at
  `plugins/s/external-loaders.json`, relative paths from `plugins/s/`; its test
  lives in the engine suite that CI already runs.

Risk: an external loader that matches a heading by different text. The
manifest test only guards this repo's side.

## Readiness attestation

### Problem and motivation

The headless contract has several copies that disagree on the ledger label.

Evidence:

- `plugins/s/skills/autopilot/SKILL.md`, `autopilot.py` `GOAHEAD_REPLY`,
  `_stage_prompt`, `_replan_prompt`, and the epic-grill skill each restate it.
- `evals/run.py` `ADOPTING_ANSWERERS` was `("USER",)`.

### Scope and non-goals

Nothing outside the listed files changes.

Evidence:

- In scope: `plugins/s/skills/ask/references/`, `autopilot/SKILL.md`,
  `epic-grill/SKILL.md`, `plan/SKILL.md`, `plan/references/emission.md`,
  `build/scripts/autopilot.py`, `spec_gate.py`, `evals/run.py`, the harness
  body `epic-grill.md`, `AGENTS.md`.
- Out of scope: `oracle-contract.md`, `spec_lint.py`.

### Affected capabilities and files

Four capabilities change and one is new. The gate's placeholder exemption is a new requirement, not a rewrite of `context-sufficiency-checks`, because the gate scans a change's own delta and that requirement's text lists the markers.

Evidence:

- Base hashes from `spec_status.py base-hash`: X
  `oracle-aware-driven-sessions` 95f8fe376d26,
  `in-session-unattended-prompts` f57419899362, `oracle-gate-enrichment`
  cc65cc2784c7, `oracle-default-grading` 3e9fa066f47f.
- `spec_lint.py` only requires the three ledger fields to be present
  (`QA_REQUIRED_FIELDS`), so the gate carries the new check.

### No open task-shaping decision

The request fixes the label, the headings, and the gate rules.

Evidence:

- The label `ASSUMPTION` and the epic-grill `PLANNER` exception come from the
  request.
- Where the manifest lives is the one judgement call: beside the plugin
  manifest, tested by the engine suite.
