## ADDED Requirements

### Requirement: Harnesses user documentation
id: harness-user-docs

The repository SHALL provide `docs/harnesses.md`, titled "Harnesses", as the
main page for the `shipd harness` verb family. The page SHALL conform to the
shipd documentation standard with `<!-- doc-type: how-to -->` as its first
line and a total line count within the how-to cap.

The page SHALL follow the main-page shape: opening paragraphs saying what a
harness is, then `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order. It SHALL state:

- that a harness is a coding agent surface, and that the harness registry
  lets each registered harness drive the same `shipd` CLI from its own
  command palette;
- that one shared body per command is rendered per harness against the
  features its registry entry declares (`subagents`, `question-dialogs`,
  `file-references`, `background-tasks`), so a generated file never mentions
  a feature its harness lacks;
- that placement, file naming, and the frontmatter dialect follow each
  harness's own convention;
- the run as numbered steps: list the registry with `shipd harness`, inspect
  one entry with `shipd harness show <id>`, generate the commands with
  `shipd harness add <id>...`, and check them with `shipd harness status`;
- that every generated file carries the ownership marker, that re-running
  `add` is idempotent and serves as the upgrade path, that `add` refuses a
  target file without the marker unless `--force` is passed, and that
  `remove` deletes only marker-carrying files;
- that a harness with no surface for the selected mode is reported as
  skipped and does not fail the run;
- that `shipd harness add aider` writes one `shipd-conventions.md` file,
  wired in through `read: shipd-conventions.md` in `.aider.conf.yml`;
- that with the `s@shipd` plugin installed at user scope and enabled,
  `shipd install` and `shipd harness add claude-code --user` write no Claude
  Code command or agent files and retire the copies shipd wrote earlier;
- in one sentence, that `shipd install` runs the user-global half for the
  harnesses a person picks.

The `## Reference` section SHALL hold a table of the five verbs `list`,
`show`, `add`, `remove`, and `status`, a table of the flags `--all`,
`--root`, `--user`, `--force`, and `--json`, and a link to
`harness-agents-reference.md` for the agent files. The page SHALL link
`customise.md`, SHALL carry no mermaid fence, and SHALL carry no table of
every registered harness. Every command on the page SHALL be a `shipd` verb
or a `/s:` skill.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/harnesses.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the feature scaling and the safety rules
- **WHEN** `docs/harnesses.md` is inspected
- **THEN** it names the four features, the ownership marker, the idempotent
  `add`, the `--force` refusal, and the marker-only `remove`

#### Scenario: Reference tables match the CLI
- **WHEN** the verbs and flags in the `## Reference` tables are compared with
  the output of `shipd harness --help`
- **THEN** every verb and flag in the tables appears in that output

#### Scenario: Page nests the agents reference
- **WHEN** the `## Reference` section is read
- **THEN** it holds a resolving link to `harness-agents-reference.md`, and
  the page states no agent file location and no agent frontmatter

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/harnesses.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer,
  the file holds no mermaid fence, and every relative link resolves

## MODIFIED Requirements

### Requirement: Agent surface documentation
id: agent-surface-docs
base: a5bfc0c0d60c
Dropped: Customise points at the reference

The documentation SHALL describe the harness agent surface.
`docs/harnesses.md` SHALL state in one sentence that a harness declaring
`subagents` receives agent files beside its commands, and SHALL link to the
reference from its `## Reference` section.
`docs/harness-agents-reference.md` SHALL be the nested reference of
`docs/harnesses.md`. It SHALL open with a link back to that main page. It
SHALL record, for each harness that declares `subagents`, its agent files'
repository and user-global locations and the frontmatter those files carry,
the `shipd-<role>` agent ids, and the steps to add a harness. It SHALL keep
how `shipd harness status` counts the agent files, and SHALL state the
plugin-provided skip in one sentence that links `harnesses.md`.

#### Scenario: The reference records each harness's agent surface
- **WHEN** `docs/harness-agents-reference.md` is read
- **THEN** it names `claude-code`, `opencode`, `agy`, and `oh-my-pi` with each
  one's agent repository and user-global location and frontmatter, and states
  the `shipd-sub-agent` and `shipd-validator` ids, and names no `shipd-oracle` agent

#### Scenario: The main page points at the reference
- **WHEN** `docs/harnesses.md` is read
- **THEN** it states that a harness declaring `subagents` receives agent
  files beside its commands, and links to `harness-agents-reference.md`

#### Scenario: The reference links back to its main page
- **WHEN** the opening paragraph of `docs/harness-agents-reference.md` is read
- **THEN** it holds a resolving link to `harnesses.md` and no link that names
  `customise.md` as the owner of the registry

#### Scenario: The reference passes the lint
- **WHEN** `docs_lint.py` runs over `docs/harness-agents-reference.md`
- **THEN** it exits 0 with the file marked `reference`
