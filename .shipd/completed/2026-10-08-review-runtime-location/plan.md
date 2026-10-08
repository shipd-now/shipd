# review-runtime-location
Status: verified
Theme: reliability

## Idea

### Motivation

v0.6.262 generalised the further-location rule to remove a contradiction, and
made the behaviour it was fixing strictly worse. The pg-pool file-not-shipped
finding named its second location in 1 of 3 rounds on v0.6.261 and **0 of 3** on
v0.6.262, measured by benchy-cf over three rounds of the same three PRs.

The rule as shipped reads: a further location "SHALL be added **only** where
that site independently shows the defect on its own terms."

The import that fails — `require('./diagnostics')` — is correct code on its own
terms. It is not wrong; it fails only because the manifest omits the file it
names. So a reviewer applying the rule literally excludes the import, and that
is what the measurement shows. The rule rules out the exact site it was written
to permit.

This is a reasoning error, not an oversight, and it is worth recording as one.
The wording was lifted from the description-drift case so that "the general rule
and the special cases agree by construction". The two cases are not the same
shape: a code site *can* independently contradict a description, so the
predicate is satisfiable there, while a manifest omission has no such site
because the defect is the **conjunction** of the manifest and the import and
neither line is wrong alone. A predicate that is satisfiable in one case was
applied to a case where it is unsatisfiable, and the neatness of the reuse is
what stopped the check.

The spec records the same mistake in a second place. `review-risk-lenses` says
the import "independently shows the omission: it is the line that fails at run
time" — asserting the import satisfies a predicate its own general rule does not
support. Two requirements disagree about what "independently shows" means.

### Details

Restate the further-location rule so both shapes satisfy it: the primary
location stays the fix site, and a further location names a site where the
defect is **visible** — a line wrong in the same way, a line that shows the
mismatch on its own terms, or the line at which the defect surfaces at run time
even though that line is correct in isolation.

### Non-goals

- The primary anchor is untouched. It remains the line a fix would change, and
  a symptom site still may not stand in place of it. Only the *further*
  location admits the run-time failure site, so nothing here reopens
  symptom-anchoring.
- No change to the severity rubric, which v0.6.262 measured as fixed: all three
  target issues lifted to `medium` in 3 of 3 rounds.
- No change to the breadth sweep, the exposure floor, or the no-drop rule.
- The copilot template is untouched: it carries no fix-site or symptom rule, so
  there is nothing for this rule to attach to.
- Not the recall gap. v0.6.262 is still about three golden findings per round
  below v0.6.260 on these three PRs, and establishing whether that is real needs
  a five-PR measurement rather than another prompt change.

## Implementation

### The rule

`SKILL.md` step 6's further-location sentence becomes a disjunction of three
visible-site shapes rather than a single "independently shows" test. The word
**only** goes: it was doing the exclusion, and the permissive list now carries
the limit instead.

The three shapes are not arbitrary. Each is a case the repository already has:
a recurring defect at parallel sites, a description-drift finding whose code
site shows the mismatch, and a manifest omission whose import fails at run time.
A rule that admits exactly its known cases is the right width — wider invites
symptom anchoring, narrower is what shipped and failed.

`review-risk-lenses` stops claiming the import "independently shows the
omission" and says what is true: the import is the line at which the omission
surfaces at run time, though the import itself is correct. It keeps citing the
general permission rather than granting its own, which is the part of v0.6.262
that was right.

### Surfaces

`SKILL.md` step 6 and `plugins/s/harness/bodies/review.md` step 11 both carry
the rule inline and both change. The harness body may phrase it more tersely
but must keep all three shapes — it can read no reference file, so a shape
dropped there is gone for every repository that ships it.

### Budget

No pressure. `SKILL.md` is at 338 against the 350 ceiling raised in v0.6.262,
and the rendered harness body at 141 against 160. The sentence grows by about
two lines on each surface. No reflow, and no ceiling change.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.262 → 0.6.263.

## Readiness attestation

### Problem and motivation

A measured regression this workstream introduced: the further-location rule
excludes the run-time failure site it was written to permit, taking the pg-pool
second location from 1 of 3 rounds to 0 of 3.

Evidence: benchy-cf's v0.6.262 checkpoint, three rounds on chronicle, CrabTrap
and node-postgres with `--pr-context`. The pg-pool finding appeared in all three
rounds at `high`, always anchored at `packages/pg-pool/package.json:46` alone.
The rule's text is at `plugins/s/skills/review/SKILL.md:184` and
`.shipd/verified/semantic-review/spec.md:247`; the contradicting claim is at
`.shipd/verified/semantic-review/spec.md:1110`.

### Scope and non-goals

In scope: the further-location rule on `SKILL.md` and the harness body, the
matching `review-skill` prose, the `review-risk-lenses` justification, a test
pinning the run-time shape, the version bump.

Out of scope: the primary anchor rule, the severity rubric, the breadth sweep,
the exposure floor, the no-drop rule, the copilot template, both line ceilings,
and the unexplained recall gap.

### Affected capabilities and files

One capability, two requirements.

Evidence, hashes computed with `spec_status.py base-hash` in this worktree:
`semantic-review` requirements `review-skill` (base `993a5177bca6`) and
`review-risk-lenses` (base `a4a96da45c31`). Files:
`plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `SKILL.md` is 338 lines against a 350 ceiling;
the harness review body renders at 141 against 160; the live rule says "only
where that site independently shows the defect on its own terms" at
`SKILL.md:184` and the harness body's step 11 says "a further site only where it
independently shows the defect"; `review-risk-lenses` asserts the import
"independently shows the omission".

### No open task-shaping decision

- Whether to add a run-time clause or restate the rule: restate it, because the
  existing predicate is false for this case rather than merely incomplete, and
  bolting an exception onto a false rule leaves the falsehood in place —
  settled above.
- How wide the permission gets: exactly the three shapes the repository already
  has — settled above, with the reasoning for why wider and narrower are both
  wrong.
- Whether the primary anchor changes: no — settled in the non-goals.
- Whether the copilot template changes: no, it carries no rule to attach to —
  settled in the non-goals.
