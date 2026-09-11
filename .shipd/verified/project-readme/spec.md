# project-readme

### Requirement: README displays the shipd banner
id: readme-displays-the-shipd-banner

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
installation and the `docs/getting-started.md` link before the engine
internals.

#### Scenario: Install instructions survive the rewrite
- **WHEN** a reader wants to try the plugin
- **THEN** the README still shows how to add the marketplace and install
  the `s` plugin, and how to add a new command or skill

#### Scenario: Newcomer content precedes internals
- **WHEN** a reader scans the README top to bottom
- **THEN** installation and the `docs/getting-started.md` link appear
  before the spec-engine and statusline internals

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

### Requirement: Pipeline follower surfaces stay current
id: pipeline-follower-docs

The root `README.md`'s autonomous-pipeline overview SHALL mention that
entries may carry typed per-stage options validated strictly (unknown keys
and wrong types rejected) by the engine's stdlib-only schema module,
requiring no third-party package, linking the format authority for the full
grammar. `docs/getting-started.md`'s doctor step SHALL list the checks the
`shipd doctor` verb reports and SHALL carry a one-line mention that
`{"autonomous-pipeline": "eco"}` in `.shipd-config.json` opts a delivery
into the cheap preset.

#### Scenario: Root README names the options layer
- **WHEN** a reader finishes the README's autonomous-pipeline paragraph
- **THEN** it names typed per-stage options and strict validation and
  points at the format authority for the grammar

#### Scenario: Doctor list matches the shipped checks
- **WHEN** a reader compares the doctor step's check list in
  `docs/getting-started.md` against a `shipd doctor` run
- **THEN** every check the verb reports appears in the list

#### Scenario: Guide mentions the eco opt-in
- **WHEN** a reader searches `docs/getting-started.md` for the
  cheap-delivery opt-in
- **THEN** one line shows `{"autonomous-pipeline": "eco"}` as the way to
  opt in

### Requirement: Copilot review guide
id: copilot-review-guide

The repository SHALL provide the Copilot code-review guide as two documents,
each conforming to the shipd documentation standard: a doc-type marker
comment on the first line and a total line count within that type's cap.

`docs/copilot-review.md` SHALL be the how-to (marker `how-to`), covering in
task order: the prerequisites (a paid Copilot plan, GitHub hosting, `shipd`
on the PATH); installing with `shipd copilot add` (naming all four managed
file paths and `--root`), with `/s:gate` named as the skill that runs the
whole setup; committing and pushing the files because Copilot reads skills
and workflows from the pull request's head branch, with any
changed-skill-reviews-itself consequence scoped to the CCR/poll surface only
(the CLI reviewer pins instructions to the base ref); enabling reviews per-PR
(requesting Copilot as a reviewer) and automatically (a GitHub branch
ruleset), and that the CLI reviewer mode requires neither; the reviewer-token
recipe — the `COPILOT_GITHUB_TOKEN` secret SHALL be documented as a dedicated
minimal fine-grained personal access token with no repository access and only
the account-level "Copilot Requests" permission, never a reused broad-scope
token, with the creation steps, the `gh secret set COPILOT_GITHUB_TOKEN`
storage path, a bounded expiry with fail-safe semantics, and removal
returning the repository to the poll fallback; verifying via `shipd doctor`'s
`protection`, `automerge`, and `copilot-secret` lines and the bare
`shipd copilot` report; and maintenance — re-running `add` to upgrade,
`remove` to uninstall, and editing the plugin's templates rather than the
installed copies. The how-to SHALL link to `docs/copilot-review-reference.md`.

