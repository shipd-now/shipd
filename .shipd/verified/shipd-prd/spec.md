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

### Requirement: PRD user documentation
id: prd-user-docs

The repository SHALL provide the discover-phase guide as two documents, each
conforming to the shipd documentation standard: a doc-type marker comment on
the first line and a total line count within that type's cap.

`docs/prd.md` SHALL be the concept hub (marker `concept`), covering: the PRD
concept and the Initiative → PRD → Epic → Change hierarchy with every link
optional (a mermaid diagram included) and references written upward;
workspace storage at the resolved `prds/<slug>/prd.md` path with
workspace-chain resolution, the no-workspace refusal, and the PRD's
standalone nature; an overview of the `draft`/`approved`/`superseded`
lifecycle with approval as a staged re-install, never a hand edit of the
store; an overview of the three template tiers with `standard` as the
default; the `/s:prd` interview as the authoring path; and a relative link
to `docs/prd-reference.md`.

`docs/prd-reference.md` SHALL be the reference (marker `reference`), opening
with a link back to the hub and covering: the header format with its
recognized keys (`Status:`, `Template:`, `Initiative:` as the only optional
key); the three-status vocabulary; the staged re-install approval mechanics
with `shipd lint --prd` as the validation check; the three template tiers
with their exact section lists, their additive nesting, and the
floor-not-ceiling rule; `shipd search` as the retrieval surface with an
example; `shipd prd` as the inspection surface — the slugged report with its
`cited-by` epics and the bare roster — including composing the report's path
with `shipd render`; and the epic header's `PRD:` link with its
workspace-resolution lint rule.

Every interactive command in either guide SHALL invoke the `shipd` binary or
name a `/s:` skill — never an engine script path.

#### Scenario: Concept hub covers the discover phase
- **WHEN** `docs/prd.md` is inspected
- **THEN** it holds the hierarchy mermaid diagram, the workspace storage path
  and chain-resolution rule, the standalone nature, the lifecycle and tier
  overviews, the `/s:prd` authoring path, and a resolving relative link to
  `docs/prd-reference.md`

#### Scenario: Reference covers the formats and surfaces
- **WHEN** `docs/prd-reference.md` is inspected
- **THEN** it documents the header keys, the three statuses with staged
  re-install approval, the three tiers' exact section lists with the
  `standard` default, a `shipd search` example, `shipd prd <slug>` (the
  report with citing epics) and bare `shipd prd` (the roster), and names
  `shipd render` composition

#### Scenario: Commands stay binary-or-skill
- **WHEN** both guides' command invocations are scanned
- **THEN** none names a `spec_status.py` or `spec_emit.py` path

#### Scenario: Standalone nature is stated
- **WHEN** the hub's storage prose is read
- **THEN** it states that a PRD needs no initiative and no epic, and that
  epics cite the PRD rather than the reverse

#### Scenario: Both guides carry their markers and fit their caps
- **WHEN** `docs_lint.py` runs over `docs/prd.md` and `docs/prd-reference.md`
- **THEN** it exits 0, with `docs/prd.md` marked `concept` and
  `docs/prd-reference.md` marked `reference`

### Requirement: PRD show verb
id: prd-show-verb

The status CLI SHALL provide `prd-show [slug]`. With a slug it SHALL print
the PRD's report: the slug and status, the `Template:` tier, the
`Initiative:` link when the header carries one, the resolved path (relative
to the invocation root when inside it, absolute otherwise, the nearest
workspace-chain member winning), and one `cited-by:` line per epic in the
invocation root's universe (the root and its worktrees, deduped root-first)
whose header carries `PRD: <slug>` — with an explicit `cited-by: none` line
when no epic cites it. An unknown slug SHALL exit non-zero naming the
expected `prd.md` path, and no discoverable workspace SHALL exit non-zero
with the no-workspace error. Bare `prd-show` SHALL list every PRD across the
workspace chain — one `<slug>: <status> (<tier>)` line per slug, the nearest
chain member winning, sorted by slug — reporting an empty store rather than
erroring when the chain holds none. Both forms SHALL accept `--json`
emitting the same facts as one JSON document. The verb is read-only.

#### Scenario: Report prints the PRD's facts and citing epics
- **WHEN** `prd-show mobile-push` runs where a chain member hosts the PRD
  and a universe epic carries `PRD: mobile-push`
- **THEN** the report holds the status, `Template:` tier, resolved path,
  and a `cited-by:` line naming that epic and its status

#### Scenario: Uncited PRD says so
- **WHEN** `prd-show mobile-push` runs and no epic carries `PRD: mobile-push`
- **THEN** the report holds `cited-by: none`

#### Scenario: Unknown slug is an error
- **WHEN** `prd-show no-such-prd` runs in a workspace with no such PRD
- **THEN** the CLI exits non-zero naming the expected `prd.md` path

#### Scenario: Bare form lists the roster with chain shadowing
- **WHEN** `prd-show` runs where an inner chain member shadows an outer
  member's copy of the same slug
- **THEN** one line prints per slug, the shadowed slug showing the inner
  copy's status and tier

#### Scenario: Empty store lists nothing without erroring
- **WHEN** `prd-show` runs in a workspace whose chain holds no PRDs
- **THEN** the CLI reports the empty store and exits zero

#### Scenario: JSON mode carries both forms
- **WHEN** `prd-show mobile-push --json` and `prd-show --json` run
- **THEN** the first emits one object with `slug`, `status`, `template`,
  `initiative`, `path`, and `cited_by`, and the second emits one array of
  `{slug, status, template}` objects
