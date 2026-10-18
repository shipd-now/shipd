## MODIFIED Requirements

### Requirement: Symbolic model-tier resolution
id: stage-model-resolution
base: 3ea368e1c224
Dropped: Below-tiers step down from the ladder top by default
Dropped: Anchored stepping clamps at the ladder bottom
Dropped: A declared ladder replaces the default
Dropped: An off-ladder anchor falls back to itself
Dropped: The dry run prints the ladder and the anchor

The engine SHALL export, stdlib-only in `spec_common`, `EFFORT_LEVELS` —
exactly `high`, `medium`, `low` — and a `STAGE_EFFORT` map giving every
pipeline stage a default level: the planning stages (`plan`, `enrich`,
`replan`, `epic`) `high`, the implementation and judgement stages (`build`,
`review`) `medium`, and every other stage `low`. It SHALL export a pure
`resolve_effort(stage, declared=None)` resolving to the level a stage runs at:
`declared` when it names `session` or an effort level, `declared` verbatim when
it is a concrete model id, else the stage's default level.

The session driver's runners SHALL express a resolved level through the
harness's own knob: the `claude` runner SHALL render `--effort <level>`, the
`opencode` runner SHALL render `--model <base>#<level>` using the optional
config `model` base and SHALL render no model or effort flag when no base is
declared, and both SHALL render a concrete model id as `--model <id>`.
`session` SHALL render no model or effort flag, so the harness's own default
decides.

When a driven stage's resolved pipeline entry declares `model`, the autopilot
SHALL use that value; otherwise it SHALL use the stage's default level. The
autopilot SHALL accept a `--session-model` control naming the model `session`
inherits, SHALL print each stage's resolved level and the acting anchor in its
dry run, and SHALL record both in the run report.

#### Scenario: Session tier inherits the CLI default
- **GIVEN** a plan entry declaring `"model": "session"` and no anchor
- **WHEN** the autopilot drives the plan stage
- **THEN** the driven session is launched without a `--model` or `--effort`
  flag

#### Scenario: Concrete ids pass through verbatim
- **WHEN** an entry declares `"model": "claude-fable-5"`
- **THEN** the driven session is launched with `--model claude-fable-5`

#### Scenario: A stage defaults to its effort level
- **WHEN** the pipeline's `plan`, `build`, and `gate` stages declare no `model`
- **THEN** their levels resolve to `high`, `medium`, and `low`

#### Scenario: An entry overrides its stage's level
- **WHEN** a `build` entry declares `"model": "high"`
- **THEN** its level resolves to `high` rather than the stage default

#### Scenario: The claude runner expresses a level as effort
- **WHEN** the `claude` runner renders the level `high`
- **THEN** its argv carries `--effort high` and no `--model`

#### Scenario: The opencode runner expresses a level as a model variant
- **WHEN** the `opencode` runner renders the level `medium` with the base
  `provider/model` declared
- **THEN** its argv carries `--model provider/model#medium`, and with no base
  declared it carries no model flag

#### Scenario: The dry run prints the stage levels
- **WHEN** the autopilot dry-runs a repository
- **THEN** its output names each stage's resolved level and the acting anchor,
  and the run report records them

### Requirement: Session turn result text
id: session-turn-result-text
base: c8e844619217

The session driver SHALL provide `run_turn_result(prompt, cwd, resume_id=None,
timeout, harness="claude", binary=None, effort=None, model_base=None,
plugin_dir=None, extra_args=None)` returning `(ok, failure, session_id,
result_text)` where `result_text` is the headless turn's result string as its
harness runner extracts it, or an empty string when the transcript carries no
result text; `run_turn` SHALL return the first three values unchanged for every
existing caller. `binary` SHALL default to the selected runner's own
executable, `effort` SHALL be the effort level or concrete model id the runner
expresses, and `model_base` SHALL be the base a harness that expresses a level
as a model variant appends it to. A helper `result_text_from_transcript(text)`
SHALL expose the Claude transcript's extraction.

#### Scenario: The result text is returned
- **GIVEN** a binary that prints `{"session_id": "s1", "result":
  "{\"mode\": \"change\"}"}` and exits 0
- **WHEN** `run_turn_result` runs with the default harness
- **THEN** it returns `ok` true, session id `s1`, and the inner object text,
  while `run_turn` on the same binary returns `(True, None, "s1")`

#### Scenario: A non-JSON transcript yields an empty text
- **WHEN** `result_text_from_transcript("not json")` is called
- **THEN** it returns an empty string
