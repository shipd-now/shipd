## ADDED Requirements

### Requirement: Detached pre-build drift step
id: detached-pre-build-drift

Before the detached driver drives a member's built-in `build` stage — in an
epic run or a targeted drive entering at build, never for a skipped or
replaced build entry — it SHALL run a pre-build step in this order, through
its injectable command, session, gate, and judge seams. First it SHALL
resolve the base ref: a best-effort `git fetch origin main` from the
repository root, then `origin/main` when `git rev-parse --verify --quiet`
resolves it, else `main`. If any `After` dependency of the member is not
merged into that ref (the base-branch tree check), then the member SHALL
park as `needs-human` at stage `dependency` with a reason naming the
unmerged dependencies and the ref, with no session id. It SHALL then merge
the ref into the member's worktree with `git merge --no-edit <ref>`; if the
merge fails, then it SHALL abort the merge and park the member as
`needs-human` at stage `sync` with the merge's first output line. It SHALL
then run `spec_status.py --root <worktree> drift <member> --base <ref>
--json` in the worktree: exit 0 proceeds to build; exit 4 triggers the
judgment; any other exit, or unparseable output, parks the member as
`needs-human` at stage `drift` with the exit code and first stderr line.
The judgment SHALL be one headless turn whose prompt names `/s:drift
<member> --base <ref> --json` and asks for exactly its JSON object, retried
up to the build entry's fresh-attempt budget, each turn's `result` text
parsed with a code fence or surrounding prose tolerated: the member's entry
in `verdicts` gives the verdict, a member listed under `clean` counts as
`holds`, and an `error`, a missing entry, or an unknown verdict word fails
the attempt. An exhausted budget SHALL park the member as `needs-human` at
stage `drift` with the failure and the judge session id. A `holds` verdict
SHALL proceed to build. A `conflict` verdict SHALL park the member as
`needs-human` at stage `drift` with a reason naming the `contradicts`
value and the verdict's reason, with the judge session id. A `revise`
verdict SHALL drive a `replan` session through the enrichment machinery —
the build entry's attempts, timeout, max-resumes, and model, graded on the
member change at `ready` lint-clean — whose prompt names the ref, the
verdict's reason and `revise` text, the drift findings, the rule to keep
every `**Answered by:** USER` answer and epic Decision, the oracle agent
`s:oracle` for un-inferrable decisions, that no human is present, and the
closing `spec_gate.py <member> --root <worktree> --base <ref>` re-gate;
after a successful session the driver SHALL re-run the gate engine with
`--base <ref>`, so the stamp anchors on the synced ref: a pass proceeds
to build, a rejection records the member `rejected` at stage `replan` with
the session id, and a gate failure parks it `needs-human` at stage
`replan`. Exhausted re-plan attempts SHALL park the member `needs-human` at
stage `replan`. The step SHALL NOT re-measure drift after the re-gate and
SHALL NOT redefine the drift verb, the drift skill, or the merged-dependency
check.

#### Scenario: Clean drift builds without a judge
- **GIVEN** a member whose drift verb exits 0 after the worktree merged the
  base ref
- **WHEN** the driver reaches the build stage
- **THEN** the merge and the drift verb ran in the worktree with
  `--base origin/main`, no judge turn ran, and the build session follows

#### Scenario: A holds verdict builds
- **GIVEN** a drift verb exit 4 and a judge turn whose JSON verdict is
  `holds`
- **WHEN** the step runs
- **THEN** the judge prompt names `/s:drift <member> --base origin/main
  --json`, exactly one judge turn ran, and the build session follows

#### Scenario: A conflict parks with the judge session
- **GIVEN** a judge verdict `conflict` contradicting `Q2`
- **WHEN** the step runs
- **THEN** the member is `needs_human` at stage `drift`, the reason names
  `Q2`, the session id is the judge turn's, and no build session runs

#### Scenario: A revise verdict re-plans and re-gates
- **GIVEN** a judge verdict `revise` and a gate that passes after the
  re-plan session
- **WHEN** the step runs
- **THEN** one `replan` session ran with a prompt naming the reason,
  `s:oracle`, `USER`, and `spec_gate.py --base origin/main`, the gate ran
  once more with `--base origin/main`, and the build session follows

