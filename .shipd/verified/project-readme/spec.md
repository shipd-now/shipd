# project-readme

### Requirement: README opens with the shipd brand and introduction
id: readme-displays-the-shipd-banner

The `README.md` at the repository root SHALL open with the brand icon and a
short what-it-is introduction (at most a few sentences) before any
installation or mechanics content, and SHALL NOT carry a fenced ASCII-art
banner above that introduction.

#### Scenario: No banner precedes the introduction
- **WHEN** a reader opens `README.md`
- **THEN** no fenced code block appears before the introduction paragraph

#### Scenario: Introduction precedes mechanics
- **WHEN** a reader opens `README.md`
- **THEN** a short prose introduction states what shipd is before any install
  or engine documentation appears

### Requirement: README catalogs the plugin's skills
id: readme-catalogs-the-plugin-s-skills

The `README.md` SHALL include a **Skills** section listing every skill in
the `s` plugin. Each skill entry SHALL state its invocation name
(`/s:<name>`) and a one-to-two sentence description consistent with that
skill's own `description` frontmatter. The section SHALL reflect the current
skill set exactly — no missing skills, no skills that do not exist, and no
references to retired systems. The section SHALL carry exactly three group
headings — **Pipeline**, **Orchestration** and **Memory** — and every skill
SHALL appear under exactly one of them, so the section partitions the skill
set rather than sampling it.

#### Scenario: All current skills are documented
- **WHEN** the Skills section is compared against the plugin's skill
  directories
- **THEN** every skill appears with its `/s:<name>` invocation and a
  description consistent with its frontmatter

#### Scenario: No stale entries
- **WHEN** the Skills section is read
- **THEN** it names no skill that does not exist and no retired system

#### Scenario: The three groups partition the skill set
- **WHEN** the rows of the section's three group tables are collected
- **THEN** each directory under `plugins/s/skills/` appears in exactly one
  of them, and no skill appears in two

#### Scenario: The section's three headings are Pipeline, Orchestration and Memory
- **WHEN** the Skills section's group headings are read
- **THEN** they are exactly `**Pipeline**`, `**Orchestration**` and
  `**Memory**`, in that order

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
grammar. `docs/getting-started.md`'s doctor step SHALL give the `shipd doctor`
command, SHALL link `doctor.md` as the owner of the check list, SHALL NOT
list the check names itself, and SHALL carry a one-line mention that
`{"autonomous-pipeline": "eco"}` in `.shipd-config.json` opts a delivery
into the cheap preset.

#### Scenario: Root README names the options layer
- **WHEN** a reader finishes the README's autonomous-pipeline paragraph
- **THEN** it names typed per-stage options and strict validation and
  points at the format authority for the grammar

#### Scenario: Doctor step defers to the doctor page
- **WHEN** a reader reaches the doctor step of `docs/getting-started.md`
- **THEN** it shows `shipd doctor`, links `doctor.md`, and holds no list
  of check names

#### Scenario: Guide mentions the eco opt-in
- **WHEN** a reader searches `docs/getting-started.md` for the
  cheap-delivery opt-in
- **THEN** one line shows `{"autonomous-pipeline": "eco"}` as the way to
  opt in

### Requirement: Copilot review guide
id: copilot-review-guide

The repository SHALL provide the review gate guide as two documents, each
conforming to the shipd documentation standard: a doc-type marker comment on
the first line and a total line count within that type's cap.

`docs/copilot-review.md` SHALL be the main page (marker `how-to`), titled
`# Review gate`, and SHALL follow the main-page shape: opening paragraphs
saying what the review gate is, then `## When to use it`, `## How to run it`,
and a closing `## Reference`, in that order, with no `## See also` section.
The opening SHALL name the `semantic-review` commit status and SHALL link
`/s:review` to `semantic-review.md`.

