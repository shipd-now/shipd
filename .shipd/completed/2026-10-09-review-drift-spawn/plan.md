# review-drift-spawn
Status: verified
Theme: reliability

## Idea

### Motivation

v0.6.273 gave `description-drift` candidates their own verifier spawn, and
specified that spawn as carrying "the description and no diff". A drift finding
is a mismatch *between* the description and the diff, so a verifier holding only
one of them cannot check the claim at all. Its only available outcomes are
killing for want of evidence or confirming on the description alone.

The error is visible in the text that introduces it. `verification.md` line 96
states the premise — "its claim is a relationship between the description and
the diff, not a property of the diff alone" — and line 100 then draws the
opposite conclusion. I wrote the correct reasoning and concluded against it,
because the blind defect spawn suggested a mirror image rather than an
asymmetry.

benchy-cf caught it from the spec before their round finished, which is the
second design error they have found by reading rather than measuring.

Two reporting gaps surfaced with it. A `killed` entry carries `candidate`,
`location`, `what` and `reason` but no `category`, so a drift kill can only be
identified by parsing prose. And `verifier.candidates` is a single count, which
was unambiguous when there was one spawn and is not now there are two.

### Details

The drift spawn carries the description **and** the diff. Killed entries carry
their category. The verifier block reports a count per spawn.

### Non-goals

- The defect spawn stays blind. The description must not reach it, and that is
  the one thing this change could break by accident.
- No change to the two rubrics, the verdict shape, discovery order, or severity
  ownership.

## Implementation

### The asymmetry, stated as an asymmetry

The defect spawn carries the diff and **not** the description, so a description
cannot talk a verifier out of a defect that was already detected. The drift
spawn carries **both**, because the comparison between them *is* the finding.

That is not a mirror image, and the text will say so explicitly, since the
mirror reading is what produced the error.

### Category on killed entries

Each `killed` entry gains `category`, the same taxonomy value the finding
carried as a candidate. Without it a consumer cannot tell a drift kill from a
defect kill except by reading prose, which is what benchy-cf is currently
reduced to.

### Per-spawn candidate counts

`verifier` reports the count for each spawn rather than one total: the defect
spawn's and the drift spawn's. A single `candidates` number cannot say which
spawn a position belongs to, and positions are zero-based within their own
spawn, so the total is ambiguous the moment two spawns exist.

The existing `candidates` field keeps its name and meaning as the total, with
the per-spawn breakdown beside it, so a consumer reading the old field is not
silently given a different number than it expects.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.273 → 0.6.274.

## Readiness attestation

### Problem and motivation

The drift verifier cannot check the claim it is spawned to check, and kills are
not identifiable by category.

Evidence: `plugins/s/skills/review/references/verification.md` line 96 states
that a drift claim is a relationship between description and diff, and line 100
specifies a spawn carrying "the description and no diff". The `killed` array at
`json-output.md` line 44 carries `candidate`, `location`, `what` and `reason`
and no `category`. `verifier` carries a single `candidates` count, written when
one spawn existed.

### Scope and non-goals

In scope: the drift spawn's contents, the stated asymmetry, `category` on killed
entries, per-spawn candidate counts, both reference-free surfaces, the payload
references, tests, the version bump.

Out of scope: the defect spawn's blindness, the two rubrics, the verdict shape,
discovery order, severity ownership.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review` requirement `review-skill`, base `6959e59439e4`,
computed with `spec_status.py base-hash` in this worktree. Files:
`plugins/s/skills/review/references/verification.md`,
`plugins/s/skills/review/references/json-output.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/harness/references/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: the drift-exception paragraph sits at
`verification.md` lines 95 to 101 and specifies no diff; the `killed` schema at
`json-output.md` lines 44 to 51 has four fields and no category; the review
suite is green at 303 tests; the worst rendered harness body is 233 of 250.

### No open task-shaping decision

- Whether the drift spawn gets the diff: yes, both, because the comparison is
  the finding — settled above.
- Whether the defect spawn changes: no, and the text will name that as the
  asymmetry rather than leaving a mirror reading available — settled above.
- Whether `candidates` is repurposed or kept: kept as the total, with per-spawn
  counts beside it, so an existing consumer is not handed a changed meaning
  under an unchanged name — settled above.