`docs/copilot-review-reference.md` SHALL be the reference (marker
`reference`), opening with a link back to the how-to and covering: the four
managed files with each file's role; the merge gate's two reviewer modes —
the CLI reviewer mode selected by the `COPILOT_GITHUB_TOKEN` secret, in which
the gate posts `pending` first, runs headless GitHub Copilot CLI at a pinned
version following instructions materialized from the base ref's installed
SKILL.md, classifies the output's last non-empty line into the strict
`semantic-review` status, posts the review text as a pull-request comment,
works on private repositories, consumes Copilot AI credits per review, and
leaves `pending` on a failed or timed-out run; and the poll fallback mode
used with no secret, including why its operative guarantee is fail-open and
its poll bounds; a trust-boundary section stating the same-repository
workflow-with-secrets baseline (no new actor class), content injection
against an LLM reviewer as the residual risk, and the mitigations — the CLI
step's environment holds no credential but the minimal reviewer token, the
posting step is insulated from `GITHUB_PATH`/`GITHUB_ENV` manipulation
(absolute-path `gh`, step-bound knob) so `github.token` lives only in the
posting step, the reviewer instructions are pinned to the base ref, the CLI
version is pinned, and the session flow `review_gate.py post` remains the
high-assurance path; the strictness knob — the repository Actions variable
`SHIPD_GATE_FAIL_OPEN`, default fail-open, `false` leaving every no-marker
outcome `pending`, `gh variable set` as the enable path, the session flow as
the strict repository's manual out, and pairing the knob with the reviewer
token; the verdict classification shared by both modes (a `fix-required`
last line posts `failure`, `ship-it` posts `success`, any other last line
follows the knob, markers quoted elsewhere never count); that the session
review flow posts the same status context; the fork-PR read-only-token
limit; the private-repository note scoped to the poll mode, including the
setup workflow's fail-soft checkout; the `installed`/`stale`/`foreign`/
`absent` report states with `--force` as the foreign-file override; and the
integration's scope — no repository-side model selection, relevance-driven
skill pickup, and optional difftastic/ripgrep with engine degradation.

#### Scenario: How-to walks install, enable, token, and verify in task order
- **WHEN** `docs/copilot-review.md` is inspected
- **THEN** it shows `shipd copilot add`, names all four managed file paths,
  states the files must be committed and pushed because Copilot reads them
  from the PR head branch (the changed-skill consequence scoped to the
  CCR/poll surface), covers both enable paths, carries the full
  reviewer-token recipe with the `gh secret set` storage path, and names
  `shipd doctor` and bare `shipd copilot` as the verification surfaces

#### Scenario: The reviewer-token recipe stays minimal and safe
- **WHEN** the how-to's token section is read
- **THEN** it directs creating a dedicated fine-grained PAT with no
  repository access and only the "Copilot Requests" account permission,
  warns against reusing a broad-scope token, and states the fail-safe
  expiry semantics and that removing the secret restores the poll fallback

#### Scenario: Both reviewer modes stay documented end to end
- **WHEN** the reference's merge-gate material is read
- **THEN** the CLI reviewer mode (secret selection, pending-first,
  base-pinned instructions, pinned CLI version, strict status, review
  comment, private-repo support, credit cost, pending on failure or
  timeout) and the poll fallback (fail-open guarantee and poll bounds) are
  both documented

#### Scenario: The trust boundary is documented honestly
- **WHEN** the reference's trust-boundary section is read
- **THEN** it states the same-repo workflow-with-secrets baseline, names
  content injection against an LLM reviewer as the residual risk, and
  documents the credential-isolated CLI step, the posting step's
  `GITHUB_PATH`/`GITHUB_ENV` insulation, base-ref-pinned instructions, the
  pinned CLI version, and `review_gate.py post` as the high-assurance path

#### Scenario: Verdict and strictness knob are documented
- **WHEN** the reference's verdict and strictness material is read
- **THEN** it states the last-non-empty-line classification with quoted
  markers never counting, and names `SHIPD_GATE_FAIL_OPEN` with the
  fail-open default, the `gh variable set` enable path, the session flow
  as the manual out, and the pair-with-token guidance

#### Scenario: Limits, report states, and scope are documented
- **WHEN** the reference is searched for the integration's limits
- **THEN** it states the fork-PR read-only-token limit, the poll-scoped
  private-repository note with the fail-soft setup checkout, the four
  report states with `--force`, the model-selection absence, and
  relevance-driven skill pickup

#### Scenario: Both docs carry their markers and fit their caps
- **WHEN** `docs_lint.py` runs over `docs/copilot-review.md` and
  `docs/copilot-review-reference.md`
- **THEN** it exits 0, with `docs/copilot-review.md` marked `how-to` at 150
  lines or fewer and `docs/copilot-review-reference.md` marked `reference`
  at 250 lines or fewer

