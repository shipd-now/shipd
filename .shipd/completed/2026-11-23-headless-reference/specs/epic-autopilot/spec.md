# headless-reference — epic-autopilot delta

## MODIFIED Requirements

### Requirement: Oracle-aware driven sessions
id: oracle-aware-driven-sessions
base: 95f8fe376d26

Every prompt the autopilot sends to a driven session — the canned resume
reply, and the build, enrichment, and re-plan stage prompts — SHALL state that
no human is available and name the absolute path of the headless contract,
`skills/ask/references/headless.md`, as the one place the oracle-then-default
rule lives. Each SHALL also name the `spec_status.py oracle-lookup` command by
its absolute path, and SHALL NOT restate the contract's ledger labels. The
build stage prompt SHALL direct the coordinator to settle sub-agent
`QUESTION:` escalations that the spec artifacts and code cannot answer by the
same contract, never leaving the sub-agent blocked.

#### Scenario: Canned reply names the oracle rung
- **WHEN** the autopilot's canned resume reply is inspected
- **THEN** it states that no human is available, names the headless
  contract's path and the `oracle-lookup` command, and names no ledger label

#### Scenario: Build prompt routes QUESTION escalations
- **WHEN** the build stage prompt is rendered
- **THEN** it directs settling sub-agent `QUESTION:` escalations the
  artifacts and code cannot answer by the headless contract, and names the
  `oracle-lookup` command

### Requirement: Unattended stage instructions
id: in-session-unattended-prompts
base: f57419899362

The in-session drive's plan-stage instruction and its re-plan instruction
SHALL each end with a paragraph stating that no human is available during
the run and that every decision is settled per the headless contract in
`${CLAUDE_PLUGIN_ROOT}/skills/ask/references/headless.md`, which the paragraph
names by that path, with a clause forbidding a question round and
AskUserQuestion, and does not otherwise restate. The re-plan
instruction SHALL additionally name the `/s:drift` verdict's `revise:`
pointer and reason, require the revision to stay within the plan's `USER`
ledger entries and the epic's Decisions, and end with `spec_gate.py <member>
--base origin/main`.

#### Scenario: The plan instruction states the absence of a human
- **WHEN** the drive spawns a plan-stage sub-agent
- **THEN** its instruction states that no human is available and names the
  headless contract's path

#### Scenario: The re-plan instruction carries the verdict and the re-gate
- **GIVEN** a `revise` verdict whose `revise:` names tasks 2.1 and 2.2
- **WHEN** the drive spawns the re-plan sub-agent
- **THEN** its instruction names that pointer and reason, names the
  headless contract, and ends with the `--base origin/main` re-gate

### Requirement: Oracle-backed gate enrichment
id: oracle-gate-enrichment
base: cc65cc2784c7

When the built-in gate stage rejects a member (exit 2), the autopilot SHALL
drive one oracle-backed enrichment phase before parking: headless enrichment
sessions retried on session failure or unmet grade up to the gate entry's
fresh-attempt budget (`autopilot.attempts`, default three), each session
using the gate entry's declared model, timeout, and max-resumes. The
session's prompt SHALL direct running `/s:plan <member>` — which locates the
rejected change and enters enrichment mode — resolving repository-answerable
findings by editing the artifacts, settling the decisions the repository cannot answer by the headless contract
(`skills/ask/references/headless.md`, named by its absolute path) instead of
asking any human, and exiting through the re-gate; each session SHALL be graded
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