`## How to run it` SHALL cover, as level-3 steps in task order: the
prerequisites (a paid Copilot plan, GitHub hosting, `shipd` on the PATH),
with `/s:gate` named as the skill that runs the whole setup; installing with
`shipd copilot add` (naming all four managed file paths and `--root`);
committing and pushing the files because Copilot reads skills and workflows
from the pull request's head branch; enabling reviews per-PR (requesting
Copilot as a reviewer) and automatically (a GitHub branch ruleset), and that
the CLI reviewer mode requires neither; the reviewer-token recipe — the
`COPILOT_GITHUB_TOKEN` secret SHALL be documented as a dedicated minimal
fine-grained personal access token with no repository access and only the
account-level "Copilot Requests" permission, never a reused broad-scope
token, with the creation steps, the `gh secret set COPILOT_GITHUB_TOKEN`
storage path, a bounded expiry with fail-safe semantics, removal returning
the repository to the poll fallback, and the repository setting that lets
the CI reviewer submit a decision review; verifying via `shipd doctor`'s
`protection`, `automerge`, and `copilot-secret` lines and the bare
`shipd copilot` report; and maintenance — re-running `add` to upgrade,
`/s:gate update` to refresh a gated repository, `remove` to uninstall, and
editing the plugin's templates rather than the installed copies. A last step
SHALL cover the spec lint action as `ci-action`'s `ci-usage-docs` requirement
states it.

`## Reference` SHALL link `docs/copilot-review-reference.md`, naming what it
covers, and `semantic-review.md`.

`docs/copilot-review-reference.md` SHALL be the nested reference (marker
`reference`), titled `# Review gate reference`, opening with a link back to
the main page and covering: the four
managed files with each file's role; the merge gate's two reviewer modes —
the CLI reviewer mode selected by the `COPILOT_GITHUB_TOKEN` secret, in which
the gate posts `pending` first, runs headless GitHub Copilot CLI at a pinned
version following instructions materialized from the base ref's installed
SKILL.md, classifies the output into the strict `semantic-review` status by
the reader semantics `copilot-review-skill`'s `gate-workflow-template`
requirement states (that requirement owns the reading rule and this one SHALL
NOT restate it), posts the review text as a pull-request comment,
works on private repositories, consumes Copilot AI credits per review, and
leaves `pending` on a failed or timed-out run; and the poll fallback mode
used with no secret, including why its operative guarantee is fail-open, its
poll bounds, and that a changed skill reviews the pull request that changes
it on the poll surface only, the CLI reviewer pinning its instructions to
the base ref; a trust-boundary section stating the same-repository
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
token; the verdict classification shared by both modes, as
`gate-workflow-template` defines it, and — a property of the doc's content
rather than of the reading rule — that markers quoted elsewhere never count; that the session
review flow posts the same status context; the fork-PR read-only-token
limit; the private-repository note scoped to the poll mode, including the
setup workflow's fail-soft checkout; the `installed`/`stale`/`foreign`/
`absent` report states with `--force` as the foreign-file override; and the
integration's scope — no repository-side model selection, relevance-driven
skill pickup, and the engine's tool requirements exactly as `semantic-review`
states them: `difft-required-docs` owns `difft`'s documented status and forbids
calling it optional or claiming a review degrades, while
`doctor-provisioning` and `reference-context` own `ripgrep`'s optionality and
its `git grep` fallback. This requirement SHALL NOT restate any of them.
Every level-2 and level-3 heading the reference holds today SHALL keep its
text, so existing anchors resolve.

Each fact SHALL have one owning page. The main page owns the setup steps and
the token recipe; the reference owns the modes, the verdict, the trust
boundary, the limits, and the report states. The page that does not own a
fact SHALL state it in one sentence at most and link to the owner.

#### Scenario: Main page follows the shape
- **WHEN** the level-1 and level-2 headings of `docs/copilot-review.md` are
  listed
- **THEN** the title is `# Review gate`, and the level-2 headings are
  `## When to use it`, `## How to run it`, and `## Reference`, in that order

#### Scenario: How-to walks install, enable, token, and verify in task order
- **WHEN** `docs/copilot-review.md` is inspected
- **THEN** it shows `shipd copilot add`, names all four managed file paths,
  states the files must be committed and pushed because Copilot reads them
  from the PR head branch, covers both enable paths, carries the full
  reviewer-token recipe with the `gh secret set` storage path, names
  `shipd doctor` and bare `shipd copilot` as the verification surfaces, and
  names `/s:gate` and `/s:gate update`

#### Scenario: The reviewer-token recipe stays minimal and safe
- **WHEN** the main page's token step is read
- **THEN** it directs creating a dedicated fine-grained PAT with no
  repository access and only the "Copilot Requests" account permission,
  warns against reusing a broad-scope token, and states the fail-safe
  expiry semantics and that removing the secret restores the poll fallback

