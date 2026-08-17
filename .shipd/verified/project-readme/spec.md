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

### Requirement: Copilot review guide
id: copilot-review-guide

The repository SHALL provide `docs/copilot-review.md`, a guide to running the
shipd semantic review inside GitHub Copilot code review. The guide SHALL
document, in task order: installing the integration with `shipd copilot add`,
naming the four files it manages (`.github/skills/code-review/SKILL.md`,
`.github/skills/code-review/scripts/semdiff.py`,
`.github/workflows/copilot-code-review.yml`,
`.github/workflows/copilot-review-gate.yml`) and that they must be committed
and pushed because Copilot reads skills and workflows from the pull request's
head branch; enabling reviews both per-PR (requesting Copilot as a reviewer)
and automatically (a GitHub branch ruleset); the merge gate's two reviewer
modes — the **CLI reviewer mode**, selected by a `COPILOT_GITHUB_TOKEN`
repository secret (a fine-grained personal access token carrying the
account-level "Copilot Requests" permission), in which the gate workflow
posts `pending`, runs headless GitHub Copilot CLI following the installed
SKILL.md so the engine executes and the verdict marker is authored,
classifies the output's last non-empty line into the strict
`semantic-review` status, posts the review text as a pull-request comment,
works on private repositories, consumes Copilot AI credits per review
(order of ten per run), and leaves `pending` on a failed or timed-out run;
and the **poll fallback mode**, used with no secret, in which the workflow
polls the reviews API for GitHub's Copilot code review of the head because
Copilot-authored review submissions never trigger workflow runs — with the
documented reality that GitHub's code-review surface currently cannot
execute the engine or author the verdict marker (its bash tool is disabled
and its review body is pipeline-assembled), so the poll mode's operative
guarantee is the fail-open "Copilot reviewed this commit" and the session
flow `review_gate.py post` remains the strict alternative; the verdict
classification shared by both modes (a `fix-required` last line posts
`failure`, a `ship-it` last line posts `success`, any other last line
posts `success` fail-open, markers quoted elsewhere never count); that the
session review flow posts the same status context so any poster satisfies
a required `semantic-review` check; that on pull requests from forks the
workflow token is read-only so the gate cannot post there; a
private-repository note scoped to the poll mode — GitHub's Copilot review
runner cannot check out a private repository, so the skill never loads
there and its reviews classify fail-open, while the CLI reviewer mode is
unaffected; inspecting and maintaining the install via the bare
`shipd copilot` report (the `installed`, `stale`, `foreign`, and `absent`
states), re-running `add` to upgrade, `remove` to uninstall, and `--force`
for foreign files; and the integration's scope: the Copilot code-review
surface exposes no repository-side model selection, skill pickup is
relevance-driven, and difftastic/ripgrep are optional because the engine
degrades to its text engine without them.

#### Scenario: Install section names the managed files and the head-branch rule
- **WHEN** the guide's install section is read
- **THEN** it shows `shipd copilot add`, names all four managed file paths,
  and states the files must be committed and pushed because Copilot reads
  them from the PR head branch

#### Scenario: The CLI reviewer mode is documented end to end
- **WHEN** the guide's merge-gate section is read
- **THEN** it documents the `COPILOT_GITHUB_TOKEN` secret (a fine-grained
  PAT with the "Copilot Requests" account permission), the headless CLI
  run following the installed SKILL.md, the strict status from the
  output's last line, the review comment, private-repository support, the
  per-review AI-credit cost, and `pending` standing on a failed or
  timed-out run

#### Scenario: The poll fallback and the CCR surface's limits are documented
- **WHEN** the guide's merge-gate section is read
- **THEN** it documents the no-secret poll mode, the recursion-suppression
  rationale, and that GitHub's code-review surface currently cannot
  execute the engine or author the marker — so poll mode's operative
  guarantee is fail-open, with `review_gate.py post` as the strict
  alternative

#### Scenario: The private-repository note is scoped to poll mode
- **WHEN** the guide's prerequisites or merge-gate section is read
- **THEN** the runner-checkout failure and its fail-open consequence are
  attributed to GitHub's review runner (poll mode), and the CLI reviewer
  mode is stated to be unaffected on private repositories

#### Scenario: Maintenance documents the report states and upgrade path
- **WHEN** the guide's maintenance section is read
- **THEN** it documents the `installed`, `stale`, `foreign`, and `absent`
  report states, re-`add` as the upgrade path, `remove` as the uninstall,
  and `--force` as the foreign-file override

#### Scenario: Scope states the model-selection absence
- **WHEN** the guide's scope section is read
- **THEN** it states that no repository-side model selection exists and
  that skill pickup is relevance-driven

### Requirement: README carries the brand marks
id: readme-brand-marks

The repository SHALL keep the coffee-cup vector brand as `icon.svg` at the repository root, and `README.md` SHALL display it via an `img` element referencing that file, placed after the fenced ASCII banner so the banner remains the first rendered block. The README introduction SHALL present the product name with the ☕ brand mark directly before it, and the linked `docs/what-is-shipd.md` SHALL open its level-1 title with the same mark.

#### Scenario: Icon is displayed without displacing the banner
- **WHEN** `README.md` is rendered
- **THEN** the fenced ASCII banner is still the first rendered block, and an `img` element referencing the repo-root `icon.svg` floats beside the top content

#### Scenario: Intro carries the mark
- **WHEN** a reader reaches the README introduction
- **THEN** the bold product name is directly preceded by `☕`

#### Scenario: What-is doc opens branded
- **WHEN** `docs/what-is-shipd.md` is rendered
- **THEN** its level-1 title opens with `☕` before the question naming the product