#### Scenario: A rejected re-gate records the member rejected
- **GIVEN** a judge verdict `revise` and a gate exiting 2 after the re-plan
- **WHEN** the step runs
- **THEN** the outcome is `rejected` at stage `replan` with the re-plan
  session id and no build session runs

#### Scenario: A transient judge fault is retried
- **GIVEN** a judge turn that fails once and then returns a `holds` object
  wrapped in a code fence
- **WHEN** the step runs
- **THEN** two judge turns ran and the build session follows

#### Scenario: Exhausted judge attempts park the member
- **WHEN** every judge turn of the budget fails or returns unparseable text
- **THEN** the member is `needs_human` at stage `drift` with the attempt
  count in its reason

#### Scenario: A verb error parks without a judge
- **WHEN** the drift verb exits 1
- **THEN** the member is `needs_human` at stage `drift`, the reason names
  exit 1 and the stderr line, and no judge turn or build session runs

#### Scenario: A failed sync aborts and parks
- **WHEN** `git merge --no-edit origin/main` exits non-zero
- **THEN** `git merge --abort` runs and the member is `needs_human` at
  stage `sync`

#### Scenario: An unmerged dependency parks before the sync
- **GIVEN** a member whose `After` names `a` and a base tree holding no
  `completed/` entry for `a`
- **WHEN** the step runs
- **THEN** the member is `needs_human` at stage `dependency` naming `a`,
  and no merge, drift verb, or build session runs

#### Scenario: Replaced and skipped build entries run no step
- **WHEN** the build entry is replaced by a command or skipped
- **THEN** no merge, drift verb, or judge turn runs for the member

#### Scenario: A targeted ready member gets the step
- **GIVEN** a `ready` member driven with the targeted single-member drive
- **WHEN** it enters at build
- **THEN** the drift verb runs before its build session

### Requirement: The detached run continues past a parked dependency
id: detached-dependent-continue

While driving an epic run's members in order, the autopilot SHALL record
each member's outcome, and when a member's `After` names a member driven
earlier in the same run whose outcome is not `shipped`, it SHALL NOT drive
that member: it SHALL record it `needs-human` at stage `dependency` with a
reason naming the dependency and that dependency's outcome and no session
id, write that outcome to the heartbeat roster, and continue with the next
member. A member none of whose dependencies parked SHALL be driven exactly
as before.

#### Scenario: A dependent of a parked member is not driven
- **GIVEN** members `a` and `b` with `b` after `a`, and a driver that parks
  `a` as `needs_human`
- **WHEN** the run executes
- **THEN** the driver is invoked for `a` only, and the report's `needs_human`
  holds `b` at stage `dependency` with a reason naming `a` and `needs_human`

#### Scenario: A dependent of a shipped member is driven
- **GIVEN** `b` after `a` and a driver that ships `a`
- **WHEN** the run executes
- **THEN** the driver is invoked for `a` then `b`

#### Scenario: A dependent of a drafted member waits
- **GIVEN** `b` after `a` and a driver that records `a` as `drafted`
- **WHEN** the run executes
- **THEN** `b` is reported `needs_human` at stage `dependency` and the
  summary line for it carries no `claude --resume` fragment

### Requirement: Session turn result text
id: session-turn-result-text

The session driver SHALL provide `run_turn_result(prompt, cwd,
resume_id=None, timeout, claude_bin, extra_args=None)` returning `(ok,
failure, session_id, result_text)` where `result_text` is the headless
turn's transcript `result` string, or an empty string when the transcript
is not JSON or carries no string `result`; `run_turn` SHALL return the
first three values unchanged for every existing caller. A helper
`result_text_from_transcript(text)` SHALL expose the same extraction.

#### Scenario: The result text is returned
- **GIVEN** a `claude_bin` that prints `{"session_id": "s1", "result":
  "{\"mode\": \"change\"}"}` and exits 0
- **WHEN** `run_turn_result` runs
- **THEN** it returns `ok` true, session id `s1`, and the inner object text,
  while `run_turn` on the same binary returns `(True, None, "s1")`

#### Scenario: A non-JSON transcript yields an empty text
- **WHEN** `result_text_from_transcript("not json")` is called
- **THEN** it returns an empty string