#### Scenario: Both reviewer modes stay documented end to end
- **WHEN** the reference's merge-gate material is read
- **THEN** the CLI reviewer mode (secret selection, pending-first,
  base-pinned instructions, pinned CLI version, strict status, review
  comment, private-repo support, credit cost, pending on failure or
  timeout) and the poll fallback (fail-open guarantee, poll bounds, and the
  changed-skill consequence) are both documented

#### Scenario: The trust boundary is documented honestly
- **WHEN** the reference's trust-boundary section is read
- **THEN** it states the same-repo workflow-with-secrets baseline, names
  content injection against an LLM reviewer as the residual risk, and
  documents the credential-isolated CLI step, the posting step's
  `GITHUB_PATH`/`GITHUB_ENV` insulation, base-ref-pinned instructions, the
  pinned CLI version, and `review_gate.py post` as the high-assurance path

#### Scenario: Verdict and strictness knob are documented
- **WHEN** the reference's verdict and strictness material is read
- **THEN** it states the classification as `gate-workflow-template` defines
  it, with quoted markers never counting, and names `SHIPD_GATE_FAIL_OPEN`
  with the fail-open default, the `gh variable set` enable path, the session
  flow as the manual out, and the pair-with-token guidance

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
- **THEN** the main page links to `copilot-review-reference.md`, the
  reference links back to `copilot-review.md`, and every `#` anchor either
  page uses resolves to a heading in its target

### Requirement: README carries the brand marks
id: readme-brand-marks

The repository SHALL keep the coffee-cup vector brand as `icon.svg` at the repository root, and `README.md` SHALL display it via an `img` element referencing that file as its first rendered element. The README introduction SHALL present the product name with the ☕ brand mark directly before it, and the linked `docs/what-is-shipd.md` SHALL open its level-1 title with the same mark.

#### Scenario: Icon opens the README
- **WHEN** `README.md` is rendered
- **THEN** its first element is an `img` element referencing the repo-root `icon.svg`, floating beside the introduction

#### Scenario: Intro carries the mark
- **WHEN** a reader reaches the README introduction
- **THEN** the bold product name is directly preceded by `☕`

#### Scenario: What-is doc opens branded
- **WHEN** `docs/what-is-shipd.md` is rendered
- **THEN** its level-1 title opens with `☕` before the question naming the product

### Requirement: Harness mode documentation
id: harness-mode-docs

The `README.md` SHALL document harness mode inside its installation documentation: the interactive `shipd install` finish, animated wordmark, harness multi-select over the registry's fifteen harnesses, `~/.shipd/harnesses.json` selection record, user-global generation, closing setup check that shows one progress line, installs missing local tooling, and lists only the remaining problems with a fix each, headless degradation, and re-run path. Its explicitly labeled harness-mode subsection SHALL cover repo-level `shipd harness add` and `remove`, ownership and overwrite safety, `--user`, skipped unsupported surfaces, the four-feature scaling model, `shipd-` command names, and registry inspection verbs. The CLI verb list SHALL include `harness`; the brand note SHALL remain present. `docs/install.md` SHALL carry the install finish for docs readers: harness selection, headless degradation, and a link to `harnesses.md` for repo-level `shipd harness add`; `docs/getting-started.md` SHALL NOT restate it.

#### Scenario: Install finish is documented
- **WHEN** a reader finishes the README's install-mode documentation
- **THEN** the fifteen-harness multi-select, selection record, headless write-nothing degradation, and re-run path are described

#### Scenario: The closing preflight is documented
- **WHEN** a reader finishes the README's install finish paragraph
- **THEN** it states that a confirmed finish runs the setup check, installs missing local tooling, lists each remaining problem with its fix, and that headless and aborted paths do not

#### Scenario: Repo-level installation is documented
- **WHEN** a reader reaches the README's harness-mode subsection
- **THEN** `shipd harness add` and `remove` appear with ownership, idempotence, `--force`, and `--user` behavior

#### Scenario: Feature scaling is explained
- **WHEN** a reader reaches the feature-scaling explanation
- **THEN** all four declared features are named and generated files are described as omitting undeclared features

#### Scenario: CLI list gains the harness verb
- **WHEN** a reader reads the README's CLI verb list
- **THEN** it includes a `harness` row consistent with registry list and show behavior

