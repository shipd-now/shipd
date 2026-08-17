## MODIFIED Requirements

### Requirement: Copilot review guide
id: copilot-review-guide
base: 49e7d10efe88

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
workflow posts the `semantic-review` commit status as `pending` when a pull
request opens or updates and then polls the reviews API for Copilot's review
of that head because Copilot-authored review submissions never trigger
workflow runs (they are made with a workflow-scoped token, which GitHub's
recursion suppression exempts from starting workflows), the verdict
classification (a review whose last non-empty line is the `fix-required`
marker posts `failure`; a `ship-it` last line, or any other last line, posts
`success` — the fail-open rule; markers quoted elsewhere never count), the
poll's bounds and timeout semantics (a timed-out poll leaves the status
`pending`, with the session flow `review_gate.py post` as the manual out),
its runner-minutes cost, that the session review flow posts the same status
context so either poster satisfies a required `semantic-review` check, and
that on pull requests from forks the workflow token is read-only so the gate
cannot post there; a private-repository prerequisites note — the Copilot
review runner's own repository checkout can fail on a private repository,
in which case the skill and verdict marker never load and every review
classifies fail-open, so the runner's checkout should be verified once and
the session flow treated as the working gate where it fails; inspecting and
maintaining the install via the bare `shipd copilot` report (the
`installed`, `stale`, `foreign`, and `absent` states), re-running `add` to
upgrade, `remove` to uninstall, and `--force` for foreign files; and the
integration's scope: the Copilot code-review surface exposes no
repository-side model selection, skill pickup is relevance-driven, and
difftastic/ripgrep are optional because the engine degrades to its text
engine without them. The guide SHALL NOT claim that
`pull_request_review`-triggered workflows run only from the default
branch's workflow file.

#### Scenario: Install section names the managed files and the head-branch rule
- **WHEN** the guide's install section is read
- **THEN** it shows `shipd copilot add`, names all four managed file paths,
  and states the files must be committed and pushed because Copilot reads
  them from the PR head branch

#### Scenario: Enablement covers per-PR and automatic review
- **WHEN** the guide's enablement section is read
- **THEN** it explains requesting Copilot as a reviewer on a pull request and
  enabling automatic review through a GitHub branch ruleset

#### Scenario: The merge-gate section states the polling bridge semantics
- **WHEN** the guide's merge-gate section is read
- **THEN** it documents `pending` on pull-request open/update, the polling
  rationale (Copilot-authored submissions trigger no workflow runs), the
  last-line verdict classification with the fail-open rule, the timeout
  leaving `pending` with the session flow as the manual out, the
  runner-minutes cost, the coexisting session-flow poster, and the fork
  read-only-token limit

#### Scenario: The private-repository prerequisite is documented
- **WHEN** the guide's prerequisites or merge-gate section is read
- **THEN** it states that the Copilot runner's checkout can fail on a
  private repository, that the skill and verdict marker then never load so
  reviews classify fail-open, and that the checkout should be verified once
  with the session flow as the fallback gate

#### Scenario: The default-branch bootstrap claim is retracted
- **WHEN** the guide is searched for the prior bootstrap limit
- **THEN** no text claims that `pull_request_review` workflows run only
  from the default branch's workflow file or that the installing pull
  request cannot be bridged

#### Scenario: Maintenance documents the report states and upgrade path
- **WHEN** the guide's maintenance section is read
- **THEN** it documents the `installed`, `stale`, `foreign`, and `absent`
  report states, re-`add` as the upgrade path, `remove` as the uninstall, and
  `--force` as the foreign-file override

#### Scenario: Scope states the model-selection absence
- **WHEN** the guide's scope section is read
- **THEN** it states that no repository-side model selection exists and that
  skill pickup is relevance-driven
