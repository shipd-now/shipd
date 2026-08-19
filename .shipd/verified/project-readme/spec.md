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
head branch, with any changed-skill-reviews-itself consequence scoped to
the CCR/poll surface only (the CLI reviewer pins instructions to the base
ref); enabling reviews both per-PR (requesting Copilot as a reviewer)
and automatically (a GitHub branch ruleset); the merge gate's two reviewer
modes — the CLI reviewer mode selected by a `COPILOT_GITHUB_TOKEN`
repository secret, in which the gate workflow posts `pending`, runs
headless GitHub Copilot CLI at a pinned version following instructions
materialized from the base ref's installed SKILL.md, classifies the
output's last non-empty line into the strict `semantic-review` status,
posts the review text as a pull-request comment, works on private
repositories, consumes Copilot AI credits per review, and leaves `pending`
on a failed or timed-out run; and the poll fallback mode used with no
secret, including why its operative guarantee is fail-open; a
reviewer-token setup section — the `COPILOT_GITHUB_TOKEN` secret SHALL be
documented as a dedicated minimal fine-grained personal access token with
no repository access and only the account-level "Copilot Requests"
permission, never a reused broad-scope token, with the creation steps, the
`gh secret set COPILOT_GITHUB_TOKEN` storage path, a bounded expiry with
fail-safe semantics, and removal returning the repository to the poll
fallback; a **trust boundary** section stating: that on a same-repository
branch pull request GitHub already runs the branch's own workflow files
with repository secrets, so the gate introduces no new actor class; that
adversarial content in a reviewed change can nonetheless attempt to steer
any LLM reviewer (the residual risk); and the template's mitigations —
the CLI step's environment holds no credential but the minimal reviewer
token, and the posting step is insulated from `GITHUB_PATH`/`GITHUB_ENV`
manipulation (absolute-path `gh`, step-bound knob), so a steered agent
has no route to the status or comments (`github.token` lives only in the
posting step), the reviewer instructions are pinned to
the base ref so the change under review cannot rewrite them, the CLI
version is pinned, and the session flow `review_gate.py post` remains the
high-assurance review path; the strictness knob — the repository Actions
variable `SHIPD_GATE_FAIL_OPEN`, default fail-open, where `false` makes
every no-marker outcome leave the status `pending` instead of posting
`success`, with `gh variable set` shown as the enable path, the session
flow `review_gate.py post` named as the strict repo's manual out, and a
cross-reference stating strict repositories should pair the knob with the
reviewer token; the verdict classification shared by both modes (a
`fix-required` last line posts `failure`, a `ship-it` last line posts
`success`, any other last line follows the knob, markers quoted elsewhere
never count); that the session review flow posts the same status context
so any poster satisfies a required `semantic-review` check; that on pull
requests from forks the workflow token is read-only so the gate cannot
post there; a private-repository note scoped to the poll mode — GitHub's
Copilot review runner cannot check out a private repository, so the skill
never loads there and its reviews classify per the knob, while the CLI
reviewer mode is unaffected — including that the setup workflow's checkout
is fail-soft, so the setup job completes rather than posting failure
notices on such repositories; inspecting and maintaining the install via
the bare `shipd copilot` report (the `installed`, `stale`, `foreign`, and
`absent` states), re-running `add` to upgrade, `remove` to uninstall, and
`--force` for foreign files; and the integration's scope: the Copilot
code-review surface exposes no repository-side model selection, skill
pickup is relevance-driven, and difftastic/ripgrep are optional because
the engine degrades to its text engine without them.

#### Scenario: Install section names the managed files and the head-branch rule
- **WHEN** the guide's install section is read
- **THEN** it shows `shipd copilot add`, names all four managed file paths,
  states the files must be committed and pushed because Copilot reads
  them from the PR head branch, and scopes any changed-skill-reviews-itself
  consequence to the CCR/poll surface

#### Scenario: The trust boundary is documented honestly
- **WHEN** the guide's trust-boundary section is read
- **THEN** it states the same-repo workflow-with-secrets baseline, names
  content injection against an LLM reviewer as the residual risk, and
  documents the mitigations: the credential-isolated CLI step (no
  `github.token`), the posting step's insulation from
  `GITHUB_PATH`/`GITHUB_ENV` manipulation, base-ref-pinned instructions,
  the pinned CLI version, and `review_gate.py post` as the
  high-assurance path

