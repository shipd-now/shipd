## MODIFIED Requirements

### Requirement: Deterministic context checks
id: context-sufficiency-checks
base: 267180affb56

The gate SHALL run the linter's structural change checks plus exactly these
context checks, all deterministic and repository-local: (1) every `base:`
hash on a MODIFIED or REMOVED delta entry SHALL equal the current master
requirement's content hash — a mismatch is a stale-context finding; (2) the
markers `TBD`, `TODO`, `FIXME`, `XXX`, `???`, and `OPEN QUESTION`
(case-insensitive, word-bounded) SHALL be findings wherever they appear in
`plan.md`, the delta specs, or `tasks.md`; (3) every backticked token in
`tasks.md` that contains a `/` and is shaped like a repository path SHALL
resolve to an existing file or directory, or have an existing parent or
grandparent directory — tolerating one new directory level, the
new-skill/new-test-tree case — and a token whose parent and grandparent
are both missing SHALL be a finding naming the token and both missing
levels; (4) every MODIFIED, REMOVED, or RENAMED delta operation SHALL
target a capability whose master spec exists, while ADDED-only new
capabilities pass. The gate SHALL NOT invoke a model or the network.

#### Scenario: Stale base hash is a finding
- **GIVEN** a delta whose `base:` no longer matches the master requirement
- **WHEN** the gate runs
- **THEN** the findings name the requirement id as stale context

#### Scenario: Placeholder marker is a finding
- **WHEN** a task reads "wire the config (TODO: decide key name)"
- **THEN** the findings name the placeholder and its file

#### Scenario: New file in an existing directory passes
- **WHEN** a task names a new file whose parent directory exists
- **THEN** no file-reference finding is produced for it

#### Scenario: New file one new directory deep passes
- **GIVEN** `plugins/s/skills/` exists and `plugins/s/skills/research/`
  does not
- **WHEN** a task names `plugins/s/skills/research/SKILL.md`
- **THEN** no file-reference finding is produced for it

#### Scenario: Deep dangling path is still a finding
- **WHEN** a task names `src/ghost/nested/missing.py` and neither
  `src/ghost/nested/` nor `src/ghost/` exists
- **THEN** the findings name the token and that both its parent and
  grandparent directories are missing

#### Scenario: Delta against a missing capability is a finding
- **WHEN** a delta carries `## MODIFIED Requirements` for a capability
  with no master spec
- **THEN** the findings name the capability
