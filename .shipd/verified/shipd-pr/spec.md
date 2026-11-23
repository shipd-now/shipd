# shipd-pr

### Requirement: PR skill writes title and body
id: pr-skill-writes

The plugin SHALL ship `plugins/s/skills/pr/SKILL.md`, invoked as `/s:pr [--ticket <id>] [--draft] [--base <ref>]`. The skill SHALL read the documentation standard, draft a body whose first line is `## ☕ Pull Request`, followed by a why-first paragraph, a list of what changed, and the footer line `<sub>☕ Posted by Shipd</sub>` as its own paragraph and the body's last line; stage it with `<!-- doc-type: concept -->` as line 1; run `docs_lint.py` until it exits 0; strip the marker line; and create the pull request with `gh pr create --title` and `--body-file` (adding `--draft` when asked), or run `gh pr edit` when the branch already has one. The body SHALL NOT carry a generated-by line naming a harness. The skill SHALL print the pull request's full URL and SHALL NOT push, arm auto-merge, or read `pr-mode`.

#### Scenario: Skill names the heading, lint, and create step
- **WHEN** the pr skill test reads `plugins/s/skills/pr/SKILL.md`
- **THEN** it finds `## ☕ Pull Request`, `<sub>☕ Posted by Shipd</sub>`, `docs_lint.py`, `--body-file`, `gh pr edit`, and `/s:pr [--ticket <id>] [--draft] [--base <ref>]`, and it does not find `Shipd Pull Request`

#### Scenario: No generated-by line on any surface
- **WHEN** the pr skill test reads `plugins/s/skills/pr/SKILL.md`, `plugins/s/harness/bodies/pr.md`, and `plugins/s/harness/references/pr.md`
- **THEN** none contains `Generated with`

#### Scenario: Skill leaves push and merge to callers
- **WHEN** the test scans the skill
- **THEN** it finds no `git push` and no `gh pr merge` instruction

#### Scenario: A body with the footer lints clean
- **WHEN** a body staged with `<!-- doc-type: concept -->`, the `## ☕ Pull Request` heading, a why paragraph, a bullet, and the footer paragraph `<sub>☕ Posted by Shipd</sub>` as its last line is passed to `docs_lint.py`
- **THEN** it exits 0

### Requirement: Title rendering
id: pr-title-render

`plugins/s/skills/pr/scripts/pr_title.py` SHALL render the title from the resolved `pr.title` template. The ticket SHALL come from `--ticket`, else from the first match of `pr.ticket_pattern` in the branch name. When there is no ticket, the script SHALL drop `{ticket}` and the whitespace after it. `{change}` SHALL be the slug of a `change/<slug>` branch, else empty. The script SHALL collapse repeated whitespace, and if the rendered title is empty it SHALL exit 1. The script SHALL then pass the rendered title through `spec_common.brand_subject`, so the printed title starts with `☕ ` exactly once.

#### Scenario: Ticket from the branch
- **GIVEN** template `{ticket} {summary}`, pattern `[A-Z]+-[0-9]+`, branch `change/ABC-12-add-x`
- **WHEN** the title renders with summary `Add x`
- **THEN** it is `ABC-12 Add x`

#### Scenario: No ticket drops the placeholder
- **GIVEN** template `{ticket} {summary}` and no ticket
- **WHEN** the title renders with summary `Add x`
- **THEN** it is `Add x`

#### Scenario: Flag beats branch
- **WHEN** `--ticket XY-9` is given and the branch also matches the pattern
- **THEN** the title uses `XY-9`

#### Scenario: The printed title carries the brand once
- **WHEN** `pr_title.py title --summary "Add x"` runs
- **THEN** it prints `☕ Add x`
- **WHEN** it runs with `--summary "☕ Add x"`
- **THEN** it prints `☕ Add x`
- **WHEN** it runs with `--summary "☕ Shipd: Add x"`
- **THEN** it prints `☕ Shipd: Add x`

### Requirement: Every PR-opening flow calls the skill
id: pr-callers

No file under `plugins/s` outside test directories, and not `AGENTS.md`, SHALL contain `gh pr create --fill`. The build ship phase (auto, draft, and epic-close), `worktree.sh` next steps, `/s:gate` fallbacks, `/s:epic` amend, `/s:initiative` set, the autopilot build prompt, and the harness build and gate bodies SHALL direct the agent to open the pull request with `/s:pr`, passing `--draft` in draft mode. The skill SHALL be registered in the `AGENTS.md` skill sentence, the README table, and `docs/cheatsheet.md`, with a harness body `bodies/pr.md`.

