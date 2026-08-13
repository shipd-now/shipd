## ADDED Requirements

### Requirement: Autonomous-pipeline config key
id: autonomous-pipeline-key

The resolved configuration MAY carry an `autonomous-pipeline` key holding an
ordered JSON list that defines the delivery pipeline. Each entry SHALL be
exactly one of: `{"stage": "<name>"}` running a registry stage as built in;
`{"stage": "<name>", "skip": true}` explicitly skipping it;
`{"stage": "<name>", "tools": [...]}` binding additional tools to it;
`{"stage": "<name>", "replace": {...}}` substituting its implementation; or
`{"custom": "<kebab-name>", "command": "<command>"}` inserting a custom
step at that list position. A declared list SHALL be wholesale — stages
absent from it do not run, and such omission SHALL be valid, including for
gates (declaring the key is the required explicitness). When no layer
declares the key, the pipeline SHALL be the built-in default: every
registry stage in canonical order with no skips, replacements, or
bindings. The key SHALL merge nearest-wins-wholesale like every top-level
key.

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

### Requirement: Pipeline stage registry
id: pipeline-stage-registry

The engine SHALL define the pipeline stage registry as the ordered names
`research`, `epic`, `plan`, `gate`, `build`, `review` in a single data
definition that the resolver and every consumer import. Built-in stages
included in a declared pipeline SHALL preserve this canonical relative
order; `custom` entries MAY appear at any position.

#### Scenario: Canonical order is enforced for built-ins
- **WHEN** a declared pipeline lists `build` before `plan`
- **THEN** resolution fails with an error naming the misordered stages

#### Scenario: Custom steps go anywhere
- **WHEN** a `custom` entry sits between `build` and `review`
- **THEN** resolution succeeds with the custom step at that position

### Requirement: Pipeline entry validation
id: pipeline-entry-validation

`resolve_pipeline(root)` SHALL validate every entry against the closed
grammar and SHALL fail — naming the offending entry by index and content —
on: an unknown `stage` name; an entry matching none of the five forms;
`tools` or `replace` structures missing a `fallback` or carrying one other
than `builtin` or `skip`; a `replace` lacking both `command` and `tool`; a
`custom` entry whose name is not a kebab-case slug or whose `command` is
missing; or `skip` combined with `tools` or `replace`. On success it SHALL
return the ordered effective entries together with the provenance of the
key (the supplying config file path, or the default).

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
