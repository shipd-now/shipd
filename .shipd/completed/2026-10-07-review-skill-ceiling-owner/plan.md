# review-skill-ceiling-owner
Status: verified
Theme: spec-engine

## Idea

### Motivation

Four requirements in the `semantic-review` capability state a line ceiling
for `plugins/s/skills/review/SKILL.md`, and they disagree:

| requirement | states | true? |
| --- | --- | --- |
| `review-skill-references` | under 330 lines | yes |
| `review-risk-lenses` | under 300 lines | **no** |
| `review-lint-step` | under 300 lines | **no** |
| `review-incremental` | under 300 lines | **no** |

`SKILL.md` is 325 lines and `test_under_line_ceiling` enforces `< 330`. So
three requirements and three of their scenarios assert something the
repository has not satisfied for some time, and nothing caught it: those
scenarios have no automated test behind them, and the figure was copied into
each requirement rather than referenced.

This is the same defect shape the preceding headroom change fixed for the
harness bodies, where one ceiling was restated across three capabilities. It
surfaced now because the next change in the queue modifies
`review-risk-lenses`, and that requirement cannot be honestly restated while
it carries a false claim.

### Details

Give the ceiling one owner. `review-skill-references` keeps the figure and
says explicitly that it owns it; the other three stop restating it and refer
to the owner instead, as do their scenarios.

### Non-goals

- No change to the ceiling's value, to `test_under_line_ceiling`, or to
  `SKILL.md` itself. This change makes the spec describe the repository as
  it already is.
- No change to any requirement's substance beyond the ceiling sentence and
  the scenario clause stating the figure.
- No new test. The ceiling already has one; the problem was three copies of
  a number, not a missing check.

## Implementation

`review-skill-references` — the owner, and already correct at 330 — has its
sentence extended to "this requirement owns that ceiling, and no other
requirement SHALL restate the figure", so a future change has somewhere
unambiguous to look and no licence to copy it again.

`review-risk-lenses` and `review-lint-step` each drop the sentence
" `SKILL.md` SHALL stay under 300 lines." entirely, and their shared
scenario "The skill body still fits the ceiling" changes its THEN from "it
is under 300 lines" to "it is within the line ceiling
`review-skill-references` owns".

`review-incremental` phrases its claim differently — "adding no line, and
SHALL stay under 300 lines" — so it keeps the adding-no-line guarantee,
which is its own concern, and drops only the figure. Its scenario "The
trigger costs no line" likewise keeps the `posting.md` row assertion and
refers to the owner for the ceiling.

No implementation file changes, so no version bump: the plugin ships
identical bytes. The change is a spec-library correction.

## Readiness attestation

### Problem and motivation

Three requirements assert `SKILL.md` stays under 300 lines; it is 325, and
the enforcing test allows 330.

Evidence: `wc -l plugins/s/skills/review/SKILL.md` reports 325;
`test_skill_references.py`'s `test_under_line_ceiling` asserts
`len(self.lines) < 330`; `.shipd/verified/semantic-review/spec.md` states
"under 330 lines" at line 997 (`review-skill-references`) and "under 300
lines" at lines 1065 (`review-risk-lenses`), 1219 (`review-lint-step`) and
1265 (`review-incremental`), with matching scenario assertions at 1106,
1233 and 1305.

### Scope and non-goals

In scope: the ceiling sentence and scenario clause in four requirements of
one capability. Out of scope: the ceiling's value, the test, `SKILL.md`, and
every other part of those four requirements.

### Affected capabilities and files

One capability, four requirements, no implementation file.

Evidence: `semantic-review` requirements `review-skill-references` (base
`bbb61d51cda8`), `review-risk-lenses` (base `44b949a44d24`),
`review-lint-step` (base `d82ad034043f`), `review-incremental` (base
`ead16f3b6b79`), each from `spec_status.py base-hash`. Runnable premise:
the full review suite is green before and after, since no implementation
file is touched.

### No open task-shaping decision

- Which requirement owns the number: `review-skill-references`, which
  already carries the correct figure and is the one about `SKILL.md`'s
  structure — settled above.
- Whether to raise the three stale claims to 330 instead of removing them:
  removal. Three correct copies of a number drift exactly as three
  incorrect ones did.
- Whether `review-incremental` keeps its adding-no-line guarantee: yes,
  that is a distinct claim about the References row and survives untouched.
- Whether a version bump is needed: no, nothing under `plugins/s/` changes.