#### Scenario: The pair cross-links and inbound links resolve
- **WHEN** the two docs' links are checked
- **THEN** the how-to links to `copilot-review-reference.md`, the reference
  links back to `copilot-review.md`, and `docs/guardrails.md`'s See-also
  entry resolves to the how-to

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
animated wordmark, the harness multi-select over the registry's fourteen
harnesses, the selection record at `~/.shipd/harnesses.json`, user-global
command generation for harnesses declaring a user-global directory, the
read-only `shipd doctor` preflight that closes a confirmed finish (and its
absence on the headless and aborted paths), the
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
brand mark. `docs/getting-started.md`'s install step SHALL mention the
harness selection step and its headless degradation, and the guide SHALL
name `shipd harness add` as the way to install the generated commands into
a repository.

#### Scenario: Install finish is documented
- **WHEN** a reader finishes the README's install-mode documentation
- **THEN** the interactive `shipd install` finish is described with the
  harness multi-select, the `~/.shipd/harnesses.json` selection record, the
  headless write-nothing degradation, and re-running `shipd install` to
  reopen the selection

#### Scenario: The closing preflight is documented
- **WHEN** a reader finishes the README's install finish paragraph
- **THEN** it states that a confirmed finish closes by running the read-only
  `shipd doctor` preflight, and that the headless and aborted paths do not

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

#### Scenario: Getting started carries the mode
- **WHEN** a reader follows `docs/getting-started.md`'s install step
- **THEN** the harness selection step and its headless degradation are
  mentioned, and `shipd harness add` is named for repo-level installs

### Requirement: Getting-started guide
id: getting-started-doc

`docs/getting-started.md` SHALL be the single entry how-to: it SHALL open
with a `<!-- doc-type: how-to -->` comment on its first line, total 150
lines or fewer, pass `docs_lint.py`, and walk a newcomer in this order:
install (the one-command installer), the `shipd doctor` preflight, the
`/s:onboard` tour, a first `/s:plan` and `/s:build`, then watching the
result with `shipd board`, `shipd status`, and the statusline. The plan step
SHALL name each planning artifact — `plan.md`, the per-capability delta
`spec.md`, and `tasks.md` — with its purpose and SHALL link the content
directory's `README.md` as the grammar authority. The build step SHALL name
the three durable outcomes: the `change/<name>` branch, the merge into
`verified/`, and the archive under `completed/`. The watch step SHALL give
`shipd statusline install` as the registration command and state that the
written entry resolves the newest cached snapshot rather than a
version-pinned path. The guide SHALL link `docs/cheatsheet.md` from its
closing where-to-go-next section.

#### Scenario: Guide passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/getting-started.md` runs
- **THEN** it exits 0, the first line is the how-to marker, and the file is
  at most 150 lines

#### Scenario: The walk is ordered install-first
- **WHEN** a reader follows `docs/getting-started.md` top to bottom
- **THEN** install, doctor, onboard, plan, build, and watch appear as steps
  in that order, each naming its exact command

#### Scenario: Artifacts are each explained
- **WHEN** the reader reaches the plan step
- **THEN** `plan.md`, the delta `specs/<capability>/spec.md`, and `tasks.md`
  are each named with their purpose, and the content directory's `README.md`
  is linked as the grammar authority

#### Scenario: Build outcomes are named
- **WHEN** the reader reaches the build step
- **THEN** the change branch, the `verified/` merge, and the `completed/`
  archive are all named as the build's durable outcomes

#### Scenario: Statusline registration survives updates
- **WHEN** the reader reaches the watch step
- **THEN** `shipd statusline install` is the given command, and the text
  states the registered entry resolves the newest cached snapshot rather
  than a version-pinned path

#### Scenario: Guide points at the cheatsheet
- **WHEN** a reader reaches the guide's closing where-to-go-next section
- **THEN** a relative link to `cheatsheet.md` is present there

### Requirement: Command cheatsheet
id: cheatsheet-doc

`docs/cheatsheet.md` SHALL be a lookup reference opening with a
`<!-- doc-type: reference -->` comment on its first line, totalling 250
lines or fewer and passing `docs_lint.py`, listing every user-facing command
in two tables — one for the `/s:` commands, one for the `shipd` CLI verbs.
Each row SHALL carry the invocation including its argument and option forms,
a one-line description of what the command does, and exactly one short
example invocation. The `/s:` table SHALL carry one row for every directory
under `plugins/s/skills/`, and the `shipd` table SHALL carry one row for
every verb listed in the `shipd --help` banner. Where an option is accepted
by several verbs, the cheatsheet SHALL state it once in a conventions
preamble rather than repeating it on every row. Where a verb requires a
precondition this repository does not meet, its row SHALL name that
precondition rather than omit the verb or invent an invocation that avoids
it.

