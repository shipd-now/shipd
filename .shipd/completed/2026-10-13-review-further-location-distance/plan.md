# review-further-location-distance
Status: verified
Theme: reliability

## Idea

### Motivation

ReviewBench scores **each location as its own candidate**, so every further
location that matches nothing is a false positive. Measured across every set
benchy-cf holds, the further locations that never match are the ones nearest
the primary:

| further location sits | matched / total |
| --- | --- |
| in another file | 53 / 109 — 49% |
| same file, more than 15 lines away | 28 / 70 — 40% |
| same file, within 15 lines | **4 / 34 — 12%**, and 0 of 40 on the three-PR set |

Locations per finding rose 1.37 → 1.67 → 1.84 across v0.6.260, v0.6.275 and
v0.6.276 while **primary** locations kept matching at a flat ~50%. So the
findings are not getting worse; the anchors are. v0.6.276's increase was almost
entirely the near bucket, 5 → 11.

The reason those anchors never match is structural, not statistical: the golden
finding is anchored on one of the two lines, so a reviewer spelling out the
other half of the mechanism a few lines down produces a second candidate for a
finding that already has its anchor. The reviewer is being more thorough and
scoring worse for it.

**The claim this change rests on is about redundancy, not about matching.**
Across 4 repositories and 74 near anchors, not one golden finding *depended* on
a near anchor: in each of the 4 that did match, the primary matched too and
every golden finding the near location covered was also covered by another
location in the same review. So dropping them is a precision gain at zero
retroactive recall cost. An earlier framing — "near anchors never match" — was
false, and apilix disproved it before this change was written.

### Details

A further location must lie outside the primary's hunk **and** outside the
function, block or table the primary sits in, with a genuinely recurring site
exempt.

### Non-goals

- **No change to the three shapes a further location may take.** The
  conjunction clause in particular pays for itself: pg-pool `index.js:3` and
  `api.go:331` are both conjunction anchors and both match. The rule gains a
  distance condition, not a shape condition.
- **No line count in the instruction.** `semdiff diff` hands the reviewer its
  hunks, so "outside the hunk you anchored in" is checkable against output it
  already has. The 15-line figure is the scoring diagnostic, not the rule — a
  prompt asking a reviewer to count lines is asking for arithmetic it does
  inconsistently.
- No change to the rubric, the breadth sweep, or any other step.
- No verifier, of any kind.

## Implementation

One clause on two surfaces.

- `plugins/s/skills/review/SKILL.md`, the report step's further-location
  sentence: "It must also sit outside the primary's function or hunk — an
  anchor a few lines away restates the defect instead of naming a second site."
- `plugins/s/harness/bodies/review.md`, step 11's location parenthetical,
  inline, because that file ships standalone and can read no reference.

`references/pr-description.md` and `references/risk-lenses.md` need no edit:
both already defer to the general permission rather than granting their own, so
they inherit the condition. The packaging case they rely on anchors at a
manifest and names an import **in another file**, so the distance rule cannot
reach it — stated in the requirement and pinned by a new scenario, because that
is the case most likely to be broken by a careless reading.

### The first wording was wrong, and the correction costs both ceilings

A first attempt wrote the condition as a **disjunction** — "outside the
primary's function, **or** outside its hunk" — which the review showed is
satisfied by either half alone. Worse, in any file with no functions the first
half is vacuously true and the rule never binds at all; the diff shipping it
was six Markdown files and one JSON, so the rule did not constrain a review of
its own pull request. It also collided with the recurrence rule two sentences
below, which the harness body does not carry at all, so on that surface the
prohibition had no counterweight.

The corrected wording is conjunctive, names the block or table that encloses a
manifest line so a function-less primary is still constrained, and exempts a
genuinely recurring site. That costs lines neither surface had:

- `SKILL.md` goes 336 → **341**, so `review-skill-references` raises its
  ceiling 340 → **350**.
- The worst rendered harness body goes 145 → **149**, one line under its
  ceiling, so `body-content` raises it 150 → **160**.

Both raises buy correctness rather than volume, and both are recorded in the
ceiling tests' own docstrings with the disjunction bug that forced them.
`body-content` already states the ceiling is "not a budget to compress real
instructions into".

### Registered criteria, fixed before the build

- **Primary:** near further locations — same file, within 15 lines of the
  primary — fall from v0.6.276's 11 to at most 3 over 3 rounds. If they do not
  fall, the instruction did nothing, whatever precision does.
- **Keep-check:** pg-pool `index.js:3` and `api.go:331` each matched in ≥2 of
  3 rounds; a drop to ≤1 fails the change. Both are cross-file, so a correctly
  scoped instruction cannot touch them — this is the over-suppression test.
- **Guard:** at most 2 named valid golden findings going ≥2/3 against
  v0.6.276 to 0/3, each named and bucketed by whether the hunt proposed the
  candidate at all.
- **Secondary, must not regress:** `move_file` and `QuerySummaries` hold at
  medium in a majority of observed rounds.
- **Pre-registered null:** near anchors unchanged with the keep-check holding
  means this is a no-op, and it will be reported as one rather than kept on the
  strength of the retroactive count.

Grounded precision is **context only**. It has no calibrated threshold —
v0.6.275's own rounds spanned 0.21 to 0.42 — so a criterion written on it could
not fail.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.278 → **0.6.280**. 0.6.279 is
taken by `spec-owned-wording-drifts`, which is in review on its own branch.

## Readiness attestation

### Problem and motivation

Every further location that matches nothing is a scored false positive, and the
ones nearest the primary are the ones that never match while never being the
only cover for a finding.

Evidence, from benchy-cf's scoring over four repositories: near anchors matched
4 of 34 on apilix and 0 of 40 across the three-PR set; other-file anchors 53 of
109; same-file-but-distant 28 of 70. In all 4 near matches the primary matched
too and another location in the same review covered the same golden finding, so
no finding depended on a near anchor. Locations per finding rose 1.37 → 1.84
while primary match rate stayed flat near 50%.

### Scope and non-goals

In scope: one clause on `SKILL.md` and the harness body, one MODIFIED
requirement with two added scenarios, the version bump.

Out of scope: the three shapes, every other workflow step, the rubric, the two
reference files that already defer, and any verifier.

### Affected capabilities and files

Two capabilities, three requirements, hashes from `spec_status.py base-hash`
here: `semantic-review`/`review-skill` (`0432db60caa7`) for the rule,
`semantic-review`/`review-skill-references` (`d01334930663`) for the
`SKILL.md` ceiling, and `harness-command-bodies`/`body-content`
(`2c7a54ce28b1`) for the rendered-body ceiling.

Files: `plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/skills/build/tests/test_harness_bodies.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `SKILL.md` is 336 lines before the change and
338 after, against its 340 ceiling; the worst rendered harness body is 145
before and 147 after, against 150, measured by rendering every registered
harness; `review-skill` already states the three shapes and the general
permission; `references/pr-description.md` and `references/risk-lenses.md` both
defer to that permission rather than granting their own; and the packaging
case's primary sits in a manifest with its further location in a different
file.

### No open task-shaping decision

- Function-or-hunk versus a line count: function or hunk, because the reviewer
  already holds `semdiff`'s hunks and would count lines inconsistently —
  settled above, with the 15-line figure kept as the scoring diagnostic.
- Whether the conjunction shape narrows too: no, it pays for itself on two
  measured anchors — settled above.
- Whether the reference files change: no, both already defer — settled above
  and verified.
- What the criteria are: registered above and with benchy-cf before this build,
  including the null.
