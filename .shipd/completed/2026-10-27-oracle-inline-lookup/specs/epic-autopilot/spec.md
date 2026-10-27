## MODIFIED Requirements

### Requirement: Oracle-backed gate enrichment
id: oracle-gate-enrichment
base: 9bce2e993633

When the built-in gate stage rejects a member (exit 2), the autopilot SHALL
drive one oracle-backed enrichment phase before parking: headless enrichment
sessions retried on session failure or unmet grade up to the gate entry's
fresh-attempt budget (`autopilot.attempts`, default three), each session
using the gate entry's declared model, timeout, and max-resumes. The
session's prompt SHALL direct running `/s:plan <member>` — which locates the
rejected change and enters enrichment mode — resolving repository-answerable
findings by editing the artifacts, consulting the oracle inline (one `spec_status.py oracle-lookup` run per gap's compact question carrying the decision, options, and recommendation, judged per the oracle consultation contract) for decisions the repository cannot answer instead
of any human, and exiting through the re-gate; each session SHALL be graded
on the member change sitting at `ready` lint-clean. After a successful
enrichment session the autopilot SHALL re-run the gate engine and let its
verdict decide: a pass SHALL continue the pipeline; a second rejection SHALL
park the member as `rejected` with a reason naming the failed enrichment and
the enrichment session id recorded. If every enrichment attempt fails or
its grade stays unmet, then the member SHALL park as `rejected` with the
failure appended to the reason and the session id recorded — unless the
member's worktree vanished, in which case the vanished-worktree resolution
applies. The autopilot SHALL NOT drive a second enrichment phase for the
same member in the same run.

#### Scenario: Enrichment pass continues the pipeline
- **GIVEN** a member whose gate exits 2 and, after the enrichment session,
  exits 0
- **WHEN** the autopilot drives it
- **THEN** exactly one enrichment session runs, the gate runs twice, and the
  pipeline continues into build

#### Scenario: Second rejection parks with the session id
- **GIVEN** a member whose gate exits 2 both before and after the enrichment
  session
- **WHEN** the autopilot drives it
- **THEN** the member parks as rejected with a reason naming the enrichment
  and the enrichment session id, and no second enrichment phase runs

#### Scenario: Exhausted enrichment budget parks rejected, not needs-human
- **WHEN** every enrichment attempt of the gate entry's budget errors or
  leaves its grade unmet while the worktree still exists
- **THEN** the member parks as rejected with the failure in the reason and
  the session id recorded

### Requirement: Oracle-aware driven sessions
id: oracle-aware-driven-sessions
base: 4efda61971ea

The canned resume reply the autopilot sends to every driven session SHALL
direct the session to shape any undecided point into a compact question
(decision, options, recommendation), consult the oracle by running `spec_status.py oracle-lookup`, named by its absolute path, and judging its output per the oracle consultation contract, adopt an `ANSWER` verdict, and fall back to its own
recommendation on `INSUFFICIENT` or an unavailable oracle — never waiting
for a human. The build stage prompt SHALL direct the coordinator to route
sub-agent `QUESTION:` escalations that the spec artifacts and code cannot
answer through the same oracle before answering on its own authority.

#### Scenario: Canned reply names the oracle rung
- **WHEN** the autopilot's canned resume reply is inspected
- **THEN** it directs compact-question consultation through `oracle-lookup`,
  adopting `ANSWER` and self-recommending on `INSUFFICIENT`

#### Scenario: Build prompt routes QUESTION escalations
- **WHEN** the build stage prompt is rendered
- **THEN** it directs consulting `oracle-lookup` for sub-agent `QUESTION:`
  escalations the artifacts and code cannot answer

### Requirement: Detached pre-build drift step
id: detached-pre-build-drift
base: 355e6a134a2a

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
every `**Answered by:** USER` answer and epic Decision, the `oracle-lookup` verb for un-inferrable decisions, that no human is present, and the
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
- **THEN** one `replan` session ran with a prompt naming the reason, `oracle-lookup`, `USER`, and `spec_gate.py --base origin/main`, the gate ran
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

### Requirement: Unattended stage instructions
id: in-session-unattended-prompts
base: 76000f825fac

The in-session drive's plan-stage instruction and its re-plan instruction
SHALL each end with a paragraph stating that no human is available during
the run, that a decision the repository cannot settle is put to the oracle
(run `spec_status.py oracle-lookup` for one compact question and judge it per the oracle consultation contract), that on `INSUFFICIENT`
the recommended default is adopted and recorded in the plan's ledger, and
that no question round and no AskUserQuestion is opened. The re-plan
instruction SHALL additionally name the `/s:drift` verdict's `revise:`
pointer and reason, require the revision to stay within the plan's `USER`
ledger entries and the epic's Decisions, and end with `spec_gate.py <member>
--base origin/main`.

#### Scenario: The plan instruction states the absence of a human
- **WHEN** the drive spawns a plan-stage sub-agent
- **THEN** its instruction states that no human is available and names the
  oracle-then-default rule

#### Scenario: The re-plan instruction carries the verdict and the re-gate
- **GIVEN** a `revise` verdict whose `revise:` names tasks 2.1 and 2.2
- **WHEN** the drive spawns the re-plan sub-agent
- **THEN** its instruction names that pointer and reason, forbids a question
  round, and ends with the `--base origin/main` re-gate
