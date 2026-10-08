# review-verifier-rubric
Status: verified
Theme: reliability

## Idea

### Motivation

v0.6.269 moved severity to the verify stage — "severity SHALL be the
verifier's: an earlier pass may propose one and the verifier overrides it" —
and the spawn message carries only each candidate's index, location, claim and
why it was suspected. A cold `general-purpose` verifier never reads `SKILL.md`.

So the point of rating now sits with an agent that has **no rubric at all**:
not v0.6.262's concrete instances, not the impact rule, and not the exposure
floor that makes a secret, credential or authorization-boundary finding `high`
whatever the reviewer's confidence.

That is the failure v0.6.255 and v0.6.261 each measured — a severity rule that
is not present where rating happens. v0.6.262 fixed it by putting concrete
recognisable instances at the point of rating, and benchy-cf measured all three
target issues lifting to `medium` in 3 of 3 rounds. v0.6.269 then moved the
point of rating away from the rubric and undid the condition that made it work.

**There is already evidence, from the review of pull request 279.** A verifier
there confirmed a PR-description drift finding at `high`. The reviewing session
disagreed in its own report — by the skill's rubric, informational drift with
no functional impact is nothing like `high` — but deferred, because the spec
hands severity to the verifier. A rating that far outside the rubric is what a
rater without the rubric produces.

### Details

The spawn message carries the severity rubric, quoted from the rating step the
composing session has just read.

### Non-goals

- **No second copy of the rubric in the repository.** The composing session has
  the rubric in its own context when it spawns the verifier, so the instruction
  is to include it, not to maintain a duplicate. Two copies of a constant is
  how the line-ceiling figures drifted across requirements, and a rubric is
  more valuable to keep single-sourced than a number.
- No change to the rubric's content, to what else the spawn carries, to the
  verdict shape, or to the payload.
- No change to severity ownership. The verifier still decides. It will now
  decide with the rule in front of it.
- Not a claim that this improves severity. v0.6.262 earned that result; this
  change only stops the verify stage undoing it. The honest success condition
  is **parity with v0.6.262**, not improvement.

## Implementation

### What the spawn carries

`references/verification.md`'s "What the verifier receives" gains the severity
rubric: the composing session includes it **verbatim, as it appears in the
rating step it has just read** — the `high`, `medium` and `low` definitions,
the impact rule with its concrete instances, and the exposure floor.

Quoting rather than duplicating is the point. The rubric lives in one place per
surface, and the spawn is composed at runtime by a session that already has it.
A copy checked into `verification.md` would be a second source that drifts the
first time the rubric changes, and the rubric has changed in four of the last
ten versions.

### Why the whole rubric, not only the instances

benchy-cf's prediction concerns v0.6.262's concrete instances, and those are
the measured part. But the verifier is equally missing the exposure floor,
which is the one absolute in the rubric: a credential exposure or an
authorization boundary reached without a scope check is `high` regardless of
confidence. A verifier that downgraded one of those would be a worse failure
than a `low`/`medium` drift, and it would not show up in benchy-cf's severity
targets at all, since none of them is an exposure case. So the whole rubric
goes, not the fashionable part of it.

### The harness body

A harness-installed review has no `SKILL.md` to quote from, so the same
instruction points at that body's own rubric step. The substance must be inline
there, as always, and the body is at 189 of 200 in its worst case.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.270 → 0.6.271.

## Readiness attestation

### Problem and motivation

Severity is decided by an agent that cannot see the severity rubric.

Evidence: `references/verification.md` lines 20 to 24 list what the spawn
carries — index, location, claim, why — and name no rubric. The same file makes
severity the verifier's own judgement, overriding any proposal. The verifier is
spawned `subagent_type: general-purpose`, so it reads no skill file. In the
review of pull request 279 a verifier confirmed a description-drift finding at
`high` and the reviewing session recorded its disagreement on rubric grounds.

### Scope and non-goals

In scope: the spawn message's contents on `references/verification.md` and
`plugins/s/harness/bodies/review.md`, a test pinning that each surface requires
the rubric in the spawn, and the version bump.

Out of scope: the rubric's content, severity ownership, the verdict shape, the
payload, and any second copy of the rubric in the tree.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review` requirement `review-skill`, base `21821aefea22`,
computed with `spec_status.py base-hash` in this worktree. Files:
`plugins/s/skills/review/references/verification.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `verification.md` states what the spawn
carries at lines 20 to 24 and names no rubric; the review suite is green at 291
tests; the worst-case rendered harness body is 189 against a 200 ceiling;
`SKILL.md` is 377 against 400.

### No open task-shaping decision

- Quote the rubric or check in a copy: quote it, because a second copy drifts
  and the rubric has changed in four of the last ten versions — settled above.
- The whole rubric or only the concrete instances: the whole rubric, because
  the exposure floor is an absolute whose loss would not show in the measured
  targets — settled above.
- Whether severity moves back off the verifier: not here. That is the response
  if this fix fails to hold parity — settled above and registered with
  benchy-cf.
