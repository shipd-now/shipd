# restore-gate-scenarios
Status: verified
Theme: reliability

## Idea

Restore the ten `semantic-review` scenarios a past `MODIFIED` delta deleted,
so the merge gate's own blocking behaviour is specified again.

### Motivation

An archive audit found `2026-08-23-review-output-redesign` restated
`gate-poster` and `skill-post-flow` verbatim while listing only its new
scenarios, deleting ten that pinned when the gate posts `success` versus
`failure` — the behaviour every merge in this repo depends on.

### Details

- Restore seven `gate-poster` scenarios: the pass/green and red/failure status
  mappings, the three `--disposition` scope mappings, summary upsert on
  re-post, and legacy-marker migration.
- Restore three `skill-post-flow` scenarios: the implement-before-merge branch
  under scope `all`, and the `high-only` and `none` disposition flows.
- Carry every scenario both requirements currently hold, restating rather than
  replacing them.

Affected capabilities: `semantic-review` (modified). Impact: delta specs only
— `plugins/s/skills/review/scripts/review_gate.py` and
`plugins/s/skills/review/SKILL.md` already implement all ten and are not
edited. Tests under `plugins/s/skills/review/tests/` already cover the seven
`gate-poster` scenarios.

### Non-goals

- No behaviour change anywhere. Every restored scenario describes what the
  code already does; a diff touching `review_gate.py` would mean this change
  went wrong.
- No restoration of the other sixteen coverage-lost scenarios the audit found
  in `copilot-review-skill`, `delivery-dashboard`, `shipd-cli`,
  `shipd-config`, `shipd-workspace`, `spec-status`, and
  `build-task-coordination`. Those are lower value and stay open.
- No new tests for behaviour already covered by `test_review_gate.py`.

## Implementation

- **Restate, never replace.** Both entries carry every scenario the master
  holds today plus the restored ones — `gate-poster` goes from six to
  thirteen, `skill-post-flow` from two to five. This is the rule
  `modified-scenario-retention` now enforces, so the linter fails this change
  if a single existing title is dropped.
  Verified premise: `spec_status.py base-hash semantic-review gate-poster`
  prints `7c45b96f6514` and `... skill-post-flow` prints `586808a10517`; the
  masters carry six and two scenarios respectively.

- **Word each restored scenario against the implementation, not the audit
  note.** The audit cited `review_gate.py:206-211` for the three scope
  mappings, `:431-441` for the upsert and legacy-marker branches, and
  `:180-191` for finding partition. Each scenario is written from the code at
  those lines so it states what the gate does today, not what a summary said
  about it. Rejected: copying the pre-deletion wording verbatim from the
  archive, since the poster gained `--disposition` and `--model` after those
  scenarios were written and the old text predates both.

- **The three `skill-post-flow` scenarios describe an agent flow, not a
  function**, so they are specified but not unit-tested — the same shape as
  the two scenarios that requirement already carries. No test is added for
  them, and none is claimed.

Risk: a restored scenario could describe the gate's behaviour slightly wrong
and become a false contract. Guarded by wording each against cited code and by
the validator exercising all thirteen against the real poster.