#### Scenario: Brand note is stated
- **WHEN** a reader reaches the harness documentation's brand note
- **THEN** it confines the animated wordmark to installation and retains ☕ as the brand mark

#### Scenario: Install page carries the mode
- **WHEN** a reader follows `docs/install.md`'s harness step
- **THEN** harness selection and headless degradation are named, and `harnesses.md` is linked for repo-level `shipd harness add`

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

The file SHALL additionally carry exactly one mermaid diagram: a `venn-beta`
fence, above the `/s:` table and under its own level-2 heading, whose three
sets are the `README.md` **Skills** groups, named exactly as this
capability's `readme-catalogs-the-plugin-s-skills` requirement names them —
that requirement owns the group names and this one SHALL NOT restate them.
Enumerating them here is what left this requirement naming three groups the
README had renamed. Each of the fence's seven regions SHALL hold exactly
one `text` node naming what that region holds, in at most three words — and
in at most two for the three pairwise regions and the centre, whose area does
not carry more — and SHALL name no skill. The fence SHALL carry no `title` line and no `style`
line, so the corpus states content and the rendering surface states
presentation. Beneath the fence the file SHALL carry a list naming every
directory under `plugins/s/skills/` exactly once as `s:<name>`, grouped under
the region names the fence uses, so every skill the diagram places is legible
without reading the diagram.

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

#### Scenario: Every skill appears in the list exactly once
- **WHEN** the `s:<name>` tokens in the list beneath the fence are collected
  and compared against the directory names under `plugins/s/skills/`
- **THEN** every directory appears exactly once and no token names a skill
  that has no directory

#### Scenario: The fence names regions, not skills
- **WHEN** the `venn-beta` fence is read
- **THEN** each of its seven `set` and `union` declarations is followed by
  exactly one indented `text` line of at most three words, and no `text` line
  contains the string `s:`

#### Scenario: The fence is content-only and singular
- **WHEN** `docs/cheatsheet.md` is read
- **THEN** it holds exactly one ```mermaid fence, that fence's first body
  line is `venn-beta`, and the fence carries no `title` line and no `style`
  line

#### Scenario: Every region name reappears in the list
- **WHEN** the region names in the fence's `text` lines are compared against
  the bolded group names in the list beneath it
- **THEN** each of the seven region names appears in the list, so a reader
  moving from a circle to the list finds the same word

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
`docs/install.md` (how-to) → `docs/getting-started.md` (how-to) →
`docs/core-ideas.md` (concept) → `docs/cheatsheet.md` (reference).
`docs/what-is-shipd.md` SHALL open with a `<!-- doc-type: concept -->`
comment on its first line, SHALL total 100 lines or fewer, SHALL pass
`docs_lint.py`, and SHALL link `getting-started.md` from its prose before
the overview diagram, labelling that link "Your first change". Its prose
SHALL also link `core-ideas.md`, and the overview diagram's review stage
SHALL be a subgraph titled `Review and merge`, the name of the docs group
that documents it. `docs/quickstart.md` SHALL NOT exist, and no file
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

#### Scenario: What-is doc matches the regrouped docs
- **WHEN** `docs/what-is-shipd.md` is read top to bottom
- **THEN** the `getting-started.md` link is labelled "Your first change", a
  relative link to `core-ideas.md` is present, and the mermaid fence holds
  a subgraph titled `Review and merge` and none titled `Ship`

### Requirement: Semantic review guide
id: semantic-review-doc

`docs/semantic-review.md` SHALL be the main page for `/s:review`: a concept
guide opening with a `<!-- doc-type: concept -->` comment on its first line,
totalling 100 lines or fewer and passing `docs_lint.py`. It SHALL list no
command flag and no JSON field — that lookup material belongs to the nested
reference.

The page SHALL follow the main-page shape. Its opening says what the review
is: that it reads a change structurally through `semdiff`, that the engine
supplies the facts and the reviewer supplies the judgement, and that a
reviewer approves only from its own account, in one sentence linking
`agent-identity.md`. The sections `## What it looks for` and
`## Severity and the blocking rule` SHALL follow, then `## When to use it`,
`## How to run it`, and a closing `## Reference`, in that order. The page
SHALL carry no `## See also` and no `## What it reads` section, and SHALL NOT
hold the `semdiff` subcommand table, which the reference owns.

