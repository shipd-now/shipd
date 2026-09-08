## MODIFIED Requirements

### Requirement: Body template source
id: body-templates
base: b3f45edbf7c9

The plugin SHALL carry one body template per `/s:` command at
`plugins/s/harness/bodies/<command>.md`, whose ids exactly match the
skill directories under `plugins/s/skills/` — the directories carrying a
`SKILL.md`; a directory without one (shipped reference data, not a command)
is excluded from the match — plus a shared
`bodies/_preamble.md` partial. Every body template SHALL open with a
`<!-- description: <one line> -->` marker carrying the command's one-line
description. Templates SHALL express feature-conditional
content only through whole-line markers `<!-- if:<feature> -->`, optional
`<!-- else -->`, and `<!-- end -->` (non-nesting), MAY use
`<!-- include:preamble -->` and the `{refs}` placeholder, and every
`if:` gate name SHALL be a member of `harness_registry.FEATURES`. For each
command whose template carries at least one gated segment, a fallback
reference template SHALL exist at
`plugins/s/harness/references/<command>.md`.

#### Scenario: Every command has a template
- **WHEN** the bodies directory listing (ignoring `_`-prefixed partials) is
  compared to the `SKILL.md`-bearing directories under `plugins/s/skills/`
- **THEN** the two id sets are equal

#### Scenario: A skill-less directory needs no template
- **WHEN** a directory under `plugins/s/skills/` carries no `SKILL.md`
- **THEN** the template match ignores it and the guard still passes

#### Scenario: Gate names are vocabulary members
- **WHEN** the test suite scans every template's `if:` markers
- **THEN** every gate name is in `harness_registry.FEATURES`

#### Scenario: Gated commands carry fallback references
- **WHEN** a template contains at least one `if:` gate
- **THEN** `plugins/s/harness/references/<command>.md` exists

#### Scenario: Every template declares a description
- **WHEN** the test suite reads each template's first marker line
- **THEN** it is a `<!-- description: … -->` marker with non-empty text
