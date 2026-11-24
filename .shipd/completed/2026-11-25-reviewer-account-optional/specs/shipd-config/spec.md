## ADDED Requirements

### Requirement: The distinct_reviewer config key
id: distinct-reviewer-key

The configuration MAY declare `distinct_reviewer`: `true` or `false`,
resolved through the standard layered per-key merge. When `true`, a room
reviewer SHALL act from a GitHub account other than the pull request
author's; when `false` or undeclared, a reviewer MAY share the author's
account. `distinct_reviewer` SHALL be a member of
`spec_common.RECOGNIZED_CONFIG_KEYS`, SHALL carry a row in
`config_registry.py` with scope `repo`, so `config-set` accepts it, SHALL be documented as a
`// distinct_reviewer` entry in the copyable config example, and SHALL carry
a row in the `docs/customise.md` key table. The engine SHALL expose the
resolved value through a stdlib-only `resolve_distinct_reviewer(root)`
accessor in `spec_common` returning `False` when no layer declares the key.
If the declared value is not `true` or `false`, then the accessor SHALL raise
`ConfigError` naming `distinct_reviewer`, the offending value and the config
file that supplied it.

#### Scenario: The key defaults to false
- **WHEN** `resolve_distinct_reviewer` runs in a repository whose
  configuration declares no `distinct_reviewer`
- **THEN** it returns `False`

#### Scenario: A workspace root governs its members
- **WHEN** a workspace root's `.shipd-config.json` declares
  `"distinct_reviewer": true` and a member repository beneath it declares
  nothing
- **THEN** `resolve_distinct_reviewer` run from the member returns `True`

#### Scenario: A bad value names the key and the file
- **WHEN** a config file declares `"distinct_reviewer": "yes"`
- **THEN** the accessor raises `ConfigError` whose message names
  `distinct_reviewer`, the value `'yes'` and that config file

#### Scenario: The key is settable and documented
- **WHEN** `spec_status.py config-set distinct_reviewer true` runs in a
  repository, and `docs/customise.md` and the copyable config example are read
- **THEN** the verb exits `0` and writes the key to the repository's config
  file, `docs/customise.md` carries a `distinct_reviewer` row, and the example
  holds a `// distinct_reviewer` entry

#### Scenario: Config-set refuses a non-boolean
- **WHEN** `spec_status.py config-set distinct_reviewer maybe` runs
- **THEN** it exits `1` with an error naming `distinct_reviewer` and the hint
  `true or false`, and writes nothing
