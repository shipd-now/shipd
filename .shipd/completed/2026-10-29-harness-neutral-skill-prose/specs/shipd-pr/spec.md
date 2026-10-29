## MODIFIED Requirements

### Requirement: PR skill writes title and body
id: pr-skill-writes
base: 20142fdcb65a

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
