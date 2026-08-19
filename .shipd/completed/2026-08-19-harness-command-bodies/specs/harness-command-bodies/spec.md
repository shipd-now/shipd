## ADDED Requirements

### Requirement: Body template source
id: body-templates

The plugin SHALL carry one body template per `/s:` command at
`plugins/s/harness/bodies/<command>.md`, whose ids exactly match the
directory names under `plugins/s/skills/`, plus a shared
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
  compared to the `plugins/s/skills/` directory listing
- **THEN** the two id sets are equal

#### Scenario: Gate names are vocabulary members
- **WHEN** the test suite scans every template's `if:` markers
- **THEN** every gate name is in `harness_registry.FEATURES`

#### Scenario: Gated commands carry fallback references
- **WHEN** a template contains at least one `if:` gate
- **THEN** `plugins/s/harness/references/<command>.md` exists

#### Scenario: Every template declares a description
- **WHEN** the test suite reads each template's first marker line
- **THEN** it is a `<!-- description: … -->` marker with non-empty text

### Requirement: Feature-scaled rendering
id: body-render

The engine SHALL provide a stdlib-only module
`plugins/s/skills/build/scripts/harness_bodies.py` whose
`render(command, features, refs_dir=None)` returns the template with
includes resolved, marker lines stripped, each gated segment kept only when
its feature is declared (the `else` segment kept otherwise, when present),
and `{refs}` replaced by `refs_dir`. The module SHALL expose `commands()`
(sorted template ids), `reference(command)` (the fallback text or
`None`), and `description(command)` (the template's declared one-line
description); `render` SHALL strip the description marker from its output. If a kept segment contains `{refs}` while `refs_dir` is `None`, or
a template carries an unknown gate name, then `render` SHALL raise an
error naming the template. A body rendered with an empty feature set SHALL
contain no marker lines, no `{refs}`, and none of the tokens `subagent`,
`sub-agent`, or `AskUserQuestion`.

#### Scenario: Declared feature keeps its segment
- **WHEN** the build command's template is rendered with `subagents`
  declared and again with no features
- **THEN** the delegated-flow segment appears only in the first rendering,
  and the second carries that gate's `else` content instead

#### Scenario: Empty-feature render never names gated capabilities
- **WHEN** every command is rendered with an empty feature set and a
  `refs_dir`
- **THEN** no output contains `<!--`, `{refs}`, `subagent`, `sub-agent`, or
  `AskUserQuestion`

#### Scenario: Refs placeholder resolves or refuses
- **WHEN** a template whose kept segment carries `{refs}` is rendered with
  `refs_dir="X"` and again with `refs_dir=None`
- **THEN** the first output contains `X` where the placeholder stood and
  the second raises an error naming the template

#### Scenario: Fallback pointer is gated on file-references
- **WHEN** a command with a fallback reference is rendered with
  `file-references` declared and again without it
- **THEN** the first output points at its `{refs}`-addressed reference file
  and the second instead carries an inline degradation note

### Requirement: Distilled router content
id: body-content

Every body template SHALL be a distilled router for its command — a lean
imperative workflow driving the `shipd` CLI's read verbs and, for
lifecycle mutations, the engine scripts through the preamble's
snapshot-resolution snippet — and SHALL NOT reproduce its SKILL.md
verbatim. The shared preamble SHALL define the engine-scripts resolution
(newest plugin cache snapshot by dotted-version order). Each rendered body
(any feature set) SHALL stay under 120 lines.

#### Scenario: Preamble resolves the newest snapshot
- **WHEN** the preamble's resolution snippet runs in a shell against a fake
  cache root holding `0.6.9` and `0.6.10`
- **THEN** the resolved scripts path is under `0.6.10`

#### Scenario: Bodies stay lean
- **WHEN** every command is rendered with the full feature vocabulary
- **THEN** every rendered body is under 120 lines

#### Scenario: Bodies drive the CLI, not pasted skills
- **WHEN** the plan command's rendered body is inspected
- **THEN** it invokes `spec_emit.py` and `spec_gate.py` via the preamble's
  scripts variable and is not byte-identical to any portion of
  `plugins/s/skills/plan/SKILL.md` exceeding 10 consecutive lines
