## MODIFIED Requirements

### Requirement: PR skill writes title and body
id: pr-skill-writes
base: 584516de8bfa

The plugin SHALL ship `plugins/s/skills/pr/SKILL.md`, invoked as `/s:pr [--ticket <id>] [--draft] [--base <ref>]`. The skill SHALL read the documentation standard, draft a body whose first line is `## ☕ Pull Request`, followed by a why-first paragraph, a list of what changed, the footer line `<sub>☕ Posted by Shipd</sub>` as its own paragraph directly before the generated-by line, and the generated-by line as the last line; stage it with `<!-- doc-type: concept -->` as line 1; run `docs_lint.py` until it exits 0; strip the marker line; and create the pull request with `gh pr create --title` and `--body-file` (adding `--draft` when asked), or run `gh pr edit` when the branch already has one. The skill SHALL print the pull request's full URL and SHALL NOT push, arm auto-merge, or read `pr-mode`.

#### Scenario: Skill names the heading, lint, and create step
- **WHEN** the pr skill test reads `plugins/s/skills/pr/SKILL.md`
- **THEN** it finds `## ☕ Pull Request`, `<sub>☕ Posted by Shipd</sub>`, `docs_lint.py`, `--body-file`, `gh pr edit`, and `/s:pr [--ticket <id>] [--draft] [--base <ref>]`, and it does not find `Shipd Pull Request`

#### Scenario: Skill leaves push and merge to callers
- **WHEN** the test scans the skill
- **THEN** it finds no `git push` and no `gh pr merge` instruction

#### Scenario: A body with the footer lints clean
- **WHEN** a body staged with `<!-- doc-type: concept -->`, the `## ☕ Pull Request` heading, a why paragraph, a bullet, the footer paragraph `<sub>☕ Posted by Shipd</sub>`, and the generated-by line is passed to `docs_lint.py`
- **THEN** it exits 0

### Requirement: Title rendering
id: pr-title-render
base: ff7709723c94

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
