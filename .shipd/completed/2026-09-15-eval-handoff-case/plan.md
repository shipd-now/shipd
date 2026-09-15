# eval-handoff-case
Status: verified

## Idea

Add a `handoff` grader and a `fix-spec-wrong` case, so an eval can measure the
one outcome where a spec-grounded skill and a bare agent should act
differently: the documented behavior is itself wrong, so the correct move is to
change nothing and say so.

### Motivation

The `fix-report-drift` A/B returned 5/5 against 5/5 on two model tiers, because
a bare agent fixes an easy bug as reliably as `/s:fix` does. Pass/fail on a
solvable bug cannot separate the arms at any capability level.

### Details

- Add `handoff` to the recognized graders, selected by `expect.json`.
- Grade a handoff case on four assertions: `src/` unchanged, the fixture's
  content directory unchanged, the shipped suite still green, and the session's
  final text naming the requirement that documents the wrong behavior.
- Declare that requirement id in `expect.json` as `handoff_requirement`, so the
  grader stays generic.
- Sanity-check a handoff fixture before the session: the shipped suite must
  exit 0, because the code faithfully implements its spec.
- Add the `fix-spec-wrong` case: a `report-column-width` requirement fixing the
  name column at width 6, code implementing it exactly, and a row whose longer
  name misaligns the table.
- Document the third grader in `AGENTS.md`'s `## Evals` section.

Affected capabilities: `skill-evals` (modified). Impact: `evals/run.py`,
`evals/tests/test_runner.py`, `AGENTS.md`, new `evals/cases/fix-spec-wrong/`.
Stdlib only, nothing under `plugins/s/`, so no plugin version bump.

### Non-goals

- No change to the `structural` or `behavior` graders.
- No held-out `verify/` tree for a handoff case; the correct outcome leaves the
  code untouched, so there is no test to flip.
- No assertion that the session named `/s:plan`. That is shipd vocabulary, and
  asserting it would penalize the baseline arm for not knowing it.
- No statistical claim from this one case; it is one instance, not a benchmark.

## Implementation

- **A handoff case is graded on divergent action, not on difficulty.** A bare
  agent asked to fix a misaligned table will patch the format string; a
  spec-grounded one should find that the width is documented, conclude the
  contract is wrong, and stop. That gap widens as models improve, because a more
  capable bare agent patches more confidently. Rejected: making
  `fix-report-drift` harder — difficulty-matching decays with every model
  release, per `.shipd/research/swe-benchmark-rigor/report.md`.
- **The positive signal is the requirement id, never the skill's vocabulary.**
  The grader reads the session's final `result` text from the turn transcript
  and requires the `handoff_requirement` id to appear in it. Any agent that
  correctly diagnosed the contract will name the requirement it read, whichever
  arm it ran in. Rejected: matching on `/s:plan` — the captured position
  `q-eval-fix-grader-scope` holds that a grader asserts the outcome under test,
  never a discipline specific to the skill being graded.
- **Three negative assertions carry the weight.** `src/` unchanged, the
  fixture's content directory unchanged, and the shipped suite still exiting 0.
  Together these fail a session that patched the code, one that edited the spec
  to match, and one that broke something while exploring.
- **The text check alone cannot separate "handed off" from "did nothing".**
  A session that produced no output at all fails the text assertion, and one
  that patched the code fails the diff assertions, so the four together
  distinguish the three outcomes. This is the weakest link in the design and is
  recorded as such: a session could in principle name the requirement while
  reasoning wrongly, and the grader would score it a pass.
- **`handoff` is not `structural`, so the baseline arm is permitted.**
  `_arm_refusal` refuses only a structural grader, so a handoff case accepts
  `--arm baseline` and `--arm both` with no change to that function. The A/B is
  the point of this case.
- **Comparing trees by content, not by git.** The grader compares the scratch
  `src/` and content directory against the case's `fixture/` copies file by
  file, rather than shelling out to git, keeping the check independent of
  whatever the session did to the scratch repo's index.

Risk: `/s:fix` may take branch A and patch the code, failing its own arm. That
is a real result about the skill rather than a defect in the case, and the
report should say so rather than treat it as a broken fixture.
