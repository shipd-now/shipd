# review-skill-headroom
Status: verified
Theme: developer-experience

## Idea

### Motivation

Four consecutive ReviewBench-driven changes to `/s:review` have each paid a
compression tax. `plugins/s/skills/review/SKILL.md` has sat at 329/330
lines (`test_under_line_ceiling`) and the rendered review harness body at
119/120 (`test_every_body_stays_lean_at_the_full_vocabulary`) through all
four, so every addition has had to buy its space by shortening existing
prose. That has cost real content twice: item 2's trim dropped
"duplicated" from the low-severity rubric and the breadth sweep's pointer
at the rubric categories, both restored only after a peer session
benchmarking the releases caught them.

The peer session (benchy-cf) also flagged the measurement cost: v0.6.253
reworded ~130 SKILL.md lines to fit step 5d, so any behavioral shift in
that version is item 3 plus the rewording, not item 3 alone. Their
suggestion — move whole steps into references rather than compressing prose
on every change — is what this change does.

### Details

Create real headroom on both surfaces, each by the mechanism that surface
supports:

- `SKILL.md` has a references mechanism, so extract the detail of steps 3
  and 4 into one new reference, keeping every check's **name** inline per
  the pattern the risk lenses and new-code checks already follow. This
  frees 13 lines (329 → 316).
- The harness bodies have no references mechanism — they ship standalone
  into other repos with no `${CLAUDE_PLUGIN_ROOT}` — so nothing can be
  extracted from them. Raise their shared ceiling from 120 to 140 instead,
  and make `harness-command-bodies` the single owner of that number so the
  two other capabilities that currently restate it stop duplicating it.

### Non-goals

- No behavior change. Not one instruction is added, removed, or reworded in
  substance; text moves between files and a test constant rises.
- Not a fix for any ReviewBench finding. The queued severity-calibration,
  description, and step-7 changes land separately, on top of this headroom.
- No change to SKILL.md's own 330-line ceiling. The extraction gives it 14
  lines of real slack, so raising it is unnecessary — extraction is the
  better answer wherever a references mechanism exists.

## Implementation

### SKILL.md extraction

New reference `plugins/s/skills/review/references/call-site-tracing.md`
carries two sections — the five downstream-impact checks and the two
call-site-value checks — with the full explanatory prose moved verbatim
from the current steps 3 and 4. Steps 3 and 4 keep their intro sentence,
their check **names** as one-line bullets, and a pointer to the new
reference. Step 4 points at the same reference as step 3 rather than
repeating the path. A new References table row carries the condition "a
changed signature, constant, guard, or helper needs chasing to its call
sites".

The exact post-extraction text for both steps, the reference file, and the
table row is already written and verified in this worktree's working tree
(`wc -l` 316, full review suite green) — the implementer applies it as
given rather than re-deriving it, since re-deriving prose is what cost
content twice before.

### The harness-body ceiling

`test_every_body_stays_lean_at_the_full_vocabulary`'s constant rises from
120 to 140, with a docstring recording why: four bodies (review, epic,
gate, ask) had reached 116-119, the ceiling guards against bloat rather
than being a budget to compress instructions into, and compression had
already silently dropped content twice. Measured sizes at the full feature
vocabulary, for the record: review 119, epic 119, gate 118, ask 116, then
a gap down to 112 and below — so this is a shared constraint four commands
have outgrown, not a review-specific problem.

Three capability specs currently state the number. `harness-command-bodies`
(requirement `body-content`) owns it and moves to 140, gaining a sentence
making it the single source of truth. `build-subagent-handoff`
(`build-qa-rubric-consult`) and `shipd-epic`
(`epic-authoring-rubric-consult`) stop restating the figure and reference
the owning requirement's budget instead — so the next change to the number
touches one capability, not three.

### The inline-names rule, generalized

`semantic-review`'s `review-skill` requirement currently pins the
inline-names rule to the five new-code checks specifically. This change
extracts two more always-applies check groups, so the rule generalizes:
any check that applies to every diff carrying the thing it inspects, whose
detail lives in a conditionally-loaded reference, keeps its name inline.
The requirement now names all three groups plus the risk lenses, and its
scenario widens to match.

`test_skill_references.py` gains the matching assertions — two new phrase
tuples (the five downstream-impact names, the two call-site-value names)
checked inline outside the References table, mirroring
`test_new_code_checks_named_inline` and `_missing_checks` exactly.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.253 → 0.6.254.

## Readiness attestation

### Problem and motivation

Both review prompt surfaces are at their line ceilings, so every change
compresses existing prose, and that has twice silently dropped content.

Evidence: `wc -l plugins/s/skills/review/SKILL.md` reports 329 against
`test_under_line_ceiling`'s `assertLess(lines, 330)`; rendering every
harness body at `hr.FEATURES` reports review 119, epic 119, gate 118, ask
116 against `assertLess(lines, 120)`. The two restored regressions are
shipd-now/shipd PR #260 (the "duplicated" category and the five check
names) and PR #261 (the breadth sweep's rubric pointer).

### Scope and non-goals

In scope: the SKILL.md extraction, the ceiling raise, the single-owner
consolidation of that number across three capabilities, the generalized
inline-names requirement with its tests, and the version bump. Out of
scope: every behavioral change in the queue, and SKILL.md's own ceiling.

### Affected capabilities and files

Four capabilities, four requirements.

Evidence: `semantic-review`/`review-skill` (base `a86109ac7c53`),
`harness-command-bodies`/`body-content` (base `4d80d681030d`),
`build-subagent-handoff`/`build-qa-rubric-consult` (base `8dd1e463535a`),
`shipd-epic`/`epic-authoring-rubric-consult` (base `ece516e4fe17`), each
from `spec_status.py base-hash`. Files:
`plugins/s/skills/review/SKILL.md`,
`plugins/s/skills/review/references/call-site-tracing.md` (new),
`plugins/s/skills/build/tests/test_harness_bodies.py`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`. Runnable premise: the extraction
is already applied and measured in this worktree — 316 lines, 232/232
review tests and 27/27 harness-body tests green.

### No open task-shaping decision

- Extraction for SKILL.md, ceiling raise for the harness bodies: settled —
  each surface gets the mechanism it supports, and the harness bodies
  support no extraction at all.
- 140 as the new ceiling: settled — it clears the largest current body
  (119) by 21 lines, enough for the four queued changes without another
  compression round, while still failing on genuine bloat.
- Consolidating the number into one owning capability rather than updating
  three: settled — three copies of a constant is what made this a
  three-capability change in the first place.
- Whether the inline-names rule generalizes or stays pinned to the
  new-code checks: it generalizes, since this change extracts two more
  always-applies groups under the same reasoning.
