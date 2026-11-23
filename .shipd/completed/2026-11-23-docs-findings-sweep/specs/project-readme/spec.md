## ADDED Requirements

### Requirement: Docs pages state what the engine does
id: docs-sweep-page-facts

Each page below SHALL state the named fact as the shipped engine has it, and
SHALL stay inside its doc type's line cap and pass `docs_lint.py`:

- `docs/pr.md` SHALL present the default merge rules it names as a partial
  list, and SHALL link `customise.md` from that same sentence as the full
  list. It SHALL NOT name the default approval count.
- `docs/semantic-review.md` SHALL describe a `low` finding as a real but
  minor defect and SHALL NOT give style or naming as an example of one.
- `docs/install.md` SHALL show the line the installer prints when the
  launcher directory is off the PATH: `export PATH="$HOME/.local/bin:$PATH"`.
- `docs/what-is-shipd.md` SHALL say the orchestrator runs on the session's
  model, as `docs/build.md` and `docs/core-ideas.md` do.
- `docs/cheatsheet.md` SHALL call the files `shipd harness add` writes
  generated command files, with no `/s:` label.
- `docs/plan.md` SHALL scope the gate-only exit from `rejected` to the
  `/s:plan` skill, and SHALL state that a person can also return a rejected
  plan to `draft` or `ready` through `/s:status`.
- `docs/oracle.md` SHALL state that a wiki page outranks a raw queue entry
  on the ladder.
- `docs/workspaces/external-stores.md` SHALL name the two paths that run
  networked git on a store while `store_sync` is `true`: autopilot's fetch of
  the store's `origin main`, and the session-boundary hook's push of a store
  that lives in the workspace repository, linking `teams.md` for the hook.
- `docs/room-run.md` SHALL give the by-hand hand-back flags
  `--state input-required --to <asker>`.
- `docs/room-wake-reference.md` SHALL state that an author run checks the
  head after each turn, that an unreadable head warns once and opens no
  re-review task, and that a rerun opens no task a head already has.

Where a page has no free line, the room for a fact SHALL come from rewrapping
existing paragraphs at the page's own width, never from removing a fact and
never from a new page.

#### Scenario: The merge rule list is partial and linked
- **WHEN** `### Merge it` of `docs/pr.md` is read
- **THEN** the sentence naming `ci`, `semantic-review`, and the conversation
  rule presents them as some of the default rules and links `customise.md`,
  and the page names no approval count

#### Scenario: Low severity names no style finding
- **WHEN** the severity table of `docs/semantic-review.md` is read
- **THEN** the `low` row describes a minor defect and gives neither style
  nor naming as an example

#### Scenario: The install page shows the PATH line
- **WHEN** `docs/install.md` is searched for `export PATH="$HOME/.local/bin:$PATH"`
- **THEN** one line matches, and the file is 150 lines or fewer

#### Scenario: The orchestrator's model is the session's model
- **WHEN** `docs/what-is-shipd.md` is searched for `strongest model`
- **THEN** no line matches, and the page says the orchestrator runs on the
  session's model

#### Scenario: The harness row carries no skill label
- **WHEN** the `harness` row of the `shipd` table in `docs/cheatsheet.md` is
  read
- **THEN** it says `generated command files` and holds no `/s:`

#### Scenario: A rejected plan has two exits
- **WHEN** `docs/plan.md` is read
- **THEN** its enrichment step says the skill itself reaches `ready` only
  through a gate pass, and its `### Statuses` section says a person can
  return the plan to `draft` or `ready` through `/s:status`

#### Scenario: The page outranks the queue entry
- **WHEN** `### Correcting an answer` of `docs/oracle.md` is read
- **THEN** it states that a wiki page outranks a raw queue entry on the
  ladder, and the file is 250 lines or fewer

#### Scenario: The store page names the networked paths
- **WHEN** `### Auto-commit` of `docs/workspaces/external-stores.md` is read
- **THEN** it names `store_sync`, autopilot's fetch of `origin main`, and
  the session-boundary hook, and it links `teams.md`

#### Scenario: The room pages keep their caps with the facts restored
- **WHEN** `docs_lint.py` runs over `docs/room-run.md` and
  `docs/room-wake-reference.md`
- **THEN** it exits 0, the first is 150 lines or fewer and names
  `--state input-required --to <asker>`, and the second is 250 lines or
  fewer and states the after-turn head check, the unreadable-head warning,
  and the rerun rule

### Requirement: Link text names a page by its current title
id: docs-link-text-current-titles

