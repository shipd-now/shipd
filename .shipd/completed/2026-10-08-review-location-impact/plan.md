# review-location-impact
Status: verified
Theme: reliability

## Idea

### Motivation

Three measured defects in `/s:review`, two of them regressions this workstream
shipped itself. Evidence: benchy-cf's ReviewBench checkpoints on v0.6.260 and
v0.6.261, plus a finding from PR #271's own semantic review.

**1. The location rule contradicts itself.** `review-skill` says a finding's
location "SHALL name the line its own fix would change — never a caller or
symptom site the fix does not touch", and `SKILL.md` step 6 says "the fix site,
never a symptom". But `review-risk-lenses` now says a file-not-shipped manifest
finding "SHALL name the importing line as a further location, because that is
the site where the omission breaks". The import *is* a site the fix does not
touch — the fix edits the manifest. One requirement forbids what the other
mandates.

Measured: on v0.6.261 the pg-pool finding appeared in all 3 rounds at `high`
but named the second location in only 1 of 3. The permission lives solely in
`references/risk-lenses.md`, read on condition; the prohibition is inline on the
always-read surface. The inline rule wins — the same mechanism by which the
`low` heading beat the impact floor in v0.6.260.

**2. The impact rule is four abstract nouns and the reviewer does not recognise
instances.** On v0.6.261, 1 of 3 target issues lifted. `cleanup_media` lifted to
`medium` three times. `QuerySummaries` stayed `low` three times *while writing
the broken guarantee out in its own words* — "200 with an empty page alongside a
non-zero total and has_more true". It does not connect that to "a broken
guarantee". `move_file` was seen once, still `low`, though it is nearly the
rule's own example sentence.

The contrast is the packaging lens: no severity floor at all, yet `high` or
`medium` in every round ever measured, because it names a concrete situation
rather than a category.

**3. The `low` definition left edge-case findings homeless, and they are being
dropped.** v0.6.261 defined `low` as "nothing lost, corrupted, exposed, or
promised and unmet" — the negation of the four abstract triggers, so rating
`low` now requires proving a double negative.

Measured, per round over three PRs, v0.6.260 → v0.6.261:

- edge-case findings 4/3/1 → 1/1/0, so 8 total → 2.
- test-coverage 4/4/4 → 4/4/4, exactly unchanged.
- totals 21/18/16 → 18/14/15; golden correctness matches 20 → 14.

The diagnosis is load-bearing: `medium` already says "an unhandled edge case",
so a re-rating would have moved these *up*. They fell. They are being dropped,
not re-rated — the reviewer can neither prove containment nor name a trigger, so
it reports nothing. That is worse than the defect v0.6.261 fixed: v0.6.255
mis-rated real defects, which at least left them countable; v0.6.261 deletes
some of them.

### Details

1. Generalise the location rule inline: the primary location is the fix site,
   and a further location is allowed where that site independently shows the
   defect on its own terms.
2. Name concrete recognisable patterns under the impact rule, each drawn from a
   measured defect.
3. State that uncertainty about severity is never grounds for omitting a
   finding.

### Non-goals

- **No defect kind goes back under `low`.** That is the cheap fix for defect 3
  and it reintroduces the kind-as-severity anchor v0.6.260 measured and v0.6.261
  removed. The no-drop rule is the alternative. `LowBulletNamesNoKindTest` must
  not be weakened; a wording that needs it relaxed is the wrong wording.
- The `low` bullet's own definition is unchanged. Defect 3 is a hole in the
  reporting rule, not in the definition.
- The breadth sweep's kinds list is untouched — it works.
- The exposure floor, the `high` and `medium` definitions, and the
  blocks/never-blocks rule are untouched.
- Not the undersell direction of the description check (confirmed 0 of 3 twice,
  its own change), and not item 4's lens 2.

## Implementation

### Defect 1 — the location rule

Precedent wording already exists in the same requirement, for
`description-drift`: the finding "SHALL carry its primary anchor alone. A
further location SHALL be added only where that site independently shows the
drift on its own terms." Generalise that shape rather than inventing phrasing,
so the general rule and the two special cases agree by construction.

The fix-site rule is not loosened. The primary anchor is still the line a fix
would change; what changes is that a *further* location is now permitted under a
stated condition, instead of being forbidden inline and permitted in a
reference. `review-risk-lenses`' manifest sentence is reconciled to cite that
general permission rather than restate its own.

### Defect 2 — concrete patterns

The four abstract triggers stay as the general rule. Three concrete instances
are named beneath them, each one a defect actually measured:

- a success response that hides a failure — an empty result returned as if real
  while a count or flag says otherwise (QuerySummaries, three rounds of
  evidence);
- a cleanup path that drops the record and leaves the data, or the reverse
  (`cleanup_media`);
- an error path that loses the only copy (`move_file`).

These go inline. Defect 1 is the direct evidence that a rule which must fire on
every review cannot live in a conditionally-read reference.

### Defect 3 — the no-drop rule

