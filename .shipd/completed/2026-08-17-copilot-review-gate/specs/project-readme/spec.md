## MODIFIED Requirements

### Requirement: Copilot review guide
id: copilot-review-guide
base: cce9b11953fb

The repository SHALL provide `docs/copilot-review.md`, a guide to running the
shipd semantic review inside GitHub Copilot code review. The guide SHALL
document, in task order: installing the integration with `shipd copilot add`,
naming the four files it manages (`.github/skills/code-review/SKILL.md`,
`.github/skills/code-review/scripts/semdiff.py`,
`.github/workflows/copilot-code-review.yml`,
`.github/workflows/copilot-review-gate.yml`) and that they must be committed
and pushed because Copilot reads skills and workflows from the pull request's
head branch; enabling reviews both per-PR (requesting Copilot as a reviewer)
and automatically (a GitHub branch ruleset); the merge gate — the gate
workflow posts the `semantic-review` commit status, `pending` when a pull
request opens or updates and bridged from Copilot's submitted review on the
head commit (a `fix-required` verdict marker posts `failure`; a `ship-it`
marker, or a review with no parseable marker, posts `success` — the
fail-open rule), that the session review flow posts the same status context
so either poster satisfies a required `semantic-review` check, and that on
pull requests from forks the workflow token is read-only so the gate cannot
post there; inspecting and maintaining the install via the bare
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

#### Scenario: Enablement covers per-PR and automatic review
- **WHEN** the guide's enablement section is read
- **THEN** it explains requesting Copilot as a reviewer on a pull request and
  enabling automatic review through a GitHub branch ruleset

#### Scenario: The merge-gate section states the bridge semantics
- **WHEN** the guide's merge-gate section is read
- **THEN** it documents `pending` on pull-request open/update, `failure` on
  a `fix-required` marker, `success` on a `ship-it` marker or a marker-less
  review (fail-open), the session flow as a coexisting poster of the same
  status context, and the fork read-only-token limit

#### Scenario: Maintenance documents the report states and upgrade path
- **WHEN** the guide's maintenance section is read
- **THEN** it documents the `installed`, `stale`, `foreign`, and `absent`
  report states, re-`add` as the upgrade path, `remove` as the uninstall, and
  `--force` as the foreign-file override

#### Scenario: Scope states the model-selection absence
- **WHEN** the guide's scope section is read
- **THEN** it states that no repository-side model selection exists and that
  skill pickup is relevance-driven
