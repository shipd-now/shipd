# shipd-prd

### Requirement: PRD store layout and header grammar
id: prd-store-format

A PRD SHALL live at `<workspace-root>/<content-dir>/prds/<slug>/prd.md`, the
content directory resolved from the workspace root's configuration, with
engine path helpers (`prds_dir`, `prd_path`) constructing the path and a
`resolve_prd` helper resolving a slug across the workspace chain exactly as
initiative briefs resolve (the nearest chain member hosting the file wins;
no resolution yields none).

The document SHALL open with a `# <slug>` title matching its directory name,
SHALL carry a `Status:` line among its first five non-blank lines whose value
is one of `draft`, `approved`, or `superseded`, and SHALL carry a `Template:`
line among its first five non-blank lines whose value is one of the template
tiers — an absent or unknown `Template:` value is invalid rather than
defaulted. The only recognized header metadata key SHALL be `Initiative:`,
whose value MUST be a kebab-case slug that resolves to an existing initiative
brief across the workspace chain.

#### Scenario: Path helpers build the workspace store path
- **WHEN** the engine resolves a PRD named `mobile-push` under a workspace
  root with the default content directory
- **THEN** the resolved path is `<ws>/.shipd/prds/mobile-push/prd.md`

#### Scenario: Title must match the directory
- **WHEN** `prds/mobile-push/prd.md` opens with `# push-notifications`
- **THEN** validation reports a title mismatch error

#### Scenario: Unknown status is an error
- **WHEN** a PRD carries `Status: shipped`
- **THEN** validation reports the value and the accepted vocabulary

#### Scenario: Missing Template line is an error
- **WHEN** a PRD carries no `Template:` line in its first five non-blank
  lines
- **THEN** validation reports the missing line rather than assuming a
  default tier

#### Scenario: Unresolvable Initiative is an error
- **WHEN** a PRD carries `Initiative: no-such-goal` and no chain member
  hosts `initiatives/no-such-goal/brief.md`
- **THEN** validation reports that the initiative does not resolve

#### Scenario: Unrecognized metadata key is an error
- **WHEN** a PRD header carries `Project: something`
- **THEN** validation reports the unrecognized key and the recognized set

### Requirement: PRD template tier registry
id: prd-tier-registry

The engine SHALL define the template tiers `basic`, `standard`, and
`comprehensive` and an engine-side registry mapping each tier to its complete
required level-2 section list, additively nested: `basic` requires
`## Problem`, `## Solution`, and `## Success criteria`; `standard` requires
`basic`'s sections plus `## Users`, `## Requirements`, and `## Non-goals`;
`comprehensive` requires `standard`'s sections plus `## Risks`, `## Rollout`,
and `## Open questions`. Validation SHALL require every section named by the
PRD's declared tier to be present as an exact level-2 heading line, and SHALL
allow additional sections beyond the tier's list.

#### Scenario: Tier lists nest additively
- **WHEN** the registry is read
- **THEN** every section required by `basic` is required by `standard`, and
  every section required by `standard` is required by `comprehensive`

#### Scenario: Missing tier section is an error
- **WHEN** a `standard` PRD carries no `## Non-goals` heading
- **THEN** validation reports the missing section

#### Scenario: Lower tier is not held to higher sections
- **WHEN** a `basic` PRD carries `## Problem`, `## Solution`, and
  `## Success criteria` but no `## Users`
- **THEN** validation reports no missing-section error

#### Scenario: Extra sections are allowed
- **WHEN** a `comprehensive` PRD carries all nine required sections plus a
  bespoke `## Pricing` section
- **THEN** validation reports no error for the extra section

### Requirement: Plugin-shipped PRD template files
id: prd-template-files

The plugin SHALL ship one PRD template per tier at
`plugins/s/skills/prd/references/<tier>.md` (`basic.md`, `standard.md`,
`comprehensive.md`). Each template SHALL open with a `# ` title placeholder
line, carry `Status: draft` and a `Template:` line naming its own tier, and
present exactly its tier's required sections from the engine registry as
level-2 headings in registry order — no missing sections and no extra
sections in the skeleton — each followed by guidance prose an authored PRD
replaces. A test suite SHALL guard the templates against registry drift:
heading equality per tier, the `Template:` line, the header shape, and the
absence of unexpected template files, and SHALL verify a PRD filled from a
template passes the engine's PRD validation.

#### Scenario: Templates exist per tier
- **WHEN** the plugin tree is inspected
- **THEN** `plugins/s/skills/prd/references/` holds exactly `basic.md`,
  `standard.md`, and `comprehensive.md`

#### Scenario: Skeleton headings equal the registry
- **WHEN** a template's level-2 headings are compared with its tier's
  registry tuple
- **THEN** they are equal in content and order

#### Scenario: Template names its own tier
- **WHEN** `standard.md` is read
- **THEN** its header carries `Template: standard` and `Status: draft`

#### Scenario: Registry drift fails the guard
- **WHEN** the registry and a template skeleton disagree on a section
- **THEN** the drift-guard test fails naming the tier

#### Scenario: A filled template lints clean
- **WHEN** a PRD is produced from the `basic` template by replacing the
  title placeholder and guidance prose
- **THEN** the engine's PRD validation reports no errors

### Requirement: PRD interview skill
id: prd-skill-contract

The plugin SHALL ship a `/s:prd` skill at `plugins/s/skills/prd/SKILL.md`
whose contract is the discover-phase interview: announce the running plugin
version first; refuse to proceed when no workspace is discoverable, pointing
at workspace initialization; investigate before asking (the engine's `search`
retrieval and the workspace surfaces, with nothing discoverable ever asked);
interview in multiple rounds, one template section at a time, against the
active tier's template file; default the tier to `standard` and announce any
mid-interview escalation or de-escalation; compose the PRD by filling the
tier's template; install only through the engine's staged `prd` emit verb and
read the installed PRD back through the engine; and end by pointing at
`/s:epic` (an epic born from the PRD carrying `PRD: <slug>`) without invoking
it. The skill SHALL keep `plugins/s/skills/prd/references/` holding exactly
the three tier templates.

The plugin SHALL ship the matching harness command body at
`plugins/s/harness/bodies/prd.md` with a description marker, feature gates
drawn only from the registry vocabulary, and — since the body carries gated
segments — a fallback reference at `plugins/s/harness/references/prd.md`
condensing the PRD shape and the emit-install rule.

#### Scenario: Skill file exists with the interview contract
- **WHEN** `plugins/s/skills/prd/SKILL.md` is read
- **THEN** it carries `name: prd` frontmatter, the version announcement
  rule, the workspace preflight, the search-first investigation rule, the
  `standard` default with announced tier switches, the staged emit install,
  and the `/s:epic` handoff

#### Scenario: Bodies guard passes with the new command
- **WHEN** the harness bodies test suite runs
- **THEN** `prd` appears in both the SKILL.md-bearing skill directories and
  the body-template ids, and the 1:1 match holds

#### Scenario: Gated body carries its fallback reference
- **WHEN** `plugins/s/harness/bodies/prd.md` is scanned for `if:` gates
- **THEN** every gate name is in the registry vocabulary and
  `plugins/s/harness/references/prd.md` exists

#### Scenario: Templates directory stays templates-only
- **WHEN** the templates drift guard runs with the skill installed
- **THEN** `plugins/s/skills/prd/references/` still holds exactly
  `basic.md`, `standard.md`, and `comprehensive.md`

#### Scenario: Skill roster names the command
- **WHEN** `AGENTS.md`'s skill enumeration is read
- **THEN** it names `/s:prd` among the `/s:` commands