The rubric closes with "When you are unsure between two levels, state the doubt
rather than inflating." That covers being unsure *between levels* and says
nothing about being unable to place a severity at all, which is the hole the
edge-case findings fall through. It gains the missing case: never drop a finding
because its severity is unclear — report it at the best estimate and say the
estimate is uncertain.

This is deliberately a change to the *reporting* rule rather than to `low`.
Rewriting `low` to welcome edge cases would mean naming a kind under it.

### The copilot template

Defects 2 and 3 are mirrored there; defect 1 is not. Bound here: the template
carries no fix-site or symptom rule at all — it asks only for a "location" — so
there is no contradiction to resolve and nothing for the generalisation to
attach to. It does carry the impact rule and the contained-impact `low` as of
v0.6.261, and it sits in `ImpactFloorParityTest`'s loop, so the other two apply.

### The line budget — raise the ceiling, do not reflow

`SKILL.md` is at 329 against a ceiling of 330. Measured reflow headroom outside
the frontmatter is 6 lines across six blocks, and three of those blocks sit
inside the rubric and breadth-sweep text this change edits, so the usable figure
is smaller. The additions come to roughly 9 lines. Reflow cannot pay for it.

Extraction cannot either, and that is the substantive point: everything this
change adds is a rule applied on every review, and defect 1 is a measured
demonstration that such a rule loses to the inline surface when it is deferred
to a reference. The detail that *could* be extracted already has been — the
new-code checks, the downstream checks, the call-site checks, the risk lenses.

So the ceiling rises from 330 to 350. The precedent is exact: the harness body's
ceiling went 120 → 140 in v0.6.254, with the rationale recorded in its own test
docstring — "The ceiling guards against bloat; it is not a budget to compress
real instructions into… A body that legitimately grows a step belongs under a
raised ceiling, not under reworded instructions." `SKILL.md` has grown
legitimately across handoff items 1 to 4 and now taxes every change.

Per PR #267 the ceiling has one owner: the `review-skill-references`
requirement, which states it at two places in its own text and scenario. Change
it there and nowhere else; do not restate 350 in a second requirement.

**No reflow in this change.** With the ceiling raised there is no need, and
benchy-cf flagged v0.6.261's rewrap of the base-fetch paragraph as unrelated
churn in a measured diff. They were right: a rewrap that is not needed makes the
diff harder to attribute, so this change touches only the lines it means to.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.261 → 0.6.262.

## Readiness attestation

### Problem and motivation

Three measured defects: a self-contradicting location rule that suppresses the
second location in 2 of 3 rounds, an impact rule stated so abstractly that the
reviewer rates a defect `low` while describing it as a broken guarantee, and a
`low` definition that causes edge-case findings to be dropped rather than rated.

Evidence: benchy-cf's v0.6.261 checkpoint (3 PRs × 3 rounds, `--pr-context`,
grounded-only, majority rule per issue) — 1 of 3 issues lifted; second location
1 of 3 rounds; edge-case findings 8 → 2 with test-coverage flat; golden
correctness matches 20 → 14. Plus PR #271's semantic review, finding f2, which
named the location contradiction independently.

### Scope and non-goals

In scope: the generalised location rule, three concrete impact patterns, the
no-drop rule, all on `SKILL.md` and the harness body; patterns 2 and 3 on the
copilot template; the ceiling raise; three spec deltas; the version bump.

Out of scope: any defect kind under `low`, the `low` definition itself, the
breadth sweep, the exposure floor, the high and medium definitions, the
blocks/never-blocks rule, the undersell direction, lens 2.

### Affected capabilities and files

Two capabilities, four requirements.

Evidence, hashes computed with `spec_status.py base-hash` in this worktree:
`semantic-review` requirements `review-skill` (base `69341354702c`),
`review-risk-lenses` (base `adfe35d189b0`) and `review-skill-references` (base
`d8c1623f5588`), and `copilot-review-skill` requirement `skill-template` (base
`f606d89eef69`). Files: `plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/skills/review/references/risk-lenses.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `SKILL.md` is 329 lines; `test_under_line_ceiling`
asserts under 330; reflow headroom outside the frontmatter totals 6 lines across
six blocks, three of them inside text this change edits; the ceiling is stated
in `review-skill-references` at spec lines 1034 and 1066 and nowhere else; the
copilot template carries the impact rule and the contained-impact `low` but no
fix-site or symptom rule; `description-drift`'s further-location wording exists
in `review-skill` and is the model for the generalisation.

### No open task-shaping decision

- How the location rule is generalised: by reusing `description-drift`'s
  further-location wording, so general rule and special cases agree by
  construction — settled above.
- Whether the fix-site rule loosens: no, the primary anchor is unchanged and a
  further location becomes permitted under a stated condition — settled above.
- Where the concrete patterns live: inline, because defect 1 measured what
  happens to an always-applies rule placed in a reference — settled above.
- Whether defect 3 is fixed in `low` or in the reporting rule: the reporting
  rule, because fixing it in `low` requires naming a kind — settled above.
- Whether the copilot template gets defect 1: no, it carries no fix-site rule to
  contradict — settled above.
- How the budget is found: the ceiling rises to 330 → 350 in its single owner
  requirement, with no reflow in this change — settled above.
