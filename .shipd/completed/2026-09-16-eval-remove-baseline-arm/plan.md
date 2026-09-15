# eval-remove-baseline-arm
Status: verified

## Idea

Remove the eval harness's A/B baseline arm, and repair the handoff grader so the
remaining graders work as a single-arm regression gate.

### Motivation

The baseline arm cannot measure what a skill contributes: `assemble_scratch`
injects the host's 53KB grammar authority into every fixture, and a plugin-less
session read it and authored a complete shipd change. The handoff grader is
separately broken, failing correct sessions it told to continue.

### Details

- Remove `--arm`, `baseline_prompt`, `_arm_refusal`, `_refused_results`, the
  `RunResult.refused` field, per-arm keying in `summarize`, and `main`'s
  invocation-level refusal.
- Stop resuming a handoff-graded session, and give every grader its own gate and
  reply instead of branching behavior against everything else.
- Restore `summarize` to per-case rows and a pass-rate-driven exit code.
- Repair the handoff grader to compare authored content rather than the whole
  tree, so engine scaffolding no longer reads as a session change.
- Keep `--runs`, all three graders, and every case including `fix-spec-wrong`.
- Document the single-arm gate in `AGENTS.md`'s `## Evals` section.

Affected capabilities: `skill-evals` (modified). Impact: `evals/run.py`,
`evals/tests/test_runner.py`, `AGENTS.md`. Stdlib only. Nothing under
`plugins/s/`, so no plugin version bump.

### Non-goals

- No change to `/s:fix`. It honors branch B and stops; the harness was driving
  it past that point, so nothing under `plugins/s/` needs editing.
- No removal of any case or grader — the gate keeps all three.
- No change to how `assemble_scratch` injects the grammar authority; with no
  baseline arm there is nothing left for it to contaminate.
- No quarantine or expected-fail mechanism for a red case.

## Implementation

- **The handoff grader compares authored content, not the whole tree.** A run
  fails when a file present at assembly was modified or deleted, or when a new
  file appears under `src/` or under any `.shipd/verified/` or `.shipd/planned/`
  directory anywhere in the scratch. Engine scaffolding — `.shipd/schema`,
  `completed/`, `research/`, `shipd.config.example.json` — is created by tooling
  rather than authored by the session, so it no longer fails a run. Rejected:
  excluding those four names, which is a whitelist that rots the moment the
  engine writes a fifth.
- **The `.shipd/` globs run across the whole scratch, not just its root.**
  Observed runs wrote the planned change both at the scratch root and inside a
  fresh `.worktrees/<name>/`; a root-only check would make the red intermittent.
- **`summarize` returns to per-case rows.** Its results map is keyed by case
  name again, one row per case, exit code non-zero when any case's pass-rate is
  below 1.0. Rejected: keeping the `(case, arm)` key with a single arm — dead
  structure carrying a concept the harness no longer has.
- **`--runs` stays.** It repeats a case to measure flakiness, which is
  independent of the removed comparison.
- **A handoff-graded session is never resumed.** Its correct outcome is that
  the session stops, so resuming it is incoherent: the run ends after turn 1 and
  is graded there. Rejected: resuming with a neutral reply — any reply at all
  invites a stopped session to continue, which is the behavior under test.
- **Every grader selects its own gate and reply.** `run_conversation` currently
  branches `behavior` against everything else, so a handoff case silently
  inherits the structural gate — which a `/s:fix` session can never satisfy, so
  the resume cap is always spent — and `GOAHEAD_REPLY`, whose text is "Complete
  the plan through emission, lint, and promotion to ready". The harness
  instructed the violation it then failed the session for. Transcripts confirm
  it: turn 1 stopped correctly and turn 2 reported the change "planned,
  installed, lint-clean, and promoted to `ready`".
- **The delta removes three requirements and restates one.** `arm-selection`,
  `derived-baseline-prompt`, and `baseline-requires-behavior` are removed
  outright; `pass-rate-reporting` returns to its pre-A/B wording; and
  `handoff-grading` is restated for the authored-content comparison.

Risk: narrowing from whole-tree to authored content could re-open the gameability
the whole-tree snapshot closed — a session rewriting a shipped test. The
modified-or-deleted rule still catches that, since the shipped tests exist at
assembly; only *new* files outside the three authored locations are tolerated.

Risk: ending a handoff run after one turn loses the resume loop's tolerance for a
session that stops early for an unrelated reason. That is accepted — for this
grader a session that stopped is the passing case, and the four assertions still
decide the verdict.

## Questions and answers

### Q1: Does a regression case that legitimately fails ship red? (premise void)
- **Question:** With the handoff grader repaired, `fix-spec-wrong` still fails,
  because `/s:fix` authors a planned change instead of stopping at the hand-off.
  Options: (a) ship the case red and fix `/s:fix` separately; (b) fix `/s:fix`
  in this change, widening scope into `plugins/s/` and forcing a version bump;
  (c) loosen the grader to tolerate a planned change. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Ship the case red — option (a). A session failing the handoff
  grader by producing a change is a real result about the skill, not a defect in
  the case or the grader, so it is reported rather than smoothed away by
  loosening the grader or holding the case. Repairing `/s:fix` is its own
  change, and the harness's non-zero exit on a sub-1.0 pass-rate is the standing
  signal that the defect is open.
- **Cited:** completed/2026-09-15-eval-handoff-case, verified/skill-evals
- **Not applied:** the consultation's premise was disproved after it returned.
  Session transcripts show `/s:fix` stopped correctly at turn 1 and only
  authored a change after the harness resumed it with a reply instructing
  exactly that, so no case fails legitimately and nothing ships red.
