# eval-headless-oracle-default
Status: verified
Planned-at: c938fcbcfabf09ae41549d7e931f720b87f451d4
Gated-hash: 36062f7595d8

## Idea

Add an `oracle-default` grader and a `plan-oracle-default` case, so the eval
harness guards how a headless `/s:plan` run settles a decision nothing on disk
can answer: it consults the oracle first, then adopts the planner's own
recommended default.

### Motivation

No eval covers the oracle rung. The three `/s:plan` cases carry no
task-shaping decision, so their runs never consult the oracle, and the
structural grader would pass a plan that skipped the rung or left an
`INSUFFICIENT` entry with no answer. A regression in the rung or the ledger
grammar would ship unnoticed until a person read a plan.

### Details

- Add `oracle-default` to the recognized graders, selected by `expect.json`.
- Grade an `oracle-default` run on four points: the plan lints clean, the gate
  passes, at least one `## Questions and answers` entry carries an oracle
  `**Verdict:**`, and every `INSUFFICIENT` entry records an adopted answer.
- Make the judgement a pure function of the plan text and the lint and gate
  outcomes, and unit-test it against hand-written `plan.md` fixtures.
- Drive the case with the structural gate and the plan-specific go-ahead
  reply, so a run stops resuming once a lint-clean `ready` change exists.
- Add the `plan-oracle-default` case: the report CLI fixture, a wiki store
  holding one unrelated page, and a request to add a `--sort` flag whose
  bare-flag column nothing on disk settles.
- Document the grader and the case in `AGENTS.md`'s `## Evals` section.

Affected capabilities: `skill-evals` (modified). Impact: `evals/run.py`,
`evals/tests/test_runner.py`, `AGENTS.md`, new `evals/cases/plan-oracle-default/`.
Stdlib only, nothing under `plugins/s/`, so no plugin version bump.

### Non-goals

- No paid eval run. The case is exercised by a person later, on request.
- No change to the `structural`, `behavior`, or `handoff` graders.
- No assertion on the `**Queued:**` field. A repository with no wiki store
  queues nothing, and the ledger grammar allows that.
- No assertion that a verdict is `INSUFFICIENT`. The four points are the
  contract; the fixture is built so that `INSUFFICIENT` is the correct verdict.
- No fix to `main()` reading `args.binary`; that is a separate change.

## Implementation

- **The judgement is pure; collecting its inputs is not.**
  `judge_oracle_default(plan_text, lint_exit, gate_exit, ...)` returns a
  `RunResult` from its arguments alone and touches no file or process.
  `grade_oracle_default(scratch_dir)` finds the one change, runs `spec_lint.py`
  and `spec_gate.py --check` against the tree it lives in, reads `plan.md`,
  and hands all of it to the judge. The unit tests drive the judge with
  literal plan text, so no fixture tree and no model call is needed.
- **"The gate passes" means two things.** The plan reads `Status: ready`, which
  only the gate's own pass writes, and `spec_gate.py <change> --check` exits 0
  now. Check mode is read-only, and on a stamped plan it also fails a plan
  edited after it was gated. Rejected: re-running the mutating gate inside the
  grader, which would promote a plan the session never gated.
- **An adopted answer is a non-empty `**Answer:**` under an `**Answered by:**`
  of `USER` or `ORACLE`.** The gate already rejects `PLANNER`, and the linter
  only checks the field is present. Under the harness's go-ahead reply the
  planner records its default as `USER`, which is what `emission.md` prescribes
  for a typed resolution of an `INSUFFICIENT` entry.
- **Ledger parsing mirrors the linter.** The section runs from
  `## Questions and answers` to the next `## ` heading, and entries split at
  `### Q<n>:` headings, the same boundaries `spec_lint.py` and the gate's
  provisional check use. A field value runs from its `- **Field:**` line to the
  next field line, so a wrapped answer still counts. Backticks around a
  verdict or answerer are tolerated.
- **The resume gate stays structural.** A run is resumed only until a
  lint-clean `ready` change exists. Gating on the oracle grade would resume a
  finished plan that lacks a verdict, inviting the session to rewrite its own
  ledger until the grade passes.
- **The fixture leaves the decision open on purpose.** The wiki store holds one
  page about flag naming that never mentions sorting, and the verified
  `reporting` spec states no order. A lookup on the decision's terms finds no
  sentence taking a position, so the contract's verdict is `INSUFFICIENT`.

Risk: the planner may treat the bare-flag column as inferable and never consult
the oracle. That is a real result about the skill, and the grade's failure
names the missing verdict rather than hiding it.

## Readiness attestation

### Problem and motivation

No eval exercises the oracle rung, so a regression in it ships unseen.

Evidence:

- `evals/cases/plan-csv-export/prompt.md`, `plan-new-capability/prompt.md`,
  and `plan-video-brief/prompt.md` each fully specify their change.
- `evals/run.py` `grade` checks one change, lint, and `Status: ready` only.

### Scope and non-goals

The eval harness, its tests, one new case, and `AGENTS.md` change. Nothing
under `plugins/s/` changes.

Evidence:

- In scope: `evals/run.py` grader table, `run_conversation`, `execute_case`.
- Out of scope: the three existing graders and `main()`.

### Affected capabilities and files

One capability, `skill-evals`, gains one requirement and has two modified.

Evidence:

- `case-grader-selection` (base 65eab2107d13) and `grader-selected-driving`
  (base 3956a87b401d), hashes from `spec_status.py base-hash`.
- Runnable premise: `oracle-lookup sort default column report` against a
  freshly initialised wiki store printed `no evidence found — verdict
  INSUFFICIENT`.
- Runnable premise: `spec_gate.py --check` is documented read-only and exits 0
  on pass, 2 on findings.

### No open task-shaping decision

Every decision is settled by the request and by investigation.

Evidence:

- The four graded points are fixed by the request.
- `emission.md` fixes the ledger grammar the grader reads.
