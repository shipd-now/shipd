## MODIFIED Requirements

### Requirement: Copilot review guide
id: copilot-review-guide
base: 46fb60372a16

The repository SHALL provide `docs/copilot-review.md`, a guide to running the
shipd semantic review inside GitHub Copilot code review. The guide SHALL
document, in task order: installing the integration with `shipd copilot add`,
naming the four files it manages (`.github/skills/code-review/SKILL.md`,
`.github/skills/code-review/scripts/semdiff.py`,
`.github/workflows/copilot-code-review.yml`,
`.github/workflows/copilot-review-gate.yml`) and that they must be committed
and pushed because Copilot reads skills and workflows from the pull request's
head branch, with any changed-skill-reviews-itself consequence scoped to
the CCR/poll surface only (the CLI reviewer pins instructions to the base
ref); enabling reviews both per-PR (requesting Copilot as a reviewer)
and automatically (a GitHub branch ruleset); the merge gate's two reviewer
modes — the CLI reviewer mode selected by a `COPILOT_GITHUB_TOKEN`
repository secret, in which the gate workflow posts `pending`, runs
headless GitHub Copilot CLI at a pinned version following instructions
materialized from the base ref's installed SKILL.md, classifies the
output's last non-empty line into the strict `semantic-review` status,
posts the review text as a pull-request comment, works on private
repositories, consumes Copilot AI credits per review, and leaves `pending`
on a failed or timed-out run; and the poll fallback mode used with no
secret, including why its operative guarantee is fail-open; a
reviewer-token setup section — the `COPILOT_GITHUB_TOKEN` secret SHALL be
documented as a dedicated minimal fine-grained personal access token with
no repository access and only the account-level "Copilot Requests"
permission, never a reused broad-scope token, with the creation steps, the
`gh secret set COPILOT_GITHUB_TOKEN` storage path, a bounded expiry with
fail-safe semantics, and removal returning the repository to the poll
fallback; a **trust boundary** section stating: that on a same-repository
branch pull request GitHub already runs the branch's own workflow files
with repository secrets, so the gate introduces no new actor class; that
adversarial content in a reviewed change can nonetheless attempt to steer
any LLM reviewer (the residual risk); and the template's mitigations —
the CLI step's environment holds no credential but the minimal reviewer
token, and the posting step is insulated from `GITHUB_PATH`/`GITHUB_ENV`
manipulation (absolute-path `gh`, step-bound knob), so a steered agent
has no route to the status or comments (`github.token` lives only in the
posting step), the reviewer instructions are pinned to
the base ref so the change under review cannot rewrite them, the CLI
version is pinned, and the session flow `review_gate.py post` remains the
high-assurance review path; the strictness knob — the repository Actions
variable `SHIPD_GATE_FAIL_OPEN`, default fail-open, where `false` makes
every no-marker outcome leave the status `pending` instead of posting
`success`, with `gh variable set` shown as the enable path, the session
flow `review_gate.py post` named as the strict repo's manual out, and a
cross-reference stating strict repositories should pair the knob with the
reviewer token; the verdict classification shared by both modes (a
`fix-required` last line posts `failure`, a `ship-it` last line posts
`success`, any other last line follows the knob, markers quoted elsewhere
never count); that the session review flow posts the same status context
so any poster satisfies a required `semantic-review` check; that on pull
requests from forks the workflow token is read-only so the gate cannot
post there; a private-repository note scoped to the poll mode — GitHub's
Copilot review runner cannot check out a private repository, so the skill
never loads there and its reviews classify per the knob, while the CLI
reviewer mode is unaffected — including that the setup workflow's checkout
is fail-soft, so the setup job completes rather than posting failure
notices on such repositories; inspecting and maintaining the install via
the bare `shipd copilot` report (the `installed`, `stale`, `foreign`, and
`absent` states), re-running `add` to upgrade, `remove` to uninstall, and
`--force` for foreign files; and the integration's scope: the Copilot
code-review surface exposes no repository-side model selection, skill
pickup is relevance-driven, and difftastic/ripgrep are optional because
the engine degrades to its text engine without them.

#### Scenario: Install section names the managed files and the head-branch rule
- **WHEN** the guide's install section is read
- **THEN** it shows `shipd copilot add`, names all four managed file paths,
  states the files must be committed and pushed because Copilot reads
  them from the PR head branch, and scopes any changed-skill-reviews-itself
  consequence to the CCR/poll surface

#### Scenario: The trust boundary is documented honestly
- **WHEN** the guide's trust-boundary section is read
- **THEN** it states the same-repo workflow-with-secrets baseline, names
  content injection against an LLM reviewer as the residual risk, and
  documents the mitigations: the credential-isolated CLI step (no
  `github.token`), the posting step's insulation from
  `GITHUB_PATH`/`GITHUB_ENV` manipulation, base-ref-pinned instructions,
  the pinned CLI version, and `review_gate.py post` as the
  high-assurance path

#### Scenario: The reviewer-token setup is documented minimally and safely
- **WHEN** the guide's merge-gate section is read
- **THEN** it directs creating a dedicated fine-grained PAT with no
  repository access and only the "Copilot Requests" account permission,
  warns against reusing a broad-scope token, shows the `gh secret set`
  storage path, and states the fail-safe expiry semantics and that
  removing the secret restores the poll fallback

#### Scenario: The strictness knob is documented
- **WHEN** the guide's merge-gate section is read
- **THEN** it names `SHIPD_GATE_FAIL_OPEN`, states the fail-open default
  and that `false` leaves a no-marker outcome `pending` on every classify
  path, shows the `gh variable set` enable path, names
  `review_gate.py post` as the strict repo's manual out, and
  cross-references pairing the knob with the reviewer token

#### Scenario: Both reviewer modes stay documented end to end
- **WHEN** the guide's merge-gate section is read
- **THEN** the CLI reviewer mode (secret setup, base-pinned
  SKILL.md-driven headless run at a pinned CLI version, strict status,
  review comment, private-repo support, credit cost, pending on
  failure/timeout) and the poll fallback (with the CCR surface's
  engine/marker limits) are both documented

#### Scenario: Maintenance documents the report states and upgrade path
- **WHEN** the guide's maintenance section is read
- **THEN** it documents the `installed`, `stale`, `foreign`, and `absent`
  report states, re-`add` as the upgrade path, `remove` as the uninstall,
  and `--force` as the foreign-file override

#### Scenario: Scope states the model-selection absence
- **WHEN** the guide's scope section is read
- **THEN** it states that no repository-side model selection exists and
  that skill pickup is relevance-driven
