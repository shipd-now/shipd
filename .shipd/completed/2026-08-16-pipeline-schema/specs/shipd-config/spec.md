## MODIFIED Requirements

### Requirement: Autonomous-pipeline config key
id: autonomous-pipeline-key
base: c146f4d503fa

The resolved configuration MAY carry an `autonomous-pipeline` key holding an
ordered JSON list that defines the delivery pipeline. Each entry SHALL be
exactly one of: `{"stage": "<name>"}` running a registry stage as built in;
`{"stage": "<name>", "skip": true}` explicitly skipping it;
`{"stage": "<name>", "tools": [...]}` binding additional tools to it;
`{"stage": "<name>", "replace": {...}}` substituting its implementation; or
`{"custom": "<kebab-name>", "command": "<command>"}` inserting a custom
step at that list position. A stage entry MAY additionally carry the typed
per-stage options defined by the pipeline stage options requirement, and
any stage or custom entry MAY carry an `autopilot` options object. A
declared list SHALL be wholesale — stages absent from it do not run, and
such omission SHALL be valid, including for gates (declaring the key is the
required explicitness). When no layer declares the key, the pipeline SHALL
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

### Requirement: Pipeline entry validation
id: pipeline-entry-validation
base: b280a4259bab

`resolve_pipeline(root)` SHALL validate every declared entry against
pydantic models defined in the engine's `pipeline_schema` module, imported
lazily and only when a layer declares the `autonomous-pipeline` key — the
no-key default resolution SHALL never import the module. If a pipeline is
declared and pydantic is not importable, then resolution SHALL fail with an
error naming pydantic, the supplying config file, and the
`pip install -r requirements.txt` remedy — never falling back to weaker
validation. Validation SHALL reject, naming the offending entry by index
and content and reporting every offending entry (not only the first): an
unknown `stage` name; an entry matching none of the declared forms; any
key not defined for its entry form (unknown keys are forbidden); `tools`
or `replace` structures missing a `fallback` or carrying one other than
`builtin` or `skip`; a `replace` lacking both `command` and `tool`; a
`custom` entry whose name is not a kebab-case slug or whose `command` is
missing; `skip` combined with any other field beyond `stage`; and
option values outside their declared types and bounds. On success it SHALL
return the ordered effective entries as plain dicts carrying exactly the
keys each entry declared, together with the provenance of the key (the
supplying config file path, or the default), preserving the canonical
relative order check for built-in stages.

#### Scenario: Missing fallback is an error
- **WHEN** an entry binds `{"name": "mcp:sourcebot"}` with no `fallback`
- **THEN** resolution fails naming that entry and the missing fallback

#### Scenario: Unknown stage is an error
- **WHEN** an entry reads `{"stage": "deploy"}`
- **THEN** resolution fails naming `deploy` and the known registry names

#### Scenario: Valid bindings resolve with provenance
- **GIVEN** a repo-layer pipeline binding Sourcebot to `plan` with
  `"fallback": "builtin"`
- **WHEN** the pipeline is resolved
- **THEN** the effective entries carry the binding and the provenance
  names the repo's config file

#### Scenario: Unknown keys are rejected
- **WHEN** a declared entry reads `{"stage": "plan", "retries": 2}`
- **THEN** resolution fails naming entry 0 and the unknown `retries` key

#### Scenario: Declared pipeline without pydantic fails closed
- **GIVEN** pydantic is not importable
- **WHEN** a config layer declares any `autonomous-pipeline` list
- **THEN** resolution fails with an error naming pydantic and
  `pip install -r requirements.txt`, and no partial validation runs

#### Scenario: Default resolution needs no pydantic
- **GIVEN** pydantic is not importable
- **WHEN** no layer declares the key and the pipeline is resolved
- **THEN** the full default resolves successfully

## ADDED Requirements

### Requirement: Pipeline stage options
id: pipeline-stage-options

The pipeline entry schema SHALL define these typed options. Every stage
entry MAY carry `model`: a non-empty string that is either a symbolic tier
— `session`, `tier-below`, or `tier-two-below`, exported by the schema
module as the symbolic-tier constant — or a concrete model id (any other
non-empty string; the set of concrete ids is open). The `build` stage
additionally accepts `subagent_model` (same tier type), `validator`
(boolean, default true), `telemetry` (boolean, default true), and
`parallelism` (integer >= 1). The `review` stage additionally accepts
`disposition`: one of `all`, `high-only`, or `none`, default `all`. Any
stage or custom entry MAY carry `autopilot`: an object accepting
`attempts` (integer >= 1, default 3), `timeout` (integer > 0), and
`max_resumes` (integer >= 0), with unknown keys forbidden. Defaults SHALL
be schema-declared, not injected into resolved entries: a resolved entry
carries exactly the keys the user declared. If `skip` is true, then the
entry SHALL carry no other field beyond `stage` — options on a skipped
stage are an error.

#### Scenario: Build options are accepted and carried
- **WHEN** a declared pipeline carries `{"stage": "build",
  "validator": false, "telemetry": false, "parallelism": 2,
  "subagent_model": "tier-two-below"}`
- **THEN** the pipeline resolves and the effective entry carries exactly
  those declared keys and values

#### Scenario: Undeclared defaults are not injected
- **WHEN** a declared pipeline carries the bare entry `{"stage": "build"}`
- **THEN** the resolved entry is exactly `{"stage": "build"}` with no
  `validator`, `telemetry`, or other default keys added

#### Scenario: Disposition outside the closed set is rejected
- **WHEN** a declared review entry carries `"disposition": "medium-up"`
- **THEN** resolution fails naming the entry and the invalid value

#### Scenario: Autopilot options are bounded
- **WHEN** a declared entry carries `"autopilot": {"attempts": 0}`
- **THEN** resolution fails naming the entry and the out-of-range value

#### Scenario: Options on a skipped stage are an error
- **WHEN** a declared entry reads `{"stage": "review", "skip": true,
  "model": "tier-below"}`
- **THEN** resolution fails naming the entry and the skip exclusivity rule
