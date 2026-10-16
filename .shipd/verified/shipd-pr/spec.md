# shipd-pr

### Requirement: PR skill writes title and body
id: pr-skill-writes

The plugin SHALL ship `plugins/s/skills/pr/SKILL.md`, invoked as `/s:pr [--ticket <id>] [--draft] [--base <ref>]`. The skill SHALL read the documentation standard, draft a body whose first line is `## ☕ Shipd Pull Request`, followed by a why-first paragraph, a list of what changed, and the generated-by line; stage it with `<!-- doc-type: concept -->` as line 1; run `docs_lint.py` until it exits 0; strip the marker line; and create the pull request with `gh pr create --title` and `--body-file` (adding `--draft` when asked), or run `gh pr edit` when the branch already has one. The skill SHALL print the pull request's full URL and SHALL NOT push, arm auto-merge, or read `pr-mode`.

#### Scenario: Skill names the heading, lint, and create step
- **WHEN** the pr skill test reads `plugins/s/skills/pr/SKILL.md`
- **THEN** it finds `## ☕ Shipd Pull Request`, `docs_lint.py`, `--body-file`, `gh pr edit`, and `/s:pr [--ticket <id>] [--draft] [--base <ref>]`

#### Scenario: Skill leaves push and merge to callers
- **WHEN** the test scans the skill
- **THEN** it finds no `git push` and no `gh pr merge` instruction

### Requirement: Title rendering
id: pr-title-render

`plugins/s/skills/pr/scripts/pr_title.py` SHALL render the title from the resolved `pr.title` template. The ticket SHALL come from `--ticket`, else from the first match of `pr.ticket_pattern` in the branch name. When there is no ticket, the script SHALL drop `{ticket}` and the whitespace after it. `{change}` SHALL be the slug of a `change/<slug>` branch, else empty. The script SHALL collapse repeated whitespace, and if the rendered title is empty it SHALL exit 1.

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
