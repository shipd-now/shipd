# review-revert-to-260
Status: verified
Theme: reliability

## Idea

### Motivation

Eleven versions of review-recall work measured worse than the version they
started from. On ReviewBench's four PRs, recall per round fell 26.7 (v0.6.260)
→ 24.3 (v0.6.271) → 21.7 (v0.6.273), and precision fell 0.439 → 0.393 → 0.361
alongside it. On the three PRs benchy-cf measures round by round — chronicle,
CrabTrap, node-postgres — mean matches fell 11.0 (v0.6.260) → 8.0 (v0.6.261) →
7.7 (v0.6.262) → 7.0 (v0.6.271) → 7.0 (v0.6.273).

v0.6.273 was the pre-registered test of one hypothesis: that v0.6.261's `low`
bullet cost recall by requiring a reviewer to prove four negations before
rating anything low. It restored v0.6.260's wording verbatim and recovered
nothing — 7.0 before, 7.0 after, edge-case findings 4 before and 4 after. The
hypothesis is falsified.

Two separate losses sit underneath that number, and treating them as one is
what kept the search going in the wrong place. The verify stage killed 14 of 83
candidates, and 7 of those kills landed on a valid golden finding at the same
lines with the same claim, none of them covered by another finding that round.
Adding those 7 back gives about 9 matches per round against v0.6.260's 11, so
the hunt lost about 2 per round on its own, independently of the verifier.

Nothing measured singles out which change cost the hunt those 2. They lie
somewhere in v0.6.262–v0.6.266, and the one candidate that looked obvious —
related-file context — has no three-PR measurement at all; on the two PRs it
was measured against it scored 22.0 where v0.6.260 scored 21.7.

So the next test is not another hypothesis. It is the one configuration with
the best measurement on both axes, run again to establish that it still
reproduces. Everything between v0.6.260 and now comes off at once, and what is
re-added afterwards is re-added one change at a time with its own round set.

### Details

The `/s:review` path returns to v0.6.260, with one exception: v0.6.263's
further-location rule stays, because it is the only post-v0.6.260 change with
a clean positive measurement of its own.

### Non-goals

- **No new recall mechanism.** This change adds nothing. It removes.
- **No re-add in this change.** v0.6.262's concrete severity instances and a
  rate-only verifier are both queued behind this one, each needing its own
  round set, because a revert that smuggles a re-add measures neither.
- **The `semdiff related` subcommand is not removed.** Only the review step
  that called it goes. The subcommand keeps its `related-context`
  requirement, its tests, and its CLI surface — nothing in the skill reaches
  it, so it cannot affect a measured round.

  One consequence is deliberate and is not an oversight: `SKILL.md`'s
  subcommand line reads `diff`, `files`, `lint`, `context`, `change`,
  `doctor` and so no longer lists every subcommand `semdiff.py --help`
  prints. Naming `related` there would invite a reviewer to run it with no
  step asking for it, which is the variable this change removes; rewording
  the line to say "the subcommands this review uses" would edit prose on the
  measured surface for a cosmetic gain. v0.6.260's exact text is what
  measured 11.0 matches per round, so the line stays byte-identical to it.
- **No `semdiff` behaviour change at all**, and no change to the gate poster's
  threads, replies, or resolution.
- **No harness-body decomposition.** The reverted body is small again, so the
  pressure that raised its ceiling four times is gone for now. Splitting the
  monolithic `/review` command is a separate decision.

## Implementation

### What stays, and why exactly

**v0.6.263's further-location rule stays.** v0.6.260 carried no
further-location rule at all, and the pg-pool file-not-shipped finding named
its second location in 1 of 3 rounds. v0.6.262 added an exclusive rule that
was logically false of the case it was written for, and the figure fell to 0
of 3. v0.6.263 restated it and the figure went to 3 of 3. So this is a gain
over v0.6.260's silence, not merely a repair of v0.6.262's regression.

The rule's own sentence travels with v0.6.262's expanded primary-anchor clause
— "the fix site, the line your own fix would change, never a symptom site in
place of it" — because the two are one paragraph and the 3-of-3 measurement
was taken with both present. Keeping the further-location sentence while
reverting the clause it qualifies would ship a third configuration nobody has
measured.

Four surfaces carry that rule and all four keep it: `SKILL.md`'s report step,
the harness body's steps 10 and 11, `references/pr-description.md`'s
description-drift anchor paragraph, and `references/risk-lenses.md`'s two
packaging justifications.