Where a docs page links another docs page by that page's title, the link
text SHALL be the target's current level-1 title. This requirement covers
these links: `docs/history.md` to `getting-started.md` ("Your first
change"); `docs/guardrails.md` to `copilot-review.md` ("Review gate");
`docs/room-wake-reference.md` to `copilot-review-reference.md` ("Review gate
reference"); `docs/copilot-review-reference.md` to `room-wake-reference.md`
("Room reference"); and the `## Sources` lists of the video scripts
`01-install-and-build.md`, `02-plan-and-specs.md`,
`03-worktrees-and-small-prs.md`, and `09-ci-and-copilot-review.md` under
`docs/tutorials/videos/`.

The script `docs/tutorials/videos/09-ci-and-copilot-review.md` SHALL NOT say
that `protection`, `automerge`, and `copilot-secret` are the last three
lines of `shipd doctor`, because more lines print after them.

#### Scenario: No link carries a retired title
- **WHEN** `docs/` outside `docs/retros/` is searched for the link texts
  `[Install the Copilot review gate](`, `[Copilot review reference](`,
  `[Room wake reference](`, and `[Getting started](`
- **THEN** the first three match no line, and the last matches only links
  to `workspaces/getting-started.md`, the page that still carries that
  title

#### Scenario: The doctor claim matches the output
- **WHEN** `docs/tutorials/videos/09-ci-and-copilot-review.md` is searched
  for `last three lines`
- **THEN** no line matches, and the script still names the `protection`,
  `automerge`, and `copilot-secret` lines

## MODIFIED Requirements

### Requirement: Semantic review reference
id: semantic-review-reference-doc
base: 4814d425e4c0

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
`category`, `locations`, `what`, `why`, `fix`, `status`, `note` and the optional
`suggestion` — SHALL describe `locations` as a non-empty array of
`path:LINE` strings whose first entry is the primary site, and SHALL name every `category` value the two payload
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

#### Scenario: The payload names the locations array
- **WHEN** the field table of the payload section is inspected
- **THEN** it holds a `locations` row describing a non-empty array, it holds
  no row for a field named `location`, and the suggestion conditions anchor
  on `locations[0]`

### Requirement: Core ideas page
id: core-ideas-doc
base: d4d0c869fd27

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
- the read, oracle, human ladder (`oracle.md`), the wiki (`wiki.md`), and
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

#### Scenario: The ladder is named as the pages name it
- **WHEN** the `## Knowledge` section of `docs/core-ideas.md` is read
- **THEN** it names the three rungs as read, then oracle, then human, the
  order `docs/oracle.md` gives

### Requirement: README links each docs group
id: readme-docs-group-links
base: 558090463e02

`README.md` SHALL carry a `## Documentation` section directly after
`## Install`. The section SHALL hold nine list items, in this order, each
opening with the group name in bold and carrying exactly one link into
`docs/`: **Start here** to `docs/getting-started.md`, **Plan** to
`docs/plan.md`, **Build** to `docs/build.md`, **Epics** to `docs/epics.md`,
**Review and merge** to `docs/semantic-review.md`, **Multi-agent PRs** to
`docs/multi-agent-pr.md`, **Knowledge** to `docs/oracle.md`, **Workspaces** to
`docs/workspaces.md`, and **Configure** to `docs/customise.md`. The section
SHALL close with one sentence that links `docs/cheatsheet.md` as the list of
every command.

The level-2 headings of `README.md` SHALL be exactly `## Install`,
`## Documentation`, `## Structure`, `## Adding a command`,
`## Adding a skill`, and `## After editing`, in that order. The file SHALL
total 150 lines or fewer and SHALL hold no table.

Every relative link in `README.md` SHALL resolve to an existing file. The
test file `plugins/s/skills/build/tests/test_readme_docs_links.py` SHALL
guard the line cap, the six level-2 headings, the nine group links, and the
relative links, so a later edit that breaks one fails `ci`.

#### Scenario: Each group line links its page
- **WHEN** the list items of the README's `## Documentation` section are read
- **THEN** there are nine, their bold names are the nine groups in the order
  this requirement gives, each holds exactly one `docs/` link to the page
  this requirement assigns, and every linked file exists

#### Scenario: The moved sections are gone
- **WHEN** the level-2 headings of `README.md` are listed
- **THEN** they are `## Install`, `## Documentation`, `## Structure`,
  `## Adding a command`, `## Adding a skill`, and `## After editing`, and no
  line of the file starts a table row with `|`

#### Scenario: README fits its cap
- **WHEN** `wc -l README.md` runs
- **THEN** the count is 150 or fewer

#### Scenario: Relative links resolve
- **WHEN** every markdown link in `README.md` that is not an `http` link or
  a `#` anchor is collected
- **THEN** each target, with any `#` fragment removed, is an existing file

#### Scenario: A test guards the README
- **WHEN** `python3 -m unittest plugins/s/skills/build/tests/test_readme_docs_links.py`
  runs from the repository root
- **THEN** it exits 0, and it fails when a heading is renamed, a group link
  is retargeted to a missing file, or the file grows past 150 lines
