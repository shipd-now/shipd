## MODIFIED Requirements

### Requirement: In-session stage options
id: in-session-stage-options
base: df755762c8b7

The in-session drive SHALL obtain the resolved pipeline entries and each
entry's declared options by running the status CLI's `pipeline-show --json`
verb once per run, reading the validated entry dicts from the emitted
object's `entries` — never by parsing the dry run's rendered entry labels,
which are human-facing only. The dry run remains the sole source of the
member order. Where a resolved entry declares `model`, the in-session drive
SHALL spawn that stage's sub-agent with the Agent tool's model parameter
set to the tier resolved relative to the current session (a concrete ladder
alias passed verbatim). The in-session drive's stage instructions SHALL
mirror the detached driver's prompts, conditional option lines included,
and it SHALL ignore `autopilot` blocks entirely — interactively the human
is the retry loop.

#### Scenario: Options are read from the JSON entries
- **GIVEN** a resolved build entry declaring `subagent_model`
  `tier-two-below` and `validator` false
- **WHEN** the in-session drive prepares that member's build stage
- **THEN** the options come from the `pipeline-show --json` object's entry
  dicts, not from the dry run's rendered labels

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
