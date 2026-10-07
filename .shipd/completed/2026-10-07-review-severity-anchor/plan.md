# review-severity-anchor
Status: verified
Theme: reliability

## Idea

### Motivation

v0.6.255 added an **Impact floor** bullet to `/s:review`'s severity rubric so a
serious defect would stop being rated `low`. A ReviewBench checkpoint on
v0.6.260, run by peer session benchy-cf, measured that it does not fire.

Two cases were observed across three rounds, both named verbatim in the rubric's
low list:

- chronicle `move_file` deleting the only copy (`media.rs:108-109`) — rated
  `low` in one round, `medium` in another. This is nearly the floor's own
  example sentence, "a swallowed error that loses a file is not low".
- CrabTrap `QuerySummaries` swallowing database errors, so the API answers 200
  with an empty page — rated `low` in all three rounds.

Scored per issue on a majority rule, 0 of the 2 observed issues lifted. The
severity spread over three rounds barely moved: low 44→35, medium 35→38, high
19→20. A third case, chronicle `cleanup_media`, split `medium`/`low` across
rounds — the same inconsistency.

This matters because `low` never blocks a merge. Item 2's breadth sweep is
finding real defects — a full judge run rated 18 of 21 sampled sweep findings
valid — and the rubric then rates more than half of them `low`, where they
cannot gate anything. The detection works; the rating discards it.

### Root cause

The rubric contradicts itself, and the `low` heading wins. Read the surfaces in
the order the reviewer meets them:

1. Step 5c calls them "a remaining defect of the **minor kinds** named in the
   rubric below".
2. The rubric prints them under the **low** heading: "a real but minor defect:
   swallowed errors, resource leaks on rare paths, dead or duplicated code…".
3. Only then does the floor say that list names kinds rather than severities.

Three signals say *minor*; one says *maybe not*. A file lost on a cleanup path
**is** "resource leaks on rare paths", printed under `low`. The floor asks the
reviewer to override a label the rubric just applied, and loses.

The floor is already positioned at the point of rating — immediately under the
low bullet in step 6. So moving it closer to where severity is assigned is not
available as a fix; it is already there. The defect is the conflicting anchor,
not the floor's distance from the decision.

Supporting evidence, which benchy-cf correctly called suggestive rather than
clean: the packaging-manifest lens carries no floor at all and its findings came
out `high` or `medium` in every round, never `low`. Its guidance describes
defects by impact and never calls them minor. Manifest defects do carry obvious
impact regardless of framing, so this shows impact framing *can* reach medium
and high — not that kind framing with a floor cannot.

### Details

Three fixes ship in one version.

1. **The severity anchor.** The defect-kinds list moves out from under the `low`
   heading into step 5c as what to look for; `low` is defined by contained
   impact; nothing labels these defects minor before the reviewer rates them.
2. **The manifest fix-site second location.** A "file not shipped" finding names
   the importing line alongside the manifest, so the finding anchors where the
   break shows as well as where the fix goes.
3. **The copilot template's stale rubric.** `plugins/s/integrations/copilot/SKILL.md`
   still defines `low` as "style, naming, minor redundancy, defensive nits" —
   the wording item 2 replaced two versions ago. It is brought in line.

### Non-goals

- No change to the `high` or `medium` definitions, the exposure floor, or the
  blocks/never-blocks rule. `low` still never blocks.
- No fix for the undersell direction of the description check, which the same
  checkpoint confirmed at 0 of 3 for the second time. It is a real defect and a
  separate change.
- Not item 4's lens 2, stdlib and framework semantics.
- No pull-request comment volume cap.
- The copilot template gains no breadth-sweep step. It carries six workflow
  steps and never received item 2's sweep, so it names no defect kinds. That is
  coherent under the new structure — kinds belong to the sweep, and a template
  without the sweep simply has none to list — and the missing sweep stays a
  tracked gap rather than widening this change into a new workflow step.

## Implementation

### Where the kinds list goes