#### Scenario: The reviewer-token setup is documented minimally and safely
- **WHEN** the guide's merge-gate section is read
- **THEN** it directs creating a dedicated fine-grained PAT with no
  repository access and only the "Copilot Requests" account permission,
  warns against reusing a broad-scope token, shows the `gh secret set`
  storage path, and states the fail-safe expiry semantics and that
  removing the secret restores the poll fallback

#### Scenario: The strictness knob is documented
- **WHEN** the guide's merge-gate section is read
- **THEN** it names `SHIPD_GATE_FAIL_OPEN`, states the fail-open default
  and that `false` leaves a no-marker outcome `pending` on every classify
  path, shows the `gh variable set` enable path, names
  `review_gate.py post` as the strict repo's manual out, and
  cross-references pairing the knob with the reviewer token

#### Scenario: Both reviewer modes stay documented end to end
- **WHEN** the guide's merge-gate section is read
- **THEN** the CLI reviewer mode (secret setup, base-pinned
  SKILL.md-driven headless run at a pinned CLI version, strict status,
  review comment, private-repo support, credit cost, pending on
  failure/timeout) and the poll fallback (with the CCR surface's
  engine/marker limits) are both documented

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

### Requirement: Harness mode documentation
id: harness-mode-docs

The `README.md` SHALL document the harness mode inside its installation
documentation: the interactive install finish (`shipd install`) — the
animated wordmark, the harness multi-select over the registry's twelve
harnesses, the selection record at `~/.shipd/harnesses.json`, user-global
command generation for harnesses declaring a user-global directory, the
headless degradation that prints a note and writes nothing, and re-running
`shipd install` to reopen the selection — and, in an explicitly labeled
harness-mode subsection, the repo-level `shipd harness add`/`remove` actions
(the ownership marker, idempotent refresh, refusal of unmarked files without
`--force`, `--user` for the user-global surfaces, and harnesses without a
surface reported as skipped), the feature-scaling model (the declared feature
vocabulary `subagents`, `question-dialogs`, `file-references`,
`background-tasks`; one shared body per command rendered per harness so a
generated file never mentions a feature its harness did not declare; the
`shipd-` command-id prefix), and `shipd harness` / `shipd harness show <id>`
as the inspection verbs. The README's CLI verb list SHALL include the
`harness` verb. The harness documentation SHALL carry the brand note: the
animated wordmark is confined to the install surface and ☕ remains the
brand mark. `docs/quickstart.md`'s install step SHALL mention the harness
selection step and its headless degradation, and the quickstart SHALL name
`shipd harness add` as the way to install the generated commands into a
repository.

#### Scenario: Install finish is documented
- **WHEN** a reader finishes the README's install-mode documentation
- **THEN** the interactive `shipd install` finish is described with the
  harness multi-select, the `~/.shipd/harnesses.json` selection record, the
  headless write-nothing degradation, and re-running `shipd install` to
  reopen the selection

#### Scenario: Repo-level installation is documented
- **WHEN** a reader reaches the README's harness-mode subsection
- **THEN** `shipd harness add` and `remove` appear with the ownership
  marker, the idempotent re-run, `--force` for unmarked files, and `--user`
  for the user-global surfaces

#### Scenario: Feature scaling is explained
- **WHEN** a reader reaches the feature-scaling explanation
- **THEN** the four declared features are named and the text states that a
  generated file never mentions a feature its harness did not declare

#### Scenario: CLI list gains the harness verb
- **WHEN** a reader reads the README's CLI verb list
- **THEN** it includes a `harness` row consistent with the verb's registry
  list/show behavior

#### Scenario: Brand note is stated
- **WHEN** a reader reaches the harness documentation's brand note
- **THEN** it states the animated wordmark appears only on the install
  surface and that ☕ remains the brand mark

#### Scenario: Quickstart carries the mode
- **WHEN** a reader follows `docs/quickstart.md`'s install step
- **THEN** the harness selection step and its headless degradation are
  mentioned, and `shipd harness add` is named for repo-level installs
