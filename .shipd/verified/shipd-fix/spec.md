# shipd-fix

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
skills id sets stay equal; `docs/cheatsheet.md`'s command table and the `AGENTS.md`
skill enumeration SHALL list `/s:fix`; and
`plugins/s/.claude-plugin/plugin.json` SHALL declare version `0.6.148` or later so the
plugin cache snapshot refreshes.

#### Scenario: Body and skill ids stay equal
- **WHEN** the harness test suites under `plugins/s/skills/build/tests/` run
- **THEN** the bodies/skills id-set equality test passes with `fix` present
  in both sets

#### Scenario: The listings name the skill
- **WHEN** `docs/cheatsheet.md` and `AGENTS.md` are read
- **THEN** each lists `/s:fix` among the plugin's commands

#### Scenario: The snapshot version advances
- **WHEN** `plugins/s/.claude-plugin/plugin.json` is read
- **THEN** its `version` is `0.6.148` or later

### Requirement: Fix user documentation
id: fix-user-docs

The repository SHALL provide `docs/fix.md`, a how-to page titled "Fix a bug"
that is the main page for `/s:fix`. The page SHALL follow the main-page
shape: the opening under the title saying what the feature is, then the exact
level-2 headings `## When to use it`, `## How to run it`, and `## Reference`,
in that order. It SHALL explain that the skill retrieves the related
spec artifacts with the engine's `related` verb before it reads code, and
that it reproduces the problem before it changes anything. It SHALL state the
two outcomes: where the code is wrong, the skill fixes the code and adds a
regression test; where the documented behaviour is wrong, the skill changes
nothing and hands off to `/s:plan`. It SHALL state that the skill never edits
a spec artifact and never commits, pushes, or opens a pull request. It SHALL
list the parts of the closing report. The page SHALL carry no diagram, and
every relative link in it SHALL resolve. The page SHALL conform to the shipd
documentation standard: `<!-- doc-type: how-to -->` as its first line and a
total line count within the how-to cap.

#### Scenario: Page follows the main-page shape
- **WHEN** `docs/fix.md` is inspected
- **THEN** its level-2 headings are exactly `## When to use it`,
  `## How to run it`, and `## Reference`, in that order

#### Scenario: Page states both outcomes and the boundaries
- **WHEN** `docs/fix.md` is inspected
- **THEN** it names the `related` verb, the reproduce-first step, the
  code-wrong and spec-wrong outcomes with the `/s:plan` hand-off, and states
  that the skill never edits a spec and never ships

#### Scenario: Page carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over `docs/fix.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer,
  and the file holds no `mermaid` fence
