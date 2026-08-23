## ADDED Requirements

### Requirement: Fix skill flow
id: fix-skill-flow

The plugin SHALL provide `plugins/s/skills/fix/SKILL.md` defining the
`/s:fix` debugging skill. The skill SHALL announce the running plugin
version, distill the user's problem description into search terms, and
retrieve the related artifacts through the engine's `related` verb before any
code investigation; SHALL read every retrieved artifact through the engine's
mediated `cat` verbs, never by constructing spec-tree paths; and SHALL
reproduce the reported problem where a runnable surface exists before
changing anything. When the diagnosis shows the code has drifted from the
documented behavior, or the bug is covered by no spec, the skill SHALL apply
the fix with a regression test per the host repository's testing conventions
and re-run the reproduction and the relevant tests. When the diagnosis shows
the documented behavior itself is wrong, the skill SHALL stop without editing
any spec artifact and hand off to `/s:plan` with its findings. The skill
SHALL end by reporting the diagnosis, the fix, and the verification evidence,
and SHALL NOT commit, branch, push, or open a pull request — shipping stays
with the user and the host repository's conventions. The skill SHALL never
write into the spec tree and never move a change's status.

#### Scenario: Retrieval precedes code diving
- **WHEN** `skills/fix/SKILL.md` is read
- **THEN** its flow orders the `related` retrieval and the mediated `cat`
  reads before code investigation, and reproduction before any edit

#### Scenario: A wrong spec routes to plan
- **WHEN** the skill's diagnosis concludes the documented behavior itself is
  wrong
- **THEN** `SKILL.md` directs stopping without editing any spec artifact,
  reporting the findings, and handing off to `/s:plan`

#### Scenario: The skill stops before shipping
- **WHEN** a fix has been applied and verified
- **THEN** `SKILL.md` directs reporting diagnosis, fix, and verification
  evidence, and forbids committing, branching, pushing, or opening a PR

### Requirement: Fix skill registration
id: fix-skill-registration

The plugin SHALL register `/s:fix` like its sibling commands:
`plugins/s/harness/bodies/fix.md` SHALL exist as the distilled command body,
opening with a `<!-- description: -->` marker, so the harness bodies and
skills id sets stay equal; the `README.md` skills table and the `AGENTS.md`
skill enumeration SHALL list `/s:fix`; and
`plugins/s/.claude-plugin/plugin.json` SHALL declare version `0.6.148` so the
plugin cache snapshot refreshes.

#### Scenario: Body and skill ids stay equal
- **WHEN** the harness test suites under `plugins/s/skills/build/tests/` run
- **THEN** the bodies/skills id-set equality test passes with `fix` present
  in both sets

#### Scenario: The listings name the skill
- **WHEN** `README.md` and `AGENTS.md` are read
- **THEN** each lists `/s:fix` among the plugin's commands

#### Scenario: The snapshot version advances
- **WHEN** `plugins/s/.claude-plugin/plugin.json` is read
- **THEN** its `version` is `0.6.148`