#### Scenario: Cheatsheet passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/cheatsheet.md` runs
- **THEN** it exits 0, the first line is the reference marker, and the file
  is at most 250 lines

#### Scenario: Every skill has a row
- **WHEN** the `/s:` table's rows are compared against the directory names
  under `plugins/s/skills/`
- **THEN** every directory has exactly one row and no row names a command
  that has no directory

#### Scenario: Every shipd verb has a row
- **WHEN** the `shipd` table's rows are compared against the verb list
  printed by `shipd --help`
- **THEN** every listed verb has exactly one row and no row names a verb the
  banner does not list

#### Scenario: Each row carries one example
- **WHEN** a reader scans any row of either table
- **THEN** that row shows the invocation with its argument and option forms,
  a one-line description, and exactly one example invocation

#### Scenario: Read-only examples run as written
- **WHEN** the read-only examples in the `shipd` table whose rows name no
  precondition are executed verbatim from the repository root
- **THEN** each one runs and exits zero

#### Scenario: A precondition-gated row names its precondition
- **WHEN** a reader scans the row for a verb that cannot succeed here
  without setup — `workspace`, which resolves through the nearest ancestor
  `.shipd-config.json` declaring a `workspace` key
- **THEN** the row names that precondition, and its example is still the
  ordinary invocation rather than one contrived to exit zero

#### Scenario: Shared flags are stated once
- **WHEN** a reader looks for what `--json` or `--root` mean
- **THEN** they are explained in the conventions preamble, and the per-verb
  rows do not repeat that explanation

### Requirement: What-is overview layout
id: what-is-overview-layout

`docs/what-is-shipd.md` SHALL present its "How it fits together" overview as a
vertically-oriented mermaid flowchart (`flowchart TD`), so the published docs
site renders it within the content column without horizontal scrolling, and
SHALL place the present-and-future paragraph (the one beginning "Today shipd
builds itself") after that diagram, as the document's closing prose.

#### Scenario: Overview diagram is vertical
- **WHEN** the mermaid fence in `docs/what-is-shipd.md` is inspected
- **THEN** its first line declares `flowchart TD`, and `flowchart LR` appears
  nowhere in the file

#### Scenario: Future paragraph closes the document
- **WHEN** `docs/what-is-shipd.md` is read top to bottom
- **THEN** the paragraph beginning "Today shipd builds itself" appears after
  the "How it fits together" mermaid fence, and no body prose follows it

### Requirement: README links the workspaces guide first
id: readme-workspaces-flagship-link

The README's introduction SHALL link the workspaces guide
(`docs/workspaces.md`), and among the README's links into `docs/` that link
SHALL come first or immediately after the `docs/what-is-shipd.md` entry link.

#### Scenario: Workspaces guide is the flagship link
- **WHEN** the README's links into `docs/` are enumerated top to bottom
- **THEN** `docs/workspaces.md` is linked, preceded by no `docs/` link other
  than `docs/what-is-shipd.md`

### Requirement: Entry docs conform to the standard
id: entry-docs-standard

The entry path SHALL read `docs/what-is-shipd.md` (concept) →
`docs/getting-started.md` (how-to) → `docs/cheatsheet.md` (reference).
`docs/what-is-shipd.md` SHALL open with a `<!-- doc-type: concept -->`
comment on its first line, SHALL total 100 lines or fewer, SHALL pass
`docs_lint.py`, and SHALL link `getting-started.md` from its prose before
the overview diagram. `docs/quickstart.md` SHALL NOT exist, and no file
under `docs/` outside `docs/retros/`, and no line of `README.md`, SHALL
reference `quickstart.md`.

#### Scenario: What-is doc passes the lint
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/what-is-shipd.md` runs
- **THEN** it exits 0, the first line is the concept marker, and the file is
  at most 100 lines

#### Scenario: What-is doc links the entry how-to
- **WHEN** `docs/what-is-shipd.md` is read top to bottom
- **THEN** a relative link to `getting-started.md` appears before the
  mermaid fence

#### Scenario: Quickstart is gone and unreferenced
- **WHEN** the tree is searched for `quickstart`
- **THEN** `docs/quickstart.md` does not exist, and no match remains under
  `docs/` (outside `docs/retros/`) or in `README.md`