Step 5c carries the list, because the sweep is the pass that hunts these
defects and a detection aid belongs with the detection. Its heading loses
"minor" — it becomes `### 5c. Breadth sweep` — and its body names the kinds
directly instead of pointing at the rubric. The step closes by sending the
rating back to step 6's rubric, so the sweep never rates on its own.

The rubric's `low` bullet then defines `low` by what the defect does, not by
which kind it is: a real defect whose impact is contained — nothing lost,
corrupted, exposed, or promised and unmet. The sentence "Pure style, naming, and
formatting are never findings" stays in the rubric. It is load-bearing, it is
the other half of item 2's redefinition, and a line-budget trim has already
destroyed it once.

### The impact floor survives, restated

Bound here rather than left to the implementer. The floor's **corrective** half
("that low list names kinds of defect, not severities") loses its referent the
moment the list leaves the `low` bullet — it would be correcting a list that is
no longer there, which is exactly the kind of stale cross-reference that makes a
prompt contradict itself. That half goes.

Its **positive** half is what actually assigns severity and it stays, as a rule
in its own right: rate by what the defect does, never by the kind of defect it
is, and data loss, data corruption, a security exposure, or a broken guarantee
is `medium` or `high` however minor the kind looks. Keeping it matters most on
`plugins/s/harness/bodies/review.md`, which can read no reference file, so a
rule dropped there is simply gone.

Parity therefore holds: both rubric surfaces still state an impact rule, and
`ImpactFloorParityTest` still has something real to enforce. Its
`_IMPACT_FLOOR_PATTERNS` must be re-aimed at the new wording — the
"kinds of defect, not severities" proxy is retired with the text it proxied for.

### The line budget

`plugins/s/skills/review/SKILL.md` is at 327 lines against a ceiling of 330
(`test_under_line_ceiling`). The rubric change is close to neutral — the low
bullet plus the floor occupy 7 lines today and the new low bullet plus the
impact rule occupy about 7 — while step 5c grows by roughly 3 lines as it takes
on the kinds list. So the file lands at or just over the ceiling.

Free the budget by **mechanical reflow**, never by rewording. Measured
candidates, word-preserving rewrap at 88 columns, which is this file's existing
body convention:

- lines 65-73 rewrap from 9 lines to 7, saving 2.
- lines 120-122 rewrap from 3 lines to 2, saving 1.

That is the 3 lines needed, and four further candidates exist (173-176, 208-212,
284-289, each saving 1) if the measurement comes out worse than planned. The
YAML frontmatter at lines 2-14 is **excluded** from reflow despite scoring as a
candidate: it is a folded YAML scalar carrying the skill's discovery description
and trigger phrases.

Reflow is word-preserving and must be verified as such, not assumed. Compare the
word sequence of each reflowed block before and after; they must be identical.
Two content regressions have already shipped from compression that looked
harmless — "duplicated" dropped from "dead or duplicated code", and "end to end"
plus a rubric pointer dropped from step 5c — so this verification is the point,
not ceremony.

`plugins/s/harness/bodies/review.md` renders at 134 against a ceiling of 140
(`test_every_body_stays_lean_at_the_full_vocabulary`), so its mirrored change
has room without any reflow.

### The copilot template

`plugins/s/integrations/copilot/SKILL.md` is a different capability, read by a
different reviewer (the headless Copilot CLI), and outside what ReviewBench
measures. It is fixed here anyway because its `low` bullet does not merely lag —
it states the opposite of the other two surfaces. It makes pure style a
reportable finding at `low`, which item 2 removed everywhere else, so the same
repository ships two contradictory definitions of what a finding is.

Its rubric gains the same two changes as the others: `low` defined by contained
impact with style excluded, and the rating rule beside it. It needs no kinds
list, because it has no breadth sweep to hold one — see the non-goals.

The wording was pinned in no requirement, which is why it could drift two
versions without any test or lint noticing. So this change also states it in
`copilot-review-skill`'s `skill-template` requirement, with a scenario, rather
than leaving the fix as untested prose that can drift straight back.

