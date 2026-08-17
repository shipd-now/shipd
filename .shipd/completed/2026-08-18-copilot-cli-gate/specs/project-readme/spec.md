## MODIFIED Requirements

### Requirement: Copilot review guide
id: copilot-review-guide
base: 15ad24d32a35

The repository SHALL provide `docs/copilot-review.md`, a guide to running the
shipd semantic review inside GitHub Copilot code review. The guide SHALL
document, in task order: installing the integration with `shipd copilot add`,
naming the four files it manages (`.github/skills/code-review/SKILL.md`,
`.github/skills/code-review/scripts/semdiff.py`,
`.github/workflows/copilot-code-review.yml`,
`.github/workflows/copilot-review-gate.yml`) and that they must be committed
and pushed because Copilot reads skills and workflows from the pull request's
head branch; enabling reviews both per-PR (requesting Copilot as a reviewer)
and automatically (a GitHub branch ruleset); the merge gate's two reviewer
modes — the **CLI reviewer mode**, selected by a `COPILOT_GITHUB_TOKEN`
repository secret (a fine-grained personal access token carrying the
account-level "Copilot Requests" permission), in which the gate workflow
posts `pending`, runs headless GitHub Copilot CLI following the installed
SKILL.md so the engine executes and the verdict marker is authored,
classifies the output's last non-empty line into the strict
`semantic-review` status, posts the review text as a pull-request comment,
works on private repositories, consumes Copilot AI credits per review
(order of ten per run), and leaves `pending` on a failed or timed-out run;
and the **poll fallback mode**, used with no secret, in which the workflow
polls the reviews API for GitHub's Copilot code review of the head because
Copilot-authored review submissions never trigger workflow runs — with the
documented reality that GitHub's code-review surface currently cannot
execute the engine or author the verdict marker (its bash tool is disabled
and its review body is pipeline-assembled), so the poll mode's operative
guarantee is the fail-open "Copilot reviewed this commit" and the session
flow `review_gate.py post` remains the strict alternative; the verdict
classification shared by both modes (a `fix-required` last line posts
`failure`, a `ship-it` last line posts `success`, any other last line
posts `success` fail-open, markers quoted elsewhere never count); that the
session review flow posts the same status context so any poster satisfies
a required `semantic-review` check; that on pull requests from forks the
workflow token is read-only so the gate cannot post there; a
private-repository note scoped to the poll mode — GitHub's Copilot review
runner cannot check out a private repository, so the skill never loads
there and its reviews classify fail-open, while the CLI reviewer mode is
unaffected; inspecting and maintaining the install via the bare
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

#### Scenario: The CLI reviewer mode is documented end to end
- **WHEN** the guide's merge-gate section is read
- **THEN** it documents the `COPILOT_GITHUB_TOKEN` secret (a fine-grained
  PAT with the "Copilot Requests" account permission), the headless CLI
  run following the installed SKILL.md, the strict status from the
  output's last line, the review comment, private-repository support, the
  per-review AI-credit cost, and `pending` standing on a failed or
  timed-out run

#### Scenario: The poll fallback and the CCR surface's limits are documented
- **WHEN** the guide's merge-gate section is read
- **THEN** it documents the no-secret poll mode, the recursion-suppression
  rationale, and that GitHub's code-review surface currently cannot
  execute the engine or author the marker — so poll mode's operative
  guarantee is fail-open, with `review_gate.py post` as the strict
  alternative

#### Scenario: The private-repository note is scoped to poll mode
- **WHEN** the guide's prerequisites or merge-gate section is read
- **THEN** the runner-checkout failure and its fail-open consequence are
  attributed to GitHub's review runner (poll mode), and the CLI reviewer
  mode is stated to be unaffected on private repositories

#### Scenario: Maintenance documents the report states and upgrade path
- **WHEN** the guide's maintenance section is read
- **THEN** it documents the `installed`, `stale`, `foreign`, and `absent`
  report states, re-`add` as the upgrade path, `remove` as the uninstall,
  and `--force` as the foreign-file override

#### Scenario: Scope states the model-selection absence
- **WHEN** the guide's scope section is read
- **THEN** it states that no repository-side model selection exists and
  that skill pickup is relevance-driven
