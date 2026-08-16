# shipd-doctor

### Requirement: Doctor skill flow
id: doctor-skill-flow

A `/s:doctor` skill SHALL run the read-only `shipd doctor` preflight —
resolving the binary as `shipd` on PATH first, else
`${CLAUDE_PLUGIN_ROOT}/bin/shipd` — and parse its spec'd
`ok|warn|fail <check> — <detail>` lines. When every check is `ok`, the
skill SHALL report the healthy result and stop. Otherwise it SHALL present
the findings and propose one remedy per remediable finding, obtain explicit
consent through a single batched selection honoring the dialog-prose
separation rule, run only the consented remedies, re-run `shipd doctor`,
and report the before/after states. Where the doctor output is absent or
unparseable, the skill SHALL report that as its own failure rather than
proceeding. The skill SHALL run at most one remedy round per invocation.

#### Scenario: Healthy environment stops after diagnosis
- **WHEN** `/s:doctor` runs and every check reports `ok`
- **THEN** the skill reports the healthy result and runs no remedy and no
  consent dialog

#### Scenario: Consent precedes every remedy
- **WHEN** findings exist and the user consents to a subset of the proposed
  remedies
- **THEN** only the consented remedies run, and the preflight is re-run and
  reported afterwards

#### Scenario: Declining runs nothing
- **WHEN** the user declines all remedies
- **THEN** the skill runs nothing and ends with the findings and their
  manual hints

### Requirement: Remedy safety boundaries
id: doctor-remedy-boundaries

The skill's remedy table SHALL be: a `textual` warning →
`python3 -m pip install "textual>=8.2.8,<9"` (the range mirrored from
`requirements.txt`); a stale `snapshot` warning →
`claude plugin update s@shipd` with the restart-to-apply note; a missing
`gh` or `git` → the platform-appropriate install command, stated before it
runs. An unauthenticated `gh` SHALL be handed to the user as
`! gh auth login` and never run by the skill; a failing `python` version
check and a failing `config` check SHALL be report-only — the skill SHALL
never install an interpreter and never edit a `.shipd-config.json`. The
`shipd doctor` CLI verb itself SHALL remain unmodified by this capability.

#### Scenario: Interactive auth is handed off
- **WHEN** the findings include an unauthenticated `gh`
- **THEN** the skill instructs the user to run `! gh auth login` and does
  not execute it

#### Scenario: Config failures are never auto-edited
- **WHEN** the findings include a `config` failure naming a malformed file
- **THEN** the skill reports the file and error with no edit performed and
  proposes no remedy command for it

### Requirement: Doctor skill registration
id: doctor-skill-registration

The skill SHALL live at `plugins/s/skills/doctor/SKILL.md` with `name` and
`description` frontmatter whose description carries the `/s:doctor` trigger,
SHALL carry the question-rejection recovery rule, and SHALL be listed in the
repository `README.md` skills table and in `AGENTS.md`'s skill enumeration.

#### Scenario: Skill is discoverable and documented
- **WHEN** the plugin's skills and the README table are compared
- **THEN** `doctor` appears in both, with `/s:doctor` as its invocation

#### Scenario: Recovery rule is carried
- **WHEN** `plugins/s/skills/doctor/SKILL.md` is inspected
- **THEN** it contains the question-rejection recovery rule
