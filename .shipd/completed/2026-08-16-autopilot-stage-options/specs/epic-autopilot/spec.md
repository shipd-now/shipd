## ADDED Requirements

### Requirement: Symbolic model-tier resolution
id: stage-model-resolution

The engine SHALL export, stdlib-only in `spec_common`, a `MODEL_LADDER`
constant ordered strongest-first (`fable`, `opus`, `sonnet`, `haiku`) and a
pure `resolve_model_tier(tier, session_model=None)` function: `session`
SHALL resolve to `session_model` (a `None` result meaning "inherit the CLI
default"); `tier-below` and `tier-two-below` SHALL resolve to the ladder
alias one or two positions below the anchor — the anchor being
`session_model` when it is a ladder alias, else the ladder top — clamped at
the ladder bottom; any other non-empty string SHALL be returned verbatim as
a concrete model id. When a driven stage's resolved pipeline entry declares
`model`, the autopilot SHALL launch that stage's headless sessions with
`--model <resolved value>`; where the resolution yields `None`, it SHALL
pass no `--model` flag. The autopilot SHALL accept a `--session-model`
control naming the anchor, SHALL print the acting anchor in its dry run,
and SHALL record it in the run report.

#### Scenario: Session tier inherits the CLI default
- **GIVEN** a plan entry declaring `"model": "session"` and no anchor
- **WHEN** the autopilot drives the plan stage
- **THEN** the driven session is launched without a `--model` flag

#### Scenario: Below-tiers step down from the ladder top by default
- **WHEN** `tier-below` and `tier-two-below` resolve with no anchor
- **THEN** they resolve to `opus` and `sonnet` respectively

#### Scenario: Anchored stepping clamps at the ladder bottom
- **GIVEN** `--session-model sonnet`
- **WHEN** `tier-below` and `tier-two-below` resolve
- **THEN** both resolve to `haiku`

#### Scenario: Concrete ids pass through verbatim
- **WHEN** an entry declares `"model": "claude-fable-5"`
- **THEN** the driven session is launched with `--model claude-fable-5`

### Requirement: Stage options conveyed in stage prompts
id: stage-options-in-prompts

When a resolved build entry declares `validator` false, `telemetry` false,
`parallelism`, or `subagent_model`, the build stage prompt SHALL convey each
declared option to the driven session — the validator phase skipped, the
telemetry reporting skipped, the sub-agent cap, and the sub-agent model as
the concrete value resolved against the build session's own model with its
symbolic form named alongside. When a resolved review entry declares
`disposition` or `model`, the review stage prompt SHALL append the matching
`--disposition` and `--model` options to its poster invocation and SHALL
match the disposition-loop instruction to the scope: `high-only` implements
high-severity findings and runs `review_gate.py autoreply` with that scope
on the rest before `resolve`; `none` posts, autoreplies every finding, and
resolves. An entry declaring none of these options SHALL produce the prompt
unchanged from the optionless behavior, and the review grade SHALL remain
the green `semantic-review` status plus `unresolved=0`. The dry run's entry
labels SHALL render each entry's declared options.

#### Scenario: Build options reach the build prompt
- **GIVEN** a build entry with `validator` false, `telemetry` false,
  `parallelism` 2, and `subagent_model` `tier-two-below`
- **WHEN** the build prompt is rendered
- **THEN** it directs skipping the validator phase and telemetry, caps
  sub-agents at 2, and names the resolved sub-agent model with its
  `tier-two-below` provenance

#### Scenario: Review scope reaches the poster and the loop
- **GIVEN** a review entry with `disposition` `high-only` and `model`
  `tier-below`
- **WHEN** the review prompt is rendered
- **THEN** its poster invocation carries `--disposition high-only` and
  `--model tier-below`, and the loop instruction directs implementing
  high-severity findings and `autoreply` on the rest before `resolve`

#### Scenario: Bare entries keep today's prompts
- **WHEN** the build and review prompts render for entries declaring no
  options
- **THEN** each prompt is unchanged from the optionless rendering

#### Scenario: Dry-run labels show declared options
- **GIVEN** a pipeline whose gate entry declares `autopilot.attempts` 1
- **WHEN** the dry run prints the resolved pipeline
- **THEN** the gate entry's label renders the declared option

### Requirement: Per-stage driver knobs
id: per-stage-driver-knobs

When a resolved stage or custom entry carries an `autopilot` block, the
autopilot SHALL use its `attempts` as that entry's fresh-attempt budget in
place of the fixed three — governing driven-session re-drives, replacement
and custom command retries, and, on the gate entry, both the gate-engine
retry loop and the enrichment-session loop — and SHALL use its `timeout`
and `max_resumes` for that stage's sessions in place of the run-global
values. If an entry carries no `autopilot` block or omits a key, then the
defaults SHALL apply: three attempts and the run-global timeout and
max-resumes.

#### Scenario: A one-attempt build parks on first failure
- **GIVEN** a build entry with `autopilot.attempts` 1 and a failing session
- **WHEN** the autopilot drives the member
- **THEN** exactly one build session runs before the member parks

#### Scenario: Gate attempts govern the enrichment loop
- **GIVEN** a gate entry with `autopilot.attempts` 1 and a gate that rejects
  before and after enrichment
- **WHEN** the autopilot drives the member
- **THEN** exactly one gate-engine call precedes enrichment, at most one
  enrichment session runs, and the member parks rejected

#### Scenario: Per-stage timeout overrides the run-global value
- **GIVEN** a plan entry whose `autopilot.timeout` differs from the run's
  `--timeout`
- **WHEN** the plan session is driven
- **THEN** the session receives the entry's timeout, and stages without an
  override receive the run-global value

### Requirement: In-session stage options
id: in-session-stage-options

Where a resolved entry declares `model`, the in-session drive SHALL spawn
that stage's sub-agent with the Agent tool's model parameter set to the tier
resolved relative to the current session (a concrete ladder alias passed
verbatim). The in-session drive's stage instructions SHALL mirror the
detached driver's prompts, conditional option lines included, and it SHALL
ignore `autopilot` blocks entirely — interactively the human is the retry
loop.

#### Scenario: A declared model reaches the Agent spawn
- **GIVEN** a resolved build entry declaring `model` `tier-below`
- **WHEN** the in-session drive spawns the build stage's sub-agent
- **THEN** the spawn's model parameter carries the tier resolved one step
  below the current session

#### Scenario: Autopilot blocks are ignored in-session
- **GIVEN** a resolved entry carrying `autopilot.attempts` 1
- **WHEN** the in-session drive runs that stage
- **THEN** no retry budget is enforced from it — a failed stage stops and
  asks the user exactly as before

## MODIFIED Requirements

### Requirement: Three-strike failure handling
id: three-strike-parking
base: fdb00d55d94e

When a driven stage fails for a non-gate reason — session error or timeout,
grade unmet after the resume budget, or a non-zero replacement or custom
command — the autopilot SHALL re-drive that stage with the failure summary
appended to the prompt, up to that entry's fresh-attempt budget: the entry's
`autopilot.attempts` when declared, else three. A stage still failing after
its final attempt SHALL park the member as `needs-human`, recording the
stage, the reason, and the most recent session id so a human can reopen the
exact conversation with `claude --resume <id>`; the member's worktree SHALL
be left intact and the run SHALL continue with the next member.

#### Scenario: Second attempt can succeed
- **GIVEN** a stage that fails once and succeeds on re-drive under the
  default budget
- **WHEN** the autopilot drives it
- **THEN** the member proceeds and no parking occurs

#### Scenario: Final failure parks with the session id
- **WHEN** a stage fails every attempt of its budget
- **THEN** the member is parked as needs-human with stage, reason, and
  session id, its worktree remains, and the next member starts

### Requirement: Oracle-backed gate enrichment
id: oracle-gate-enrichment
base: 636d66fae6a5

When the built-in gate stage rejects a member (exit 2), the autopilot SHALL
drive one oracle-backed enrichment phase before parking: headless enrichment
sessions retried on session failure or unmet grade up to the gate entry's
fresh-attempt budget (`autopilot.attempts`, default three), each session
using the gate entry's declared model, timeout, and max-resumes. The
session's prompt SHALL direct running `/s:plan <member>` — which locates the
rejected change and enters enrichment mode — resolving repository-answerable
findings by editing the artifacts, consulting the ask-mikk oracle (agent
`s:oracle`, one compact question carrying the decision, options, and
recommendation per gap) for decisions the repository cannot answer instead
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