`## What it looks for` SHALL describe the three passes that look past the
changed lines: downstream impact on a changed contract, the values each call
site passes, and the risk-lens triggers. It SHALL name every trigger
`semantic-review`'s `review-risk-lenses` requirement defines, which owns how
many there are — this requirement SHALL NOT fix a count. It SHALL state that
a linter finding is corroboration the reviewer weighs rather than a review
finding in itself.

`## Severity and the blocking rule` SHALL state that `high` and `medium`
block and `low` never does, and the exposure floor — an exposed secret, and
an authorization boundary reached without a scope check, always rate `high`.

`## When to use it` SHALL say when to run `/s:review` on local changes before
a push, and when to run it against a pull request, and SHALL link
`copilot-review.md` as the way to run the review on every pull request.

`## How to run it` SHALL name the `/s:review` invocation and describe both
paths a review takes: a local run that ends at the report, and a run against
a named pull request that reads prior dispositions back before posting. It
SHALL state that a named pull request is posted to by default, that the
posted findings are left open for that pull request's owner, and that
implementing and resolving them is an opt-in the invoker asks for. It SHALL
state that the review omits a finding answered with a reasoned reply, that it
keeps a finding only a commit cleared, and that a finding's identity excludes
its line number. It SHALL carry the page's one mermaid diagram, of those two
paths, showing the local path ending at the report, the posting path, and the
opted-in disposition path looping back on a later push. It SHALL hold a
`### When a tool is missing` section stating the missing-tool behaviour
exactly as `semantic-review`'s `difft-required-docs` requirement states it —
that requirement owns it, so this one SHALL NOT restate it.

`## Reference` SHALL link `semantic-review-reference.md`, naming what it
lists, and `copilot-review.md`.

`docs/copilot-review.md` SHALL link `/s:review` to this guide rather than to a
README anchor.

#### Scenario: The guide passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/semantic-review.md` runs
- **THEN** it exits `0`, and the file is 100 lines or fewer opening with the
  concept marker

#### Scenario: The guide follows the main-page shape
- **WHEN** the level-2 headings of `docs/semantic-review.md` are listed
- **THEN** they are `## What it looks for`,
  `## Severity and the blocking rule`, `## When to use it`,
  `## How to run it`, and `## Reference`, in that order

#### Scenario: The subcommand table has moved
- **WHEN** the guide is inspected
- **THEN** it names `semdiff`, holds no table of subcommands, and links
  `semantic-review-reference.md`

#### Scenario: The blocking rule and the floor are stated
- **WHEN** the guide is inspected
- **THEN** it states that `high` and `medium` block while `low` does not, and
  that an exposed secret and an unguarded authorization boundary always rate
  `high`

#### Scenario: Every trigger is named
- **WHEN** the guide is inspected
- **THEN** it names every risk-lens trigger `review-risk-lenses` defines, and
  `plugins/s/skills/review/tests/test_skill_references.py` passes

#### Scenario: The posting default is stated
- **WHEN** the guide is inspected
- **THEN** it states that a named pull request is posted to by default, that the
  findings stay open for that pull request's owner, and that dispositioning them
  is an opt-in

#### Scenario: The suppression rule is stated honestly
- **WHEN** the guide is inspected
- **THEN** it states that a reasoned reply suppresses a recurrence, that a
  commit-cleared finding is kept, and that the identity excludes the line
  number

#### Scenario: The guide carries one diagram
- **WHEN** the guide's mermaid fences are counted
- **THEN** exactly one is present, under `## How to run it`, and it shows the
  local path ending at the report and the opted-in disposition path looping
  back

#### Scenario: The missing-tool section survives
- **WHEN** the guide's `### When a tool is missing` section is read
- **THEN** it states that a review without `difft` stops

#### Scenario: The how-to points at the guide
- **WHEN** `docs/copilot-review.md` is inspected
- **THEN** its `/s:review` link resolves to `semantic-review.md`, and it
  links `copilot-review-reference.md`

### Requirement: Semantic review reference
id: semantic-review-reference-doc

