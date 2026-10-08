# review-verify-stage
Status: verified
Theme: reliability

## Idea

### Motivation

`/s:review` reads the files holding defects and reports nothing. The clearest
instance: on apilix round c the reviewer ran `semdiff related`, then read all of
`WorkspaceManagerModal.tsx` with `git show` across two ranges, and reported none
of the three defects in it. Context was not the constraint — benchy-cf's
measurement falsified that hypothesis, 0 of 5 reachable never-matched findings.
The reviewer is self-censoring.

Cursor documented the same failure in their own agentic reviewer: it "hit the
opposite problem: it was too cautious", which they fixed with prompts
encouraging investigation of every suspicious pattern. Unblocking a reviewer
that way raises noise, and noise is what a verifier exists to absorb.

The evidence for building the verifier **before** the unblocking is specific. A
pre-registered ablation removing a verifier-and-acceptance stage found precision
fell 0.471 to 0.353 with no significant recall change, and the verifier retained
93.8% of true candidates. Refute-or-Promote's adversarial stage killed about 79%
of 171 candidates and its survivors produced real CVEs. CR-Bench measured the
opposite order: a "discover missed bugs" loop raised recall 27.01% to 32.76%
while signal-to-noise fell 5.11 to 1.95.

So every later recall idea — the permissive hunt, criterion dispatch, multi-pass
merging — adds candidates that something must filter. This change builds the
filter first. It is deliberately expected to produce **no recall gain**.

### Details

A fresh-context verify stage, between the judgement passes and the report,
confirms or kills each candidate finding and assigns its final severity.

### Non-goals

- **No permissive hunt in this change.** The passes keep behaving as they do.
  Unblocking them is the next version, and separating the two is what lets a
  precision change be attributed to the verifier and a recall change to the
  hunt.
- No criterion dispatch, no multi-pass, no description-blind hunting.
- **No description-blind hunting at all, on current evidence.** benchy-cf
  compared every golden finding across 28 rounds: pooled hit rate 0.340 without
  the description against 0.355 with, and the asymmetry runs the wrong way. The
  confirmation-bias paper's framing — a description asserting the change is
  bug-free — does not occur in this corpus. It is ruled out as a recall lever
  here, and survives only as possible robustness against an adversarial
  description, late.
- No `semdiff` change. This is workflow and reporting.

## Implementation

### The verify stage

A new step sits between judging and reporting. It collects every candidate the
earlier passes produced, spawns **one fresh-context verifier** through the
**`Agent`** tool, and replaces its own severity judgements with the verifier's
verdicts.

The verifier receives the candidate list — location, claim, and why each is
suspected — plus the diff and the ability to read files. It does **not** receive
the hunting reasoning that produced the candidates. Cold start is the property
that matters: Refute-or-Promote attributes its precision to "cold-start
reviewers" that cannot inherit the proposer's conviction.

One verifier per review rather than one per candidate. The anchoring worth
removing is to the hunt's reasoning, which a single cold verifier already
escapes. Per-candidate isolation also removes anchoring *between* candidates,
which is a refinement worth measuring later rather than paying for now.

For each candidate the verifier returns `confirmed` with a severity, or `killed`
with a one-line reason. Severity becomes the verifier's call; an earlier pass
may propose one and the verifier overrides it.

### Kills are output, not an internal filter

Killed candidates appear in the `--json` payload in their own top-level
**`killed`** array — `location`, `what`, `reason` — never inside `findings`.

This is not cosmetic. benchy-cf's scoring converter counts every entry in
`findings` as a reported finding, so a kill placed there with a status flag
would erase the precision gain the stage exists to produce. Keeping them in a
separate array is also what makes retention directly measurable: the number of
kills landing on judge-matched golden findings is the real test of whether the
93.8% retention transferred, and the recall delta alone cannot distinguish a
killed true finding from an ordinary noisy round.

The rendered report names the kill count too, so a human sees what the stage
removed rather than only what survived.

### It must never degrade quietly

