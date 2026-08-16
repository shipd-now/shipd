## MODIFIED Requirements

### Requirement: README displays the shipd banner
id: readme-displays-the-auto-mikk-banner
base: c6653754b6aa

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
base: b5dd7038d953

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
base: a6f4eeb2cc15

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

## ADDED Requirements

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
