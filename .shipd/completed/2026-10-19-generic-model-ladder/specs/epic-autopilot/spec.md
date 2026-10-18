## MODIFIED Requirements

### Requirement: Symbolic model-tier resolution
id: stage-model-resolution
base: ac93ef8e6aeb

The engine SHALL export, stdlib-only in `spec_common`, a `DEFAULT_MODEL_LADDER`
constant ordered strongest-first (`fable`, `opus`, `sonnet`, `haiku`) and a pure
`resolve_model_ladder(config=None)` function returning the `models` list a
configuration declares, else `DEFAULT_MODEL_LADDER`. It SHALL export a pure
`resolve_model_tier(tier, session_model=None, ladder=None)` function: `session`
SHALL resolve to `session_model` (a `None` result meaning "inherit the CLI
default"); `tier-below` and `tier-two-below` SHALL resolve to the ladder entry
one or two positions below the anchor, clamped at the ladder bottom, where the
anchor is `session_model` when it sits on the ladder, the ladder's top entry
when `session_model` is `None`, and `session_model` itself when a named anchor
does not sit on the ladder (an empty ladder included); `ladder=None` SHALL use
`DEFAULT_MODEL_LADDER`; any other non-empty string SHALL be returned verbatim as
a concrete model id. When a driven stage's resolved pipeline entry declares
`model`, the autopilot SHALL launch that stage's headless sessions with
`--model <resolved value>`; where the resolution yields `None`, it SHALL pass no
`--model` flag. The autopilot SHALL resolve the ladder once per run from the
run's configuration and thread it through every resolution, SHALL accept a
`--session-model` control naming the anchor, SHALL print the acting anchor and
the resolved ladder in its dry run, and SHALL record both in the run report.

#### Scenario: Session tier inherits the CLI default
- **GIVEN** a plan entry declaring `"model": "session"` and no anchor
- **WHEN** the autopilot drives the plan stage
- **THEN** the driven session is launched without a `--model` flag

#### Scenario: Below-tiers step down from the ladder top by default
- **WHEN** `tier-below` and `tier-two-below` resolve with no anchor and no
  declared ladder
- **THEN** they resolve to `opus` and `sonnet` respectively

#### Scenario: Anchored stepping clamps at the ladder bottom
- **GIVEN** `--session-model sonnet` and no declared ladder
- **WHEN** `tier-below` and `tier-two-below` resolve
- **THEN** both resolve to `haiku`

#### Scenario: Concrete ids pass through verbatim
- **WHEN** an entry declares `"model": "claude-fable-5"`
- **THEN** the driven session is launched with `--model claude-fable-5`

#### Scenario: A declared ladder replaces the default
- **WHEN** a configuration declares `models` as `["big", "mid", "small"]`
- **THEN** `resolve_model_ladder` returns that list, and `tier-below` with the
  anchor `big` resolves to `mid`

#### Scenario: An off-ladder anchor falls back to itself
- **WHEN** `tier-below` resolves against a declared ladder and an anchor that is
  not on it
- **THEN** it resolves to that anchor

#### Scenario: The dry run prints the ladder and the anchor
- **WHEN** the autopilot dry-runs a repository whose configuration declares
  `models`
- **THEN** its output names the resolved ladder and the acting anchor, and the
  run report carries both