`docs/semantic-review-reference.md` SHALL be the nested reference of
`docs/semantic-review.md`: a lookup reference opening with a
`<!-- doc-type: reference -->` comment on its first line, totalling 250 lines
or fewer and passing `docs_lint.py`. It SHALL open by naming
`docs/semantic-review.md` as its main page. Among its sections it SHALL
carry: the engine's subcommands, the `--json` finding payload, the `lint`
configuration key, and the `prior` verb's output. Every other section the
page holds today SHALL survive unchanged.

The subcommands section SHALL be a table naming every `semdiff` subcommand
the review uses — `files`, `diff`, `context`, `change`, `lint`, and
`doctor` — with one line stating what each returns.

The payload section SHALL list every field of a finding — `id`, `severity`,
`category`, `location`, `what`, `why`, `fix`, `status`, `note` and the optional
`suggestion` — and SHALL name every `category` value the two payload
surfaces accept, those surfaces being the enumeration's source and
`semantic-review`'s `review-taxonomy-parity` requirement being what holds
them in agreement. This requirement SHALL NOT restate the enumeration or fix
its size. It SHALL state that `verdict` is `changes-requested` when any
finding is high or medium and `pass` otherwise, and SHALL state the
conditions a `suggestion` must meet to be committed rather than degraded to
prose.

The configuration section SHALL name both members of the `lint` key —
`run_scripts`, a boolean defaulting to false, and `disable`, a list of linter
names — and SHALL state each default.

The `prior` section SHALL list the fields each entry carries — `hash`, `path`,
`severity`, `what`, `thread_id`, `resolved` and `disposition` — and SHALL name
all four dispositions: `replied`, `autoreplied`, `commit-only` and `none`. It
SHALL state which one suppresses a recurrence and that the other three do not.
It SHALL state that a thread posted before the identity marker reports `hash`
as null, and that a null hash matches nothing.

`docs/semantic-review.md` SHALL link to this reference.

#### Scenario: The reference passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/semantic-review-reference.md` runs
- **THEN** it exits `0`, and the file is 250 lines or fewer opening with the
  reference marker

#### Scenario: Every subcommand is named
- **WHEN** the reference's subcommands section is inspected
- **THEN** its table names `files`, `diff`, `context`, `change`, `lint` and
  `doctor`, each with what it returns

#### Scenario: Every category value is listed
- **WHEN** the reference's payload section is inspected
- **THEN** it names every `category` value the payload surfaces accept

#### Scenario: The verdict rule and the suggestion conditions are stated
- **WHEN** the payload section is inspected
- **THEN** it states that any high or medium finding makes the verdict
  `changes-requested`, and states what a `suggestion` must satisfy to be
  committed

#### Scenario: Both lint members carry their defaults
- **WHEN** the configuration section is inspected
- **THEN** it names `run_scripts` and `disable` with each one's default

#### Scenario: All four dispositions are named with their effect
- **WHEN** the `prior` section is inspected
- **THEN** it names `replied`, `autoreplied`, `commit-only` and `none`, and
  states that only `replied` suppresses a recurrence

#### Scenario: The null hash is explained
- **WHEN** the `prior` section is inspected
- **THEN** it states that a thread predating the identity marker reports `hash`
  as null, and that such an entry matches nothing

#### Scenario: Existing sections survive
- **WHEN** the reference's level-2 headings are listed
- **THEN** `## The review event` and `## Room-reviewer flags` are still
  present

#### Scenario: The guide links the reference
- **WHEN** `docs/semantic-review.md` is inspected
- **THEN** it carries a link resolving to `semantic-review-reference.md`

### Requirement: Multi-agent PR entry links
id: multi-agent-pr-entry-links

The three entry surfaces SHALL link the Multi-agent PR concept doc.
`README.md`'s "Getting started" section SHALL carry one sentence that links
`docs/multi-agent-pr.md`. `docs/what-is-shipd.md` SHALL link
`multi-agent-pr.md` in a prose paragraph placed after its Mermaid diagram
and before the paragraph that opens "Today shipd builds itself", and SHALL
stay at 100 lines or fewer. The `/s:room` row of `docs/cheatsheet.md`'s
command table SHALL link `multi-agent-pr.md` in its description cell.

#### Scenario: README links the concept doc
- **WHEN** a reader opens the "Getting started" section of `README.md`
- **THEN** it contains a link to `docs/multi-agent-pr.md`

#### Scenario: Overview links the concept doc within its cap
- **WHEN** `docs_lint.py docs/what-is-shipd.md` runs and `wc -l` counts
  the file