`references/risk-lenses.md` needs no edit: both its packaging paragraphs are
this rule's own consequence, added by v0.6.262 and restated by v0.6.263, so
its current content is already the target.

`references/pr-description.md` needed one word reverted, and the plan first
claimed otherwise. Its drift paragraph is the keeper, but its severity
sentence cites the rubric's floor by name — "severity by the normal
high/medium/low rubric and its impact floor" at v0.6.260, which v0.6.261
renamed to "impact rule". Restoring "Impact floor." in `SKILL.md` while
leaving the citation at the retired name would point a reference at a name no
surface carried. The word goes back, and a new test pins the pairing, because
nothing compared the two names before.

**The copilot integration's `low` bullet is not reverted.** At v0.6.260 that
surface still read "style, naming, minor redundancy, defensive nits" — the
stale rubric the user asked to fix when v0.6.262's scope was widened. Reverting
it would restore text that is wrong and that contradicts the skill it mirrors.
It is also not on the measured path: ReviewBench drives `/s:review` and never
renders the copilot surface, so its wording cannot move a round either way.

So that bullet is rewritten to v0.6.260's *skill* wording — the kinds list plus
the impact floor — rather than to v0.6.260's copilot wording. v0.6.262's
contained-impact phrasing, its concrete instances, and its
no-omission-for-uncertainty sentence all come off, so the two surfaces state
the same rubric again.

### What comes off

Reverted to their v0.6.260 content, whole:

- `plugins/s/skills/review/references/json-output.md` — every change since
  v0.6.260 is the `killed` array, the `verifier` object, `candidate`,
  `candidates_by_spawn`, and the discovery-order rule.
- `plugins/s/harness/references/review.md` — the same payload additions.
- `plugins/s/skills/review/scripts/review_gate.py` — the only change since
  v0.6.260 is `_verifier_line()` and its call in `render_summary`.

Deleted: `plugins/s/skills/review/references/verification.md`, which exists
only to hold the verify stage's detail.

Reverted with the further-location rule re-applied on top:

- `plugins/s/skills/review/SKILL.md`. This removes the related-file context
  step, the verify step, the reporting/rating rubric split, the verify-stage
  degradation paragraph, the kill count in the summary table, the relaxed
  context-economy principle, the `related` subcommand from the subcommand
  list, the `verification.md` References row, v0.6.261's "send this to the
  rubric, this step never rates" routing, v0.6.261's breadth-sweep rewording,
  v0.6.262's concrete instances, and v0.6.262's no-omission sentence. The
  steps renumber back to v0.6.260's 1, 2, 3, 3b, 4, 5, 5b, 5c, 5d, 6, 7.
- `plugins/s/harness/bodies/review.md`, which carries all of the above
  inline because it ships to harnesses that can read no reference file.

### The two ceilings

Both are owned by one requirement each and are stated in exactly one place,
so each moves there and nowhere else.

`SKILL.md` comes back to **332 lines** — v0.6.260's 327 plus the five the
further-location sentence adds. Its ceiling therefore falls from 400 to
**340** in `review-skill-references`, the requirement that owns it: the
smallest round figure above the real count, so the ceiling resumes guarding
rather than sitting 68 lines clear of the file.

The rendered harness body's ceiling falls from 250 to **150**, measured rather
than reasoned. v0.6.260's figure was 140, and arithmetic on the source file
predicted the reverted body would render at 138 and fit under it. Rendering it
disproves that: the full-vocabulary case is 138, but `review` on `aider`
renders **141**, because an absent feature emits fallback text longer than the
gated version it replaces, and `aider` declares no features at all.

That also says something about v0.6.260's own 140: it was never valid against
`aider`. The ceiling test only checked the full feature vocabulary until
v0.6.270 added the every-registered-harness loop, so the number this change
reverts to has to clear a case v0.6.260's test never rendered. 150 is the
smallest round figure that does.

`test_harness_bodies.py` keeps the every-command-by-every-harness rendering
v0.6.272 added. That is a test-coverage improvement with no bearing on the
review path, and only the ceiling constant inside it changes.

### Tests

`test_skill_references.py` is at 313 tests. The tests pinning reverted
behaviour come out: the verify-stage tests (`VerifyStageStepTest`,
`KilledNeverInFindingsTest`, `VerifierHandoverTest`, `VerdictIndexNumberingTest`,
`SeverityRubricInSpawnTest`, `NoRubricCopyInVerificationMdTest`,
`TwoStageRubricSeparationTest`, `OrientationSentenceNamesOtherRubricTest`,
`DriftSpawnCarriesBothTest`, `AsymmetryStatedTest`, `KilledEntryCategoryTest`,
`PerSpawnCandidateCountTest`), the related-file context step tests, and the
tests asserting v0.6.262's concrete instances and contained-impact `low`.

