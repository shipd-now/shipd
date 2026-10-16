## ADDED Requirements

### Requirement: PR configuration key
id: pr-config-key

The configuration MAY declare `pr`: a JSON object whose recognized members are `title` (a string template using only the placeholders `{ticket}`, `{summary}`, and `{change}` and containing `{summary}`; default `{summary}`) and `ticket_pattern` (a string holding a compilable regular expression; default unset), resolved through the standard layered per-key merge. `pr` SHALL be a member of `spec_common.RECOGNIZED_CONFIG_KEYS`, SHALL be documented as a `// pr` entry in the copyable config example, SHALL carry a row in the `docs/customise.md` key table, and SHALL be documented in the content directory's `README.md`. The engine SHALL expose the resolved value through a stdlib-only `resolve_pr(root)` accessor in `spec_common` returning `(title, ticket_pattern)` with `ticket_pattern` `None` when undeclared. If the declared value is not an object, or a member is present with the wrong shape, then the accessor SHALL raise `ConfigError` naming `pr`, the member, and the config file that supplied it. Members other than `title` and `ticket_pattern` SHALL be ignored. The `pr-mode` key SHALL be unchanged.

#### Scenario: Undeclared key yields the defaults
- **WHEN** `resolve_pr` runs from a repo whose layers declare no `pr`
- **THEN** it returns `("{summary}", None)`

#### Scenario: Workspace declaration governs a member repo
- **GIVEN** a workspace root declaring `"pr": {"title": "{ticket} {summary}", "ticket_pattern": "[A-Z]+-[0-9]+"}` and a member repo declaring no `pr`
- **WHEN** `resolve_pr` runs from the member repo
- **THEN** it returns that title and pattern

#### Scenario: Bad member is an error naming the file
- **WHEN** a layer declares `"pr": {"title": "{ticket}"}`, `"pr": {"title": "{oops} {summary}"}`, or `"pr": {"ticket_pattern": "("}`
- **THEN** `resolve_pr` raises `ConfigError` naming `pr`, the member, and that layer's config path

#### Scenario: Example and guide stay in step with the registry
- **WHEN** the config-sample and customise-guide drift guards run
- **THEN** both pass with `pr` documented in the example and present in the guide's key table
