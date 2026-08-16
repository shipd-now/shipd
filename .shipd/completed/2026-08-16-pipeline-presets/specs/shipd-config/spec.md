## MODIFIED Requirements

### Requirement: Autonomous-pipeline config key
id: autonomous-pipeline-key
base: 5aaae0697259

The resolved configuration MAY carry an `autonomous-pipeline` key holding
either an ordered JSON list that defines the delivery pipeline or a string
naming a built-in preset. Each list entry SHALL be exactly one of:
`{"stage": "<name>"}` running a registry stage as built in;
`{"stage": "<name>", "skip": true}` explicitly skipping it;
`{"stage": "<name>", "tools": [...]}` binding additional tools to it;
`{"stage": "<name>", "replace": {...}}` substituting its implementation; or
`{"custom": "<kebab-name>", "command": "<command>"}` inserting a custom
step at that list position. A stage entry MAY additionally carry the typed
per-stage options defined by the pipeline stage options requirement, and
any stage or custom entry MAY carry an `autopilot` options object. A
declared list is wholesale — stages absent from it do not run, and
such omission SHALL be valid, including for gates (declaring the key is the
required explicitness). A string value SHALL resolve through the named
pipeline presets requirement; a preset name and an entry list SHALL never
combine — the key holds one or the other. If the key's value is neither a
list nor a string, then resolution SHALL fail with an error naming the key
and the accepted forms. When no layer declares the key, the pipeline SHALL
be the built-in default: every registry stage in canonical order with no
skips, replacements, or bindings — resolved without importing any
third-party package. The key SHALL merge nearest-wins-wholesale like every
top-level key.

#### Scenario: Declared pipeline is wholesale
- **GIVEN** a config layer declaring the key with only `plan`, `gate`, and
  `build` entries
- **WHEN** the pipeline is resolved
- **THEN** exactly those three stages are effective and the omission of
  `review` is not an error

#### Scenario: Absent key yields the full default
- **WHEN** no config layer declares `autonomous-pipeline`
- **THEN** the resolved pipeline is every registry stage in canonical
  order, unskipped and unbound

#### Scenario: Explicit gate skip is legal
- **WHEN** a declared pipeline carries `{"stage": "gate", "skip": true}`
- **THEN** the pipeline resolves with the gate skipped and no error

#### Scenario: Typed options ride a declared entry
- **WHEN** a declared pipeline carries
  `{"stage": "build", "validator": false, "subagent_model": "tier-below"}`
- **THEN** the pipeline resolves and the effective build entry carries
  exactly those declared option keys

#### Scenario: Non-list non-string value is rejected
- **WHEN** a config layer declares `"autonomous-pipeline": 7`
- **THEN** resolution fails with an error naming the key and stating the
  value must be a JSON list or a preset name string

## ADDED Requirements

### Requirement: Named pipeline presets
id: pipeline-presets

The engine SHALL define the preset names `default`, `eco`, and `basic` in a
stdlib names constant, with the preset entry table shipped as data in the
`pipeline_schema` module keyed by exactly those names. When the
`autonomous-pipeline` value is a string, resolution SHALL first check it
against the names constant — an unknown name SHALL fail naming the value,
the supplying config file, and the known preset names, without requiring
pydantic. The name `default` SHALL resolve to the same entries as the
absent key — every registry stage bare, in canonical order — without
importing any third-party package. Every other known name SHALL expand its
table entries through the same pydantic validation as a user-declared list,
including its fail-closed behavior when pydantic is not importable. The
provenance of a preset-resolved pipeline SHALL be
`preset:<name> (<supplying-config-path>)`. The `eco` preset SHALL be:
research and epic skipped, plan `model` `session`, gate
`autopilot.attempts` 1, build `validator` false with `subagent_model`
`tier-two-below` and `telemetry` false, review `model` `tier-below` with
`disposition` `high-only`. The `basic` preset SHALL be: research and epic
skipped, plan `model` `session`, gate skipped, build `validator` false with
`subagent_model` `tier-below`, review `model` `tier-below` with
`disposition` `high-only`. Every shipped preset SHALL keep the plan stage
on `session` and SHALL include an unskipped review stage.

#### Scenario: Eco is a one-line opt-in
- **GIVEN** a repo config declaring `{"autonomous-pipeline": "eco"}` and
  pydantic importable
- **WHEN** the pipeline is resolved
- **THEN** the effective entries are the eco table — research and epic
  skipped, plan on `session`, gate with `autopilot.attempts` 1, build with
  `validator` false, `subagent_model` `tier-two-below`, `telemetry` false,
  review with `model` `tier-below` and `disposition` `high-only` — and the
  provenance reads `preset:eco` plus the repo config path

#### Scenario: Default preset needs no pydantic
- **GIVEN** pydantic is not importable
- **WHEN** a config layer declares `{"autonomous-pipeline": "default"}`
- **THEN** resolution succeeds with every registry stage bare in canonical
  order and provenance `preset:default` plus the config path

#### Scenario: Unknown preset lists the known names
- **GIVEN** pydantic is not importable
- **WHEN** a config layer declares `{"autonomous-pipeline": "ecoo"}`
- **THEN** resolution fails naming `ecoo`, the supplying config file, and
  the known presets `basic`, `default`, and `eco` — not the pydantic
  install hint

#### Scenario: Non-default preset fails closed without pydantic
- **GIVEN** pydantic is not importable
- **WHEN** a config layer declares `{"autonomous-pipeline": "eco"}`
- **THEN** resolution fails with the error naming pydantic and
  `pip install -r requirements.txt`

#### Scenario: Preset table stays valid against the schema
- **WHEN** the pydantic-dependent test suite runs
- **THEN** every preset's entry list passes entry validation and the
  canonical-order check, and the table's keys equal the stdlib names
  constant
