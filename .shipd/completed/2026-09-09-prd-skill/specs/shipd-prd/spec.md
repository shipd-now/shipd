## ADDED Requirements

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