The tests pinning the further-location rule stay, and v0.6.260's assertions on
the kinds-list `low` bullet and the impact floor come back.

`test_semdiff_files_context.py` is untouched — it tests the subcommand, which
stays.

**Every removed assertion is removed because the behaviour it pinned is gone,
never because it fails.** A test that fails after the revert and whose
behaviour is a keeper is a revert error, not a test to delete.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.274 → 0.6.275.

## Readiness attestation

### Problem and motivation

Eleven versions of recall work measured monotonically worse than their
starting point, the one hypothesis that was pre-registered and tested came
back falsified, and nothing measured identifies which of the remaining changes
costs the hunt its ~2 findings per round. The next spend is a return to the
best-measured configuration, to establish that it reproduces.

Evidence, from benchy-cf's rounds: four-PR recall 26.7 → 24.3 → 21.7 and
precision 0.439 → 0.393 → 0.361 across v0.6.260, v0.6.271, v0.6.273;
three-PR mean matches 11.0 / 8.0 / 7.7 / 7.0 / 7.0 across v0.6.260, v0.6.261,
v0.6.262, v0.6.271, v0.6.273; edge-case findings 8 → 4 → 4; kills 14 of 83
with 7 landing on uncovered valid golden findings.

### Scope and non-goals

In scope: the `/s:review` prompt surfaces, the payload reference files, the
gate poster's summary line, the two ceilings, the copilot rubric's wording,
the tests, two spec requirements, and the version bump.

Out of scope: the `semdiff related` subcommand and its requirement, every
`semdiff` behaviour, the gate poster's thread handling, any re-add of a
reverted change, and the harness-body decomposition question.

### Affected capabilities and files

Two capabilities, three requirements.

Hashes computed with `spec_status.py base-hash` in this worktree:
`semantic-review` requirements `review-skill` and `review-skill-references`,
and `harness-command-bodies` requirement `body-content`. The implementer
reads the current hash for each from that verb rather than from this plan.

Files: `plugins/s/skills/review/SKILL.md`,
`plugins/s/skills/review/references/verification.md` (deleted),
`plugins/s/skills/review/references/json-output.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/harness/references/review.md`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/skills/review/scripts/review_gate.py`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/skills/review/tests/test_review_gate.py`,
`plugins/s/skills/build/tests/test_harness_bodies.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured in this worktree, not assumed:
`plugins/s/skills/review/SKILL.md` is 378 lines against a 400 ceiling and was
327 at v0.6.260; the harness body source is 241 lines and was 133;
`git diff e360273 HEAD` over `references/json-output.md`,
`harness/references/review.md` and `review_gate.py` contains only verify-stage
content; `references/risk-lenses.md` differs in nothing from its v0.6.263 state, while
`references/pr-description.md` differs in one further word, v0.6.261's
"impact rule" rename, which this change reverts; the `semantic-review`
requirements that
differ from v0.6.260 are exactly `review-skill`, `review-skill-references`,
`review-risk-lenses` (further-location work only, so a keeper),
`fast-pass-eligibility` (one trailing blank line) and the added
`related-context`; v0.6.260's two ceilings read 330 and 140; and the reverted
body with the keeper applied renders 138 at the full vocabulary and 141 for
`review` on `aider`, the worst of the 390 command-by-harness pairs.

### No open task-shaping decision

- Whether the further-location rule stays: it stays, with v0.6.262's
  primary-anchor clause beside it, because the 3-of-3 measurement was taken
  with both present — settled above.
- Whether `semdiff related` is deleted: no, only the step that calls it, so
  the measured path is clean while the subcommand's own requirement stays
  true — settled above.
- Whether the copilot rubric reverts to its stale v0.6.260 wording: no, it
  takes v0.6.260's *skill* wording, because the surface is off the measured
  path and the stale text is simply wrong — settled above.
- What the harness ceiling becomes: 150, because the reverted body renders at
  141 for `review` on `aider` and so does not fit v0.6.260's 140 — measured
  by rendering every registered harness, not inferred from the source file.
- What the `SKILL.md` ceiling becomes: 340, the smallest round figure above
  the file's measured 332 — settled above.
- Whether a rate-only verifier ships here: no, it is the first re-add after
  this change reproduces or fails to — settled above.
