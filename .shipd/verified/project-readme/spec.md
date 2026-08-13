# project-readme

### Requirement: README displays the auto:mikk banner
id: readme-displays-the-auto-mikk-banner

The `README.md` at the repository root SHALL open with an ASCII-art header that
renders the project name **auto:mikk**. The banner SHALL be enclosed in a fenced
code block so it renders as monospaced preformatted text on GitHub and in
terminals.

#### Scenario: Banner is the first content
- **WHEN** a reader opens `README.md`
- **THEN** the first rendered block is the fenced ASCII-art header spelling
  `auto:mikk` (uppercase block styling permitted)

#### Scenario: Banner is preformatted
- **WHEN** the README is viewed on GitHub
- **THEN** the banner is inside a fenced code block and its columns stay aligned

### Requirement: README catalogs the plugin's skills
id: readme-catalogs-the-plugin-s-skills

The `README.md` SHALL include a **Skills** section listing every skill in the
`am` plugin. Each skill entry SHALL state its invocation name (`/s:<name>`)
and a one-to-two sentence description consistent with that skill's own
`description` frontmatter. The section SHALL reflect the current skill set
exactly — no missing skills, no skills that do not exist, and no references
to retired systems.

#### Scenario: All current skills are documented
- **WHEN** the plugin contains the skills `plan`, `build`, and `status`
- **THEN** the Skills section lists exactly `/s:plan`, `/s:build`, and
  `/s:status` with accurate descriptions

#### Scenario: The build skill is described by tier policy
- **WHEN** a reader reads the `/s:build` entry
- **THEN** it describes spec-driven orchestration that plans on the strongest
  model and delegates execution one tier below, with no OpenSpec reference

### Requirement: README retains onboarding content
id: readme-retains-onboarding-content

The rewritten `README.md` SHALL preserve the existing practical guidance: what the
project is, how to install it as a marketplace/plugin, the directory structure,
and how to add new commands and skills.

#### Scenario: Install instructions survive the rewrite
- **WHEN** a reader wants to try the plugin
- **THEN** the README still shows how to add the marketplace and install the `am`
  plugin, and how to add a new command or skill

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
