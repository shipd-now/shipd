## ADDED Requirements

### Requirement: Copilot review guide
id: copilot-review-guide

The repository SHALL provide `docs/copilot-review.md`, a guide to running the
shipd semantic review inside GitHub Copilot code review. The guide SHALL
document, in task order: installing the integration with `shipd copilot add`,
naming the three files it manages (`.github/skills/code-review/SKILL.md`,
`.github/skills/code-review/scripts/semdiff.py`,
`.github/workflows/copilot-code-review.yml`) and that they must be committed
and pushed because Copilot reads skills and workflows from the pull request's
head branch; enabling reviews both per-PR (requesting Copilot as a reviewer)
and automatically (a GitHub branch ruleset); inspecting and maintaining the
install via the bare `shipd copilot` report (the `installed`, `stale`,
`foreign`, and `absent` states), re-running `add` to upgrade, `remove` to
uninstall, and `--force` for foreign files; and the integration's scope: the
review is advisory alongside the repository's required `semantic-review`
status check, the Copilot code-review surface exposes no repository-side
model selection, skill pickup is relevance-driven, and difftastic/ripgrep are
optional because the engine degrades to its text engine without them.

#### Scenario: Install section names the managed files and the head-branch rule
- **WHEN** the guide's install section is read
- **THEN** it shows `shipd copilot add`, names all three managed file paths,
  and states the files must be committed and pushed because Copilot reads
  them from the PR head branch

#### Scenario: Enablement covers per-PR and automatic review
- **WHEN** the guide's enablement section is read
- **THEN** it explains requesting Copilot as a reviewer on a pull request and
  enabling automatic review through a GitHub branch ruleset

#### Scenario: Maintenance documents the report states and upgrade path
- **WHEN** the guide's maintenance section is read
- **THEN** it documents the `installed`, `stale`, `foreign`, and `absent`
  report states, re-`add` as the upgrade path, `remove` as the uninstall, and
  `--force` as the foreign-file override

#### Scenario: Scope states the advisory posture and model-selection absence
- **WHEN** the guide's scope section is read
- **THEN** it states the Copilot review is advisory beside the required
  `semantic-review` status check and that no repository-side model selection
  exists
