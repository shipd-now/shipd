## ADDED Requirements

### Requirement: PR mode key
id: pr-mode-key

The configuration MAY declare `pr-mode`: a string, exactly `auto` or
`draft`, resolved through the standard layered per-key merge — so a
workspace root's `.shipd-config.json` declaring it governs every member
repo beneath it. When no layer declares the key, the effective mode SHALL
be `auto` (today's auto-merging behavior). The engine SHALL expose the
resolved mode through a stdlib-only `resolve_pr_mode(root)` accessor in
`spec_common`; if the declared value is anything other than `auto` or
`draft`, then the accessor and every consuming flow SHALL fail with an
error naming `pr-mode` and the accepted values. The mode governs
change-shipping PR flows only — the build ship phase and autopilot
members; metadata PRs (epic-close status derivations, initiative tagging)
SHALL be unaffected by it.

#### Scenario: Workspace declaration governs a member repo
- **GIVEN** a workspace root's `.shipd-config.json` declaring
  `"pr-mode": "draft"` and a member repo beneath it declaring no
  `pr-mode`
- **WHEN** the mode is resolved from the member repo
- **THEN** `resolve_pr_mode` returns `draft` and `config-show` lists the
  key with the workspace layer as its provenance

#### Scenario: Undeclared key defaults to auto
- **WHEN** no config layer declares `pr-mode`
- **THEN** `resolve_pr_mode` returns `auto`

#### Scenario: Invalid value errors naming the key
- **GIVEN** a layer declaring `"pr-mode": "always"`
- **WHEN** the mode is resolved
- **THEN** resolution fails with an error naming `pr-mode` and the
  accepted values `auto` and `draft`