#### Scenario: No bare fill remains
- **WHEN** the pr skill test searches `plugins/s` (excluding tests) and `AGENTS.md` for `gh pr create --fill`
- **THEN** it finds none

#### Scenario: Draft mode passes the flag
- **WHEN** the test reads the build skill's draft-mode section
- **THEN** it finds `/s:pr --draft`

#### Scenario: Registrations and body render
- **WHEN** the test reads `AGENTS.md`, `README.md`, and `docs/cheatsheet.md` and renders the `pr` body
- **THEN** each contains `/s:pr` and the render succeeds

### Requirement: Pull request user documentation
id: pr-user-docs

The repository SHALL provide `docs/pr.md`, titled "Pull requests", as the
main page for `/s:pr` and the `shipd gate rules` verb, conforming to the
shipd documentation standard with the marker `how-to` on its first line and
a total line count within that type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying that
every change ships as one pull request from its `change/<slug>` branch and
that `/s:pr` writes its title and body, then `## When to use it`,
`## How to run it`, and a closing `## Reference`, in that order.

`## When to use it` SHALL state that `/s:build` and `/s:autopilot` open the
pull request themselves, and SHALL name the cases for running `/s:pr` by
hand (a branch with no pull request, and a title or body to rewrite) and for
`shipd gate rules`.

`## How to run it` SHALL hold three level-3 steps. `### Write the pull
request` SHALL cover: pushing the branch first; the `/s:pr` invocation; that
the skill reads the change on a `change/<slug>` branch and the commit log on
any other; the body's shape (the `## ☕ Pull Request` heading, a why-first
paragraph, a short list of what changed); that the body is linted against
the documentation standard; that the title comes from the `pr.title`
template with a ticket id found through `pr.ticket_pattern`; that the skill
creates the pull request or updates the existing one, leaving its draft
state; that it prints the full URL; and that it never pushes and never arms
auto-merge. `### Merge it` SHALL show `gh pr merge --auto --squash
--delete-branch` as the command that arms auto-merge, SHALL name the default
required checks `ci` and `semantic-review` and the conversation-resolution
rule, and SHALL state in one sentence that `pr-mode: draft` opens a draft a
person merges. `### Set the merge rules` SHALL cover: bare `shipd gate
rules` as a report that prints each member of the `merge` configuration
beside the live ruleset and changes nothing; `shipd gate rules apply` as
the write that creates or updates the one ruleset named `shipd merge rules`;
that applying needs admin permission; that `/s:gate` offers the apply step
in its consent round; and that `shipd doctor` reports drift on its
`merge-rules` line.

`## Reference` SHALL hold a table of the `/s:pr` flags (`--ticket <id>`,
`--draft`, `--base <ref>`), a table of the `shipd gate rules` forms (bare,
`apply`, `--repo`, `--root`), and links to `customise.md` for the `pr`,
`pr-mode`, and `merge` keys, to `semantic-review.md`, to `copilot-review.md`,
and to `agent-identity.md` for the second-account rule. The page SHALL NOT
restate the `merge` key's members or defaults beyond the two default
required checks.

Every command on the page SHALL invoke the `shipd` binary, `git`, or `gh`,
or name a `/s:` skill — never an engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/pr.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the skill
- **WHEN** `### Write the pull request` is read
- **THEN** it names the `/s:pr` invocation, the `## ☕ Pull Request` heading,
  the why-first paragraph, the `pr.title` template, the create-or-update
  rule, the full URL, and that the skill never pushes or arms auto-merge

#### Scenario: Page covers merging
- **WHEN** `### Merge it` and `### Set the merge rules` are read
- **THEN** they show `gh pr merge --auto --squash --delete-branch`, name the
  `ci` and `semantic-review` checks, show bare `shipd gate rules` and
  `shipd gate rules apply`, name the `shipd merge rules` ruleset, and name
  the `merge-rules` doctor line

#### Scenario: Reference holds the flags and the links
- **WHEN** the page's `## Reference` section is read
- **THEN** it lists the three `/s:pr` flags and the `shipd gate rules`
  forms, and its links to `customise.md`, `semantic-review.md`,
  `copilot-review.md`, and `agent-identity.md` resolve

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/pr.md`
- **THEN** it exits 0 with the page marked `how-to` at 150 lines or fewer,
  and the page names no `spec_status.py`, `review_gate.py`, or
  `merge_rules.py` path