The `Agent` spawn can be unavailable — a headless run with a restricted tool
list denies it, which is exactly how benchy-cf's runner is configured today. A
review that lost its verifier and said nothing would be indistinguishable from
v0.6.266 and would pass as a verifier round.

So the payload carries **`verifier`** with a `state` of `ran` or `skipped` and,
when skipped, a `reason`. A skipped verifier also writes an entry into the
report's explicit list of what could not be verified, and findings keep the
severity their passes proposed.

This degrades rather than fails, matching how the skill already handles a failed
difftastic probe or a failed base fetch: a review that still reports findings is
worth more than one that aborts. What it may never do is pretend a stage ran.

### Budget, and where the detail lives

`SKILL.md` is at 357 of 370. The step's **name and summary stay inline**, with
its detail in a new `references/verification.md` — the established pattern, and
the one the extraction rule permits: a check that always applies keeps its name
inline, and only its depth defers.

`plugins/s/harness/bodies/review.md` renders at 159 of 160 and **can read no
reference**, so the verify stage's substance must be inline there. Its ceiling
rises from 160 to 185 in the one requirement that owns it, `body-content`. That
figure is stated there and nowhere else.

Raising it is the right move rather than compressing: the capability's own text
says a ceiling "guards against bloat and is not a budget to compress real
instructions into", and compression on that file has destroyed content three
times in this series.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.267 → 0.6.268.

## Readiness attestation

### Problem and motivation

The reviewer reads the files holding defects and does not report them, and every
technique for unblocking it raises noise that nothing currently filters.

Evidence: benchy-cf's 0.6.266 rounds matched 0 of 5 reachable never-matched
findings, while apilix round c's transcript shows the reviewer reading all of
`WorkspaceManagerModal.tsx` and reporting none of its three defects. The
research report installed at `.shipd/research/review-recall-ideas/report.md`
cites the verifier ablation (precision 0.471 to 0.353, 93.8% true-candidate
retention), Refute-or-Promote's 79% kill rate, CR-Bench's signal-to-noise fall
from 5.11 to 1.95 without a filter, and Cursor's "too cautious" diagnosis.

### Scope and non-goals

In scope: the verify step on both reference-free surfaces, the new reference
file, the `killed` array, the `verifier` state field, the degradation path, the
harness ceiling raise, tests, the version bump.

Out of scope: the permissive hunt, criterion dispatch, multi-pass merging,
description-blind hunting, `semdiff`, and the severity rubric's own content.

### Affected capabilities and files

Two capabilities, three requirements.

Evidence, hashes computed with `spec_status.py base-hash` in this worktree:
`semantic-review` requirements `review-skill` (base `bde2b9198764`) and
`review-skill-references` (base `68b828830597`), and `harness-command-bodies`
requirement `body-content` (base `1a580072d524`). Files:
`plugins/s/skills/review/SKILL.md`,
`plugins/s/skills/review/references/verification.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/references/json-output.md`,
`plugins/s/skills/build/tests/test_harness_bodies.py`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `SKILL.md` is 357 lines against a 370 ceiling;
the rendered review harness body is 159 against 160; `SKILL.md`'s steps run to
7, with step 6 judging new code and step 7 reporting by cohort, so the verify
stage sits between them; eight reference files exist under
`plugins/s/skills/review/references/` and each is named in the References table.

### No open task-shaping decision

- One verifier per review or one per candidate: one per review, because the
  anchoring worth removing is to the hunt's reasoning — settled above, with
  per-candidate isolation named as a later refinement.
- Where kills go: a separate top-level `killed` array, never inside `findings`,
  because the scoring converter counts `findings` entries — settled above, and
  requested by benchy-cf before the first round.
- Fail or degrade when the spawn is denied: degrade, with `verifier.state`
  recorded and a could-not-verify entry, matching the skill's existing
  degradation idiom — settled above.
- Which tool the spawn uses: `Agent`, recorded here so a restricted runner can
  allow exactly that one.
- Who owns severity: the verifier, overriding any proposal — settled above.
- How the harness budget is found: its ceiling rises to 185 in `body-content`,
  never by compression — settled above.
