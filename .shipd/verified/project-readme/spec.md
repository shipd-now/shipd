# project-readme

### Requirement: README displays the shipd banner
id: readme-displays-the-auto-mikk-banner

The `README.md` at the repository root SHALL open with an ASCII-art header
that renders the project name **shipd**. The banner SHALL be enclosed in a
fenced code block so it renders as monospaced preformatted text on GitHub
and in terminals, and SHALL be followed by a short what-it-is introduction
(at most a few sentences) before any installation or mechanics content.

#### Scenario: Banner is the first content
- **WHEN** a reader opens `README.md`
- **THEN** the first rendered block is the fenced ASCII-art header spelling
  `shipd` (uppercase block styling permitted)

#### Scenario: Banner is preformatted
- **WHEN** the README is viewed on GitHub
- **THEN** the banner is inside a fenced code block and its columns stay
  aligned

#### Scenario: What-it-is precedes mechanics
- **WHEN** a reader continues past the banner
- **THEN** a short prose introduction states what shipd is before any
  install or engine documentation appears

### Requirement: README catalogs the plugin's skills
id: readme-catalogs-the-plugin-s-skills

The `README.md` SHALL include a **Skills** section listing every skill in
the `s` plugin. Each skill entry SHALL state its invocation name
(`/s:<name>`) and a one-to-two sentence description consistent with that
skill's own `description` frontmatter. The section SHALL reflect the current
skill set exactly — no missing skills, no skills that do not exist, and no
references to retired systems.

#### Scenario: All current skills are documented
- **WHEN** the Skills section is compared against the plugin's skill
  directories
- **THEN** every skill appears with its `/s:<name>` invocation and a
  description consistent with its frontmatter

#### Scenario: No stale entries
- **WHEN** the Skills section is read
- **THEN** it names no skill that does not exist and no retired system

### Requirement: README retains onboarding content
id: readme-retains-onboarding-content

The `README.md` SHALL preserve the existing practical guidance: what the
project is, how to install it as a marketplace/plugin, the directory
structure, and how to add new commands and skills, ordered newcomer-first —
installation and the quickstart link before the engine internals.

#### Scenario: Install instructions survive the rewrite
- **WHEN** a reader wants to try the plugin
- **THEN** the README still shows how to add the marketplace and install
  the `s` plugin, and how to add a new command or skill

#### Scenario: Newcomer content precedes internals
- **WHEN** a reader scans the README top to bottom
- **THEN** installation and the quickstart link appear before the
  spec-engine and statusline internals

### Requirement: README documents the spec engine and status pipeline
id: readme-documents-spec-engine

The `README.md` SHALL document the homegrown spec system: the `.shipd/` layout
(`planned/` in-flight changes, `completed/` applied changes, `verified/`
master library) with its configurability via `.shipd-config.json` (layered
upward search, the `dir` key) and the lean change artifacts; the five-status
lifecycle (`draft`, `ready`, `active`, `complete`, `verified`) with one-line
stage meanings, its pipeline ownership, and the guarded `set-status`
transitions with `--force` override; the ☕ statusline (rendered line
format, spec selection via `spec_status.py use`, and its
`.claude/settings.json` registration); and the build telemetry (report
table, the `build` config key in `~/.shipd-config.json`, `builds.jsonl` under
`~/.shipd/builds/`). It SHALL link to the content directory's `README.md` as
the grammar authority rather than restating the requirement/delta grammar.

#### Scenario: Lifecycle is explained
- **WHEN** a reader reaches the spec-engine documentation
- **THEN** the five statuses appear in pipeline order with a one-line
  meaning each, and guarded transitions with `--force` override are
  described

#### Scenario: Storage convention is explained
- **WHEN** a reader reaches the layout documentation
- **THEN** the `.shipd/` default, the `.shipd-config.json` layering, and the
  `dir` key are described

### Requirement: Quickstart document
id: quickstart-doc

A `docs/quickstart.md` SHALL walk a newcomer from install to a first
shipped change with the exact command at each step: the one-command
install, the `shipd doctor` preflight, the `/s:onboard` guided tour, a
first `/s:plan` and `/s:build` in the reader's own repository, and
watching the result with `shipd board` and `shipd status`. The README SHALL
link the quickstart from its newcomer-facing top section.

#### Scenario: Quickstart covers install to first change
- **WHEN** a reader follows `docs/quickstart.md` top to bottom
- **THEN** each step names its exact command, in order: install, doctor,
  onboard, plan, build, board/status

#### Scenario: README links the quickstart
- **WHEN** a reader finishes the README's install section
- **THEN** a link to `docs/quickstart.md` is present before the engine
  internals

### Requirement: Pipeline follower surfaces stay current
id: pipeline-follower-docs

The root `README.md`'s autonomous-pipeline overview SHALL mention that
entries may carry typed per-stage options validated strictly (unknown keys
and wrong types rejected) and that a declared list requires pydantic,
linking the format authority for the full grammar. `docs/quickstart.md`
SHALL list the `shipd doctor` checks as shipped — including the `pydantic`
check — and SHALL carry a one-line mention that
`{"autonomous-pipeline": "eco"}` in `.shipd-config.json` opts a delivery
into the cheap preset.

#### Scenario: Root README names the options layer
- **WHEN** a reader finishes the README's autonomous-pipeline paragraph
- **THEN** it names typed per-stage options and strict validation and
  points at the format authority for the grammar

#### Scenario: Quickstart doctor list matches the shipped checks
- **WHEN** a reader compares quickstart's doctor check list against a
  `shipd doctor` run
- **THEN** every check the verb reports — `python`, `git`, `config`, `gh`,
  `textual`, `pydantic`, `snapshot` — appears in the list

#### Scenario: Quickstart mentions the eco opt-in
- **WHEN** a reader searches quickstart for the cheap-delivery opt-in
- **THEN** one line shows `{"autonomous-pipeline": "eco"}` as the way to
  opt in
