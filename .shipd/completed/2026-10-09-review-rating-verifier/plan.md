# review-rating-verifier
Status: verified
Theme: reliability

## Idea

### Motivation

The impact floor names four categories — data loss, data corruption, a security
exposure, a broken guarantee — and tells a reviewer to rate by what a defect
does rather than by the kind it resembles. Categories are harder to recognise
in a diff than situations. v0.6.262 added three concrete instances beside the
floor and all three of ReviewBench's severity targets moved to `medium` in 3 of
3 rounds, holding through v0.6.273.

That result is the strongest surviving item in this series, for a reason that
only became clear today. A v0.6.260 re-run scored 8.7 against the 11.0 the same
version scored two days earlier, so the **set-to-set spread for one version is
2.3** — larger than almost every effect this series attributed to a prompt
change. Every result that replicated is a per-finding count; every result that
failed to replicate is a mean difference. Three named targets at 3/3 is a
per-finding count.

### Details

The impact floor gains three concrete instances on every surface that states
it. Nothing else changes.

### Non-goals

- **No verifier, of any kind.** The rate-but-never-kill verifier was queued
  ahead of this change on the premise that it "keeps the measured severity
  gain". That premise was wrong: v0.6.262 carried no verify stage at all —
  `git show e6d0227` has zero mentions of one — and the first arrives six
  versions later. The gain belongs to this wording, so the wording is what
  gets tested. A verifier now has to justify itself on its own evidence.
- **No `low` bullet change.** v0.6.262's instances rode on v0.6.261's
  contained-impact `low`; this change puts them on v0.6.260's kinds-list `low`.
  That pairing has never been measured and it is deliberately the only variable
  — changing both would reproduce v0.6.262 rather than test its parts.
- No ceiling change on either surface. Both fit.

## Implementation

One sentence, appended to the impact floor on three surfaces, naming the three
instances v0.6.262 used: a success response that hides a failure; a cleanup
path that drops the record and leaves the data, or the reverse; an error path
that loses the only copy.

- `plugins/s/skills/review/SKILL.md` — the `Impact floor.` rubric bullet.
- `plugins/s/harness/bodies/review.md` — its inline rate-by-impact sentence,
  which must carry the instances in full because that file ships standalone and
  can read no reference.
- `plugins/s/integrations/copilot/SKILL.md` — its own copy of the floor.

### The budget, measured rather than estimated

`SKILL.md` goes 332 → **336** against its 340 ceiling. The worst rendered
harness body goes 141 → **145** against 150, still `review` on `aider`. Both
fit, so no ceiling moves and neither owning requirement is touched. Measured by
rendering all 390 command-by-harness pairs, not by counting source lines — that
distinction cost a wrong prediction two versions ago, when arithmetic said 138
and `aider` rendered 141.

### What the test must pin

A test asserting the instances are present on all three surfaces, and
non-vacuous: it must fail against the pre-change text. Two traps this file has
hit — a phrase matched as a plain substring stops matching when the source
wraps at 88 columns, and an assertion that already passed before the change
proves nothing. Normalise whitespace, and prove the failure against
`origin/main`.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.275 → 0.6.276.

## Readiness attestation

### Problem and motivation

The impact floor names four categories without naming a recognisable instance
of any of them, and the one measured fix for that — v0.6.262's three
instances — was reverted as part of a bundle rather than on its own evidence.

Evidence: at v0.6.262 `move_file`, `QuerySummaries` and `cleanup_media` all sat
at `medium` in 3 of 3 rounds, with no verify stage in the skill at that version.
At v0.6.275 `QuerySummaries` is `low` 3/3 and `move_file` low/medium. The
v0.6.260 re-run establishes the 2.3 set-to-set spread that makes per-finding
counts the only usable measure.

### Scope and non-goals

In scope: one sentence on three surfaces, one MODIFIED requirement, one test,
the version bump.

Out of scope: any verifier, the `low` bullet's own wording, both ceilings, the
payload schema, and `semdiff`.

### Affected capabilities and files

One capability, one requirement: `semantic-review` / `review-skill`, base
`08f1f7fdef3a` as computed by `spec_status.py base-hash` in this worktree.

Files: `plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured in this worktree: `SKILL.md` is 336 lines against
its 340 ceiling with the change applied, and was 332 before; the worst rendered
harness body is 145 against 150 with the change applied, and was 141 before,
both measured by rendering every registered harness; `git show
e6d0227:plugins/s/skills/review/SKILL.md` contains no mention of a verifier;
and all three surfaces carried the floor without any instance before this
change.

### No open task-shaping decision

- Whether a verifier ships here: no, because the gain it was supposed to
  preserve predates every verifier — settled above with the command that
  shows it.
- Which `low` bullet the instances sit beside: v0.6.260's kinds list, kept
  unchanged, so the instances are the only variable — settled above.
- Whether either ceiling moves: neither, both measured to fit — settled above.
- What counts as success: registered with the measuring session before the
  build, per target rather than all-or-nothing, because the kinds list names
  "swallowed errors" and so competes with the instance for one target.
