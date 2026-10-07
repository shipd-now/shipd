# review-description-undersell
Status: verified
Theme: reliability

## Idea

### Motivation

Item 3 (v0.6.253) added the PR-description check and it works — benchy-cf
measured 100% grounded precision across 16 drift findings in three rounds,
with no nitpicking on short descriptions. But it only finds two of the three
drift shapes it was built for:

| golden case | rounds matched, 0.6.252 → 0.6.253 |
| --- | --- |
| k1LoW `github.go:75` — code diverges from the description | 1/3 → 3/3 |
| apilix `server/package.json:1` — claimed dep never declared | 3/3 → 3/3 |
| apilix `WORKSPACES.md:1` — description undersells the scope | 0/3 → 0/3 |

The undersell case has never matched, in any configuration, despite being
one of the shipped reference's own worked examples. The cause is in the
wording I wrote: the instruction is "for each concrete claim ... check it
against the diff". An undersell is not a wrong claim — it is a *missing*
one. Iterating claims cannot reach diff content no claim covers, so the
example described an outcome the procedure above it could never produce.

benchy-cf also found the one invalid drift finding of the sixteen came from
fan-out: a description-level claim anchored at a code site (`root.go:73`)
that did not itself show the drift.

### Details

Two fixes:

1. **Run the check in both directions.** Direction 1 is the existing
   claim-against-diff pass. Direction 2 walks the diff's substantial content
   and asks what the description never mentions — a distinct pass, because
   unmentioned scope has no claim to iterate over. Both named on every
   surface, not just in the reference, so a reviewer who opens no reference
   cannot run one pass and believe the check complete.
2. **Anchor a description-level finding once.** Where the drift is a
   property of the description rather than of any particular line, the
   finding carries its primary anchor alone; a second location is added
   only where that site independently shows the drift.

### Non-goals

- No change to the `description-drift` category, the `--json` shape, or
  what counts as "not a finding" (terse and informal descriptions stay
  out). Precision is already 100% and the goal is not to trade it away.
- No change to how `title`/`body` reach the review.
- Not a fix for the item 4 lens gaps (double-encoding ×3 and friends), which
  are detection, not description.

## Implementation

### Both directions

`references/pr-description.md` is restructured around the two directions,
each with its own bolded heading, and the undersell bullet is rewritten to
say why direction 1 misses it: "Nothing in the description is false, which
is exactly why direction 1 misses it — the finding is the silence." Direction
2 is scoped to substance (a new feature path, dependency, migration, public
surface, or a behavioral change to an existing one), explicitly not to every
file the diff touches, so it does not become a diff inventory.

`SKILL.md`'s step 5d and the harness body's step 10 each name both
directions inline, with the one-sentence reason the second is needed. The
harness body also carries the single-anchor rule, since it has no reference
to defer to.

### Single anchor

A paragraph in the reference and a sentence in the harness body: a
description-level finding carries its primary anchor alone, with a second
location only where that site independently shows the drift. The worked
contrast is stated — "a claim contradicted at three call sites is three
sites; a description that undersells the PR's scope is one finding about the
description, however many files the unmentioned scope spans" — because the
abstract rule alone is what the fan-out violated.

### The test

`DescriptionCheckDirectionsTest` asserts all three surfaces (SKILL.md, the
harness body, the reference) name both directions, via two proxy patterns:
`both directions`, and one of `never mentions`/`does not mention`/
`unmentioned`. Verified non-vacuous against `git show HEAD:<path>` — all
three files miss on the pre-fix text and match after.

Budgets: SKILL.md 324/330 and the rendered harness body 129/140 after the
change, so nothing is compressed to fit.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.255 → 0.6.256.

## Readiness attestation

### Problem and motivation

The description check's procedure is claim-driven, so it structurally
cannot find an undersell — and the benchmark confirms it never has.

Evidence: `plugins/s/skills/review/references/pr-description.md` as shipped
reads "For each concrete claim about what the PR adds, changes, or fixes,
check it against the actual diff"; `SKILL.md` step 5d reads "verify every
claim against the diff"; the harness body's step 10 reads "A title/body
claim the diff contradicts or exceeds". benchy-cf's three-round measurement
has apilix `WORKSPACES.md:1` at 0/3 on both 0.6.252+desc and 0.6.253+desc,
while the other two golden drift cases reach 3/3.

### Scope and non-goals

In scope: the two-direction restructure on all three surfaces, the
single-anchor rule, the parity test, the version bump. Out of scope: the
category, the `--json` shape, the terse-description exclusion, and item 4's
detection lenses.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review`/`review-skill` (base `154f3c2c968d`). Files:
`plugins/s/skills/review/references/pr-description.md`,
`plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`. Runnable premises: the change is
applied and measured in this worktree — SKILL.md 324, rendered harness body
129, 235 review tests green — and the new test's non-vacuity was confirmed
by matching its patterns against `git show HEAD:` for all three surfaces
(all False before, all True after).

### No open task-shaping decision

- Whether to reword the undersell example or add a second direction: the
  second direction. Rewording the example would leave the procedure above it
  unable to reach the case, which is the actual defect.
- How far direction 2 reaches: substance only — a new feature path,
  dependency, migration, public surface, or behavioral change — settled
  above, so the pass does not degrade into a diff inventory.
- Whether the single-anchor rule needs the concrete contrast rather than
  just the rule: yes, for the same reason the impact floor needed its
  `move_file` example.
- Whether all three surfaces need the directions named, or just the
  reference: all three, since a reviewer who skips the reference would
  otherwise run one pass believing the check complete.
