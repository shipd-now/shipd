## ADDED Requirements

### Requirement: Merge configuration key
id: merge-config-key

The configuration MAY declare `merge`: a JSON object whose members are
`approvals` (integer 0 to 10, default 2), `dismiss_stale` (boolean, default
true), `last_push_approval` (boolean, default true), `required_checks` (list
of distinct non-empty strings, default `["ci", "semantic-review"]`),
`thread_resolution` (boolean, default true), and `strict` (boolean, default
false), resolved through the standard layered per-key merge. `merge` SHALL be
a member of `spec_common.RECOGNIZED_CONFIG_KEYS`, SHALL be documented as a
`// merge` entry in the copyable config example, and SHALL carry a row in the
`docs/customise.md` key table. The engine SHALL expose the resolved value
through a stdlib-only `resolve_merge(root)` accessor in `spec_common`
returning a dict of all six members, each defaulted when absent. If the
declared value is not an object, a member has the wrong type or range, or the
object carries a member other than the six, then the accessor SHALL raise
`ConfigError` naming `merge`, the member, and the config file that supplied
it.

#### Scenario: Undeclared key yields the defaults
- **WHEN** `resolve_merge` runs from a repo whose layers declare no `merge`
- **THEN** it returns approvals 2, dismiss_stale true, last_push_approval
  true, required_checks `["ci", "semantic-review"]`, thread_resolution true,
  and strict false

#### Scenario: Partial declaration keeps the other defaults
- **WHEN** a layer declares `"merge": {"approvals": 1}`
- **THEN** `resolve_merge` returns approvals 1 and every other member at its
  default

#### Scenario: Bad member is an error naming the file
- **WHEN** a layer declares `"merge": {"approvals": true}`, or `{"approvls": 2}`
- **THEN** `resolve_merge` raises `ConfigError` whose message names `merge`,
  the member, and that layer's config path

#### Scenario: Example and guide stay in step with the registry
- **WHEN** the config-sample and customise-guide drift guards run
- **THEN** both pass with `merge` documented in the example and the guide