- **THEN** the lint exits `0`, the count is 100 or fewer, and the text
  between the closing Mermaid fence and "Today shipd builds itself"
  contains a link to `multi-agent-pr.md`

#### Scenario: Cheatsheet row links the concept doc
- **WHEN** `docs_lint.py docs/cheatsheet.md` runs and the `/s:room` row of
  its command table is read
- **THEN** the lint exits `0` and the row contains a link to
  `multi-agent-pr.md`

### Requirement: Core ideas page
id: core-ideas-doc

The repository SHALL provide `docs/core-ideas.md`, titled "Core ideas", with
`<!-- doc-type: concept -->` as its first line, 100 lines or fewer, passing
`docs_lint.py`. The page SHALL define each shipd term once, in three
sentences or fewer, and link the page that owns the detail. Its level-2
sections SHALL be, in order: `## The spec`, `## A change`, `## Gates`,
`## Agents`, `## Epics`, `## Knowledge`, and `## Workspaces`. They SHALL
define and link:

- the capability library under `verified/` and a requirement with its
  scenarios, linking the content directory's `README.md`;
- a change, its three artifacts, the delta, and the statuses `draft`,
  `ready`, `active`, `complete`, `verified`, and `rejected`, linking
  `plan.md`; and the one change, one worktree, one branch, one pull request
  rule, linking `worktrees.md` and `pr.md`;
- the context gate (`plan.md`), the supersession gate
  (`supersession-gate.md`), the semantic review (`semantic-review.md`), and
  the review gate (`copilot-review.md`);
- the orchestrator, the execution agents one model tier down, and the
  validator (`build.md`); and the room (`multi-agent-pr.md`);
- an epic and its members (`epics.md`), autopilot (`autopilot.md`), and the
  initiative and PRD above an epic (`prd.md`);
- the memory, oracle, human ladder (`oracle.md`), the wiki (`wiki.md`), and
  personal memory (`memory.md`);
- a workspace (`workspaces.md`) and the layered configuration
  (`customise.md`).

The page SHALL link `what-is-shipd.md` as the owner of the overview diagram
and `cheatsheet.md` as the command list. It SHALL carry no mermaid fence, no
table, and no shell command. It SHALL NOT take the feature main-page shape.

#### Scenario: Page passes the lint within its cap
- **WHEN** `docs_lint.py docs/core-ideas.md` runs
- **THEN** it exits 0, the first line is the concept marker, and the file is
  at most 100 lines

#### Scenario: Every idea links its owner
- **WHEN** the relative links of `docs/core-ideas.md` are collected
- **THEN** they include each of the eighteen docs pages this requirement
  names and the content directory's `README.md`, and every link resolves

#### Scenario: Page stays a concept page
- **WHEN** `docs/core-ideas.md` is read
- **THEN** its level-2 headings are the seven this requirement names, in
  order, and it holds no mermaid fence, no table row, and no code fence

### Requirement: First-change guide defers to the owner pages
id: first-change-guide-owners

`docs/getting-started.md` SHALL be titled `# Your first change` and SHALL be
the main page for `/s:onboard`. It SHALL keep its six numbered step headings
and its closing `## Where to go next` heading unchanged, so the anchor
`#1-install` still resolves, and SHALL NOT take the feature main-page shape.
Each step SHALL state a fact another page owns in one sentence at most and
link that page: `install.md` from the install step, `doctor.md` from the
doctor step, `plan.md` from the plan step, `build.md` from the build step,
and `statusline-and-telemetry.md` from the watch step. The closing section
SHALL link `cheatsheet.md`, `core-ideas.md`, `what-is-shipd.md`, and
`workspaces.md`.

#### Scenario: Guide is retitled and keeps its anchors
- **WHEN** the headings of `docs/getting-started.md` are listed
- **THEN** the level-1 heading is `# Your first change`, and the level-2
  headings begin `## 1. Install` and end `## Where to go next`

#### Scenario: Each step links its owner
- **WHEN** the relative links of `docs/getting-started.md` are collected
- **THEN** they include `install.md`, `doctor.md`, `plan.md`, `build.md`,
  `statusline-and-telemetry.md`, `customise.md`, `cheatsheet.md`,
  `core-ideas.md`, `what-is-shipd.md`, and `workspaces.md`, and each resolves

