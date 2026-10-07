# review-severity-calibration
Status: verified
Theme: reliability

## Idea

### Motivation

Item 2 of the ReviewBench handoff (shipped v0.6.250) redefined `low`
severity as a list of defect *kinds* — a swallowed error, a resource leak on
a rare path, dead or duplicated code, an unread field, an unstable identity,
a blocking call in an async context. The reviewer is reading that list as a
severity rule rather than a kind list, so a defect that merely *resembles*
one of those kinds gets rated `low` regardless of what it actually does.

`low` never blocks a merge. So the regression is not cosmetic. From
benchy-cf's classification of the extra low findings v0.6.252 produced:

- chronicle `move_file`: if `chmod` fails after the rename, the code deletes
  the destination while the source is already gone — the file is lost.
  Rated `low`, because it arrived as a swallowed error.
- Database and file permissions applied *after* creation, leaving a window
  where they are wrong. Rated `low`, because it arrived as a rare-path
  issue.

Both are the kind of defect the gate exists to stop, and both were rated so
they could not stop it. This is a regression my own item-2 wording caused,
and it is the most consequential thing the benchmark has surfaced.

### Details

State the floor the rubric is missing: the low list names kinds of defect,
not severities. Rate by what the defect does — data loss, data corruption, a
security exposure, or a broken guarantee is `medium` or `high` however
minor the kind it arrived as. Add it beside the existing exposure floor,
which already does exactly this job for secrets and authorization, and
mirror it into the harness body, which carries its own copy of the rubric.

### Non-goals

- No change to the low list's contents. The kinds are right; what was
  missing is that they do not set the severity.
- No change to the high/medium definitions, the exposure floor, or the
  blocks/never-blocks rule.
- No change to the copilot template's rubric, which still carries the older
  style-and-nits wording — a tracked inconsistency from item 2, out of
  scope here as it was there.
- Not a recall change. This moves findings between severities; it does not
  change which defects get found, so it cannot move the benchmark's recall
  numbers either way.

## Implementation

### The floor

A new `**Impact floor.**` bullet in `SKILL.md`'s severity rubric, directly
after the `low` bullet and before the existing `**Exposure floor.**`, whose
shape it deliberately copies:

```
- **Impact floor.** That low list names *kinds* of defect, not severities. Rate every
  finding by what it does, not which kind it resembles: data loss, data corruption, a
  security exposure, or a broken guarantee is `medium` or `high` even when it arrives
  as one of those kinds. A swallowed error that loses a file is not low.
```

The concrete counter-example is deliberate: `move_file` is the real case
that motivated this, and a rule stated only in the abstract is what failed
the first time.

`plugins/s/harness/bodies/review.md` gets the same floor in its own prose
style (it has no bullet sub-structure there), folded in ahead of its
existing exposure-floor sentence.

The breadth sweep's step also shifts: it currently sends the reviewer
looking for "a remaining low-severity defect of the categories named in the
rubric below", which presumes the categories imply low severity. It becomes
"a remaining defect of the minor kinds named in the rubric below", with an
explicit instruction to rate what it finds by the impact floor rather than
by the kind that surfaced it.

Both surfaces have room: SKILL.md is at 316/330 and the rendered harness
body at 119/140 after the preceding headroom change, so nothing is
compressed to fit this.

### The test

`ImpactFloorParityTest` in `test_skill_references.py` asserts both surfaces
state the floor, mirroring `_exposure_floor_stated`'s proxy-pattern
approach: one pattern for "kinds of defect, not severities" (tolerating
markdown emphasis inside the phrase) and one for impact words landing near
`medium`/`high`. Verified non-vacuous — both patterns miss on the pre-fix
text of both files and match after, checked against `git show HEAD:<path>`
rather than assumed.

The copilot template is excluded from that parity test, with the reason
recorded in the test's docstring: it carries the older rubric, so the floor
does not apply to it.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.254 → 0.6.255.

## Readiness attestation

### Problem and motivation

The low rubric's kind list is being read as a severity rule, so defects
that cause data loss are rated `low` and `low` never blocks a merge.

Evidence: `plugins/s/skills/review/SKILL.md`'s severity rubric lists six
defect kinds under `low` with no statement that impact overrides the kind;
benchy-cf's classification of v0.6.252's low findings names chronicle
`move_file` (a lost file on a failed `chmod` after rename) and
permissions-applied-after-creation as rated `low`; the same rubric states
"Any high **or** medium finding blocks (Fix required); low never blocks."

### Scope and non-goals

In scope: the impact floor on both rubric surfaces, the breadth sweep's
wording that presumed kind implies severity, the parity test, the version
bump. Out of scope: the low list's contents, the other severity
definitions, the copilot template, and anything affecting recall.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review`/`review-skill` (base `76402ad7fc2b`, from
`spec_status.py base-hash`). Files: `plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`. Runnable premises: the change is
already applied and measured in this worktree — SKILL.md 321/330, rendered
harness body 124/140, 233 review tests green — and the new test's
non-vacuity was confirmed by matching its patterns against
`git show HEAD:` for both files (both False before, both True after).

### No open task-shaping decision

- Where the floor goes: beside the exposure floor, whose shape and
  vocabulary it copies — settled above.
- Whether to restate the concrete `move_file` counter-example rather than
  only the abstract rule: yes. The abstract rule alone is what the item-2
  wording already implied and the reviewer still got wrong.
- Whether the breadth sweep's wording needs the same correction: yes, it
  explicitly asked for a "low-severity defect of the categories", baking in
  the confusion — settled above.
- Whether the copilot template is in scope: no, unchanged from item 2's
  reasoning — settled above.