`ImpactFloorParityTest` currently excludes the copilot template by name in its
docstring, calling it a tracked inconsistency. With the template fixed, that
exclusion is retired and the template joins the parity set — which is what stops
the drift recurring.

### The manifest second location

`plugins/s/skills/review/references/risk-lenses.md`'s packaging lens gains the
rule in its "Does a new file actually ship?" question and in the matching real
finding: the finding's fix site is the manifest, and the importing line is named
as a second location because that is where the break shows. The `locations`
array shipped in v0.6.249 already carries multiple sites, so no code changes.

This does not weaken the fix-site rule. The primary anchor stays the manifest —
the line a fix would change. The import is an **additional** location on the
same finding, not a replacement, and the general rule that a finding anchors at
its fix site is untouched.

Evidence it matters: pg-pool's golden finding is anchored at `index.js:3`, the
import, while the fix site is `package.json`. One checkpoint round anchored at
`package.json:46` alone and lost the match, scoring 1 of 3 instead of 3 of 3.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.260 → 0.6.261.

## Readiness attestation

### Problem and motivation

A measured defect: the impact floor added in v0.6.255 does not change severity
ratings, so real defects the breadth sweep finds are rated `low` and `low` never
blocks.

Evidence: benchy-cf's v0.6.260 checkpoint, 3 rounds with `--pr-context`, scored
per issue on a majority rule — 0 of 2 observed issues lifted, `move_file` rated
low in one round and medium in another, `QuerySummaries` low in all three. The
severity spread moved from low 44 / medium 35 / high 19 to low 35 / medium 38 /
high 20 over three rounds. A separate full judge run rated 18 of 21 sampled
sweep findings valid, with 10 of the 18 rated medium by the judge against `low`
from the skill.

### Scope and non-goals

In scope: the kinds list moving to step 5c, the `low` redefinition, the restated
impact rule, all three mirrored on the three rubric surfaces including the
copilot template, the manifest second location, the re-aimed tests, three spec
deltas, the version bump.

Out of scope: the high and medium definitions, the exposure floor, the
blocks/never-blocks rule, a breadth-sweep step for the copilot template, the
undersell direction, lens 2, and any comment volume cap.

### Affected capabilities and files

Two capabilities, three requirements.

Evidence: `semantic-review` requirements `review-skill` (base `2713f5d2abc5`)
and `review-risk-lenses` (base `5645a1133246`), and `copilot-review-skill`
requirement `skill-template` (base `0adcdaf6fe74`) — every hash computed with
`spec_status.py base-hash` in this worktree. Files:
`plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/skills/review/references/risk-lenses.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured in this worktree: `SKILL.md` is 327 lines; its body
wrap convention is 88 columns; mechanical reflow headroom outside the
frontmatter totals 6 lines across five blocks, of which 3 are needed; the
harness review body renders at 134 against a ceiling of 140; the rubric's low
bullet and impact floor occupy lines 189-195 of `SKILL.md` and lines 93-103 of
the harness body; `test_breadth_sweep_points_at_the_rubric_categories` asserts
`"rubric"` appears in step 5c, which this change inverts.

### No open task-shaping decision

- Where the kinds list goes: step 5c, with the detection pass that hunts them —
  settled above.
- Whether the impact floor bullet survives: its corrective half is retired with
  the list it corrected, its positive half stays as a rating rule on both
  surfaces — settled above with reasoning.
- How the line budget is freed: mechanical word-preserving reflow of two
  measured blocks, with four named fallbacks and the frontmatter excluded —
  settled above.
- Whether the second location weakens the fix-site rule: no, the manifest stays
  the primary anchor and the import is additional — settled above.
- Whether the copilot template changes: yes, the user widened scope to include
  it, because its `low` bullet contradicts rather than merely lags the other
  surfaces — settled above, with its rubric pinned in the spec and its parity
  exclusion retired.
- Whether the copilot template gains a breadth sweep: no — settled in the
  non-goals.