### Requirement: Cheatsheet rows link each command's main page
id: cheatsheet-page-links

In both tables of `docs/cheatsheet.md`, each row's description cell SHALL
carry exactly one relative link, to the command's main page:

- `/s:` rows: `ask` to `oracle.md`; `autopilot` to `autopilot.md`; `build`
  to `build.md`; `demo` and `drive` to `drive-and-demo.md`; `doctor` to
  `doctor.md`; `document` to `document.md`; `drift` to `drift.md`; `duck` to
  `duck.md`; `epic` and
  `explain` to `epics.md`; `epic-grill` to `epic-grill.md`; `fix` to
  `fix.md`; `forget`, `memory`, and `remember` to `memory.md`; `gate` to
  `copilot-review.md`; `init` to `customise.md`; `initiative` to
  `initiatives.md`; `onboard` to `getting-started.md`; `plan`, `plan-deep`,
  and `status` to `plan.md`; `pr` to `pr.md`; `prd` to `prd.md`; `research`
  to `research.md`; `review` to `semantic-review.md`; `room` to
  `multi-agent-pr.md`; `teach` to `wiki.md`; `video-ingest` to
  `video-ingest.md`; `workspace` to `workspaces.md`; `worktree-hooks` to
  `worktrees.md`.
- `shipd` rows: `init` and `config` to `customise.md`; `list`, `status`,
  `locate`, and `lint` to `plan.md`; `related` to `fix.md`; `search` and
  `render` to `prd-reference.md`; `epic` to `epics.md`; `prd` to `prd.md`;
  `workspace` to `workspaces.md`; `wiki` to `wiki.md`; `board` to
  `build.md`; `metrics` and `statusline` to `statusline-and-telemetry.md`;
  `worktree` to `worktrees.md`; `room` to `room-run.md`; `doctor` to
  `doctor.md`; `copilot` to `copilot-review.md`; `gate` to `pr.md`;
  `harness` to `harnesses.md`; `vendor`, `install`, and `update` to
  `install.md`.

The `/s:document` row SHALL link `document.md`. The file's level-2 headings SHALL be exactly `## Conventions`,
`## How the skills overlap`, `## /s: commands`, and `## shipd CLI`; the
`doctor --fix` detail lives on `doctor.md`. The intro SHALL label its
`getting-started.md` link "Your first change".

#### Scenario: Every row links one existing page
- **WHEN** the relative links in each table row of `docs/cheatsheet.md` are
  collected
- **THEN** every row holds exactly one, it names the page
  this requirement assigns, and the file exists

#### Scenario: The cheatsheet holds lists only
- **WHEN** the level-2 headings of `docs/cheatsheet.md` are listed
- **THEN** they are `## Conventions`, `## How the skills overlap`,
  `## /s: commands`, and `## shipd CLI`, and no heading names `doctor --fix`

#### Scenario: The drifted rows are present
- **WHEN** the tables are compared against `plugins/s/skills/` and the
  `shipd --help` banner
- **THEN** a `/s:demo` row, a `room` row, and a `gate rules` row exist, and
  `s:demo` appears once in the list beneath the venn fence

### Requirement: Feature pages link across groups
id: feature-page-cross-links

Each feature main page under `docs/` SHALL link the first mention of a
`/s:` skill or a `shipd` verb that another page owns to that owner page.
The owner of each command SHALL be the page the `cheatsheet-page-links`
requirement assigns it. The sweep SHALL cover every main page the eight
feature groups wrote or reshaped, and `docs/document.md`. A link SHALL sit
in prose or in a table cell, never in a heading or inside a code fence. A
page SHALL link a given owner page at most once through this sweep, and
SHALL NOT link itself. The sweep SHALL reword nothing beyond adding the
link, and every swept page SHALL stay within its line cap and pass
`docs_lint.py`.

#### Scenario: A foreign skill's first mention is a link
- **WHEN** `docs/build.md` is inspected
- **THEN** its first prose mention of `/s:plan` links `plan.md`

#### Scenario: Swept pages stay within their caps
- **WHEN** `docs_lint.py` runs over every swept page
- **THEN** it exits 0 and no page exceeds the cap of its doc type

#### Scenario: Every added link resolves
- **WHEN** the relative links on the swept pages are collected
- **THEN** each names an existing file under `docs/`
