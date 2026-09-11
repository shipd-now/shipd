## MODIFIED Requirements

### Requirement: Copilot review guide
id: copilot-review-guide
base: 81755c297004

The repository SHALL provide the Copilot code-review guide as two documents,
each conforming to the shipd documentation standard: a doc-type marker
comment on the first line and a total line count within that type's cap.

`docs/copilot-review.md` SHALL be the how-to (marker `how-to`), covering in
task order: the prerequisites (a paid Copilot plan, GitHub hosting, `shipd`
on the PATH); installing with `shipd copilot add` (naming all four managed
file paths and `--root`), with `/s:gate` named as the skill that runs the
whole setup; committing and pushing the files because Copilot reads skills
and workflows from the pull request's head branch, with any
changed-skill-reviews-itself consequence scoped to the CCR/poll surface only
(the CLI reviewer pins instructions to the base ref); enabling reviews per-PR
(requesting Copilot as a reviewer) and automatically (a GitHub branch
ruleset), and that the CLI reviewer mode requires neither; the reviewer-token
recipe — the `COPILOT_GITHUB_TOKEN` secret SHALL be documented as a dedicated
minimal fine-grained personal access token with no repository access and only
the account-level "Copilot Requests" permission, never a reused broad-scope
token, with the creation steps, the `gh secret set COPILOT_GITHUB_TOKEN`
storage path, a bounded expiry with fail-safe semantics, and removal
returning the repository to the poll fallback; verifying via `shipd doctor`'s
`protection`, `automerge`, and `copilot-secret` lines and the bare
`shipd copilot` report; and maintenance — re-running `add` to upgrade,
`remove` to uninstall, and editing the plugin's templates rather than the
installed copies. The how-to SHALL link to `docs/copilot-review-reference.md`.

`docs/copilot-review-reference.md` SHALL be the reference (marker
`reference`), opening with a link back to the how-to and covering: the four
managed files with each file's role; the merge gate's two reviewer modes —
the CLI reviewer mode selected by the `COPILOT_GITHUB_TOKEN` secret, in which
the gate posts `pending` first, runs headless GitHub Copilot CLI at a pinned
version following instructions materialized from the base ref's installed
SKILL.md, classifies the output's last non-empty line into the strict
`semantic-review` status, posts the review text as a pull-request comment,
works on private repositories, consumes Copilot AI credits per review, and
leaves `pending` on a failed or timed-out run; and the poll fallback mode
used with no secret, including why its operative guarantee is fail-open and
its poll bounds; a trust-boundary section stating the same-repository
workflow-with-secrets baseline (no new actor class), content injection
against an LLM reviewer as the residual risk, and the mitigations — the CLI
step's environment holds no credential but the minimal reviewer token, the
posting step is insulated from `GITHUB_PATH`/`GITHUB_ENV` manipulation
(absolute-path `gh`, step-bound knob) so `github.token` lives only in the
posting step, the reviewer instructions are pinned to the base ref, the CLI
version is pinned, and the session flow `review_gate.py post` remains the
high-assurance path; the strictness knob — the repository Actions variable
`SHIPD_GATE_FAIL_OPEN`, default fail-open, `false` leaving every no-marker
outcome `pending`, `gh variable set` as the enable path, the session flow as
the strict repository's manual out, and pairing the knob with the reviewer
token; the verdict classification shared by both modes (a `fix-required`
last line posts `failure`, `ship-it` posts `success`, any other last line
follows the knob, markers quoted elsewhere never count); that the session
review flow posts the same status context; the fork-PR read-only-token
limit; the private-repository note scoped to the poll mode, including the
setup workflow's fail-soft checkout; the `installed`/`stale`/`foreign`/
`absent` report states with `--force` as the foreign-file override; and the
integration's scope — no repository-side model selection, relevance-driven
skill pickup, and optional difftastic/ripgrep with engine degradation.

#### Scenario: How-to walks install, enable, token, and verify in task order
- **WHEN** `docs/copilot-review.md` is inspected
- **THEN** it shows `shipd copilot add`, names all four managed file paths,
  states the files must be committed and pushed because Copilot reads them
  from the PR head branch (the changed-skill consequence scoped to the
  CCR/poll surface), covers both enable paths, carries the full
  reviewer-token recipe with the `gh secret set` storage path, and names
  `shipd doctor` and bare `shipd copilot` as the verification surfaces

#### Scenario: The reviewer-token recipe stays minimal and safe
- **WHEN** the how-to's token section is read
- **THEN** it directs creating a dedicated fine-grained PAT with no
  repository access and only the "Copilot Requests" account permission,
  warns against reusing a broad-scope token, and states the fail-safe
  expiry semantics and that removing the secret restores the poll fallback

#### Scenario: Both reviewer modes stay documented end to end
- **WHEN** the reference's merge-gate material is read
- **THEN** the CLI reviewer mode (secret selection, pending-first,
  base-pinned instructions, pinned CLI version, strict status, review
  comment, private-repo support, credit cost, pending on failure or
  timeout) and the poll fallback (fail-open guarantee and poll bounds) are
  both documented

#### Scenario: The trust boundary is documented honestly
- **WHEN** the reference's trust-boundary section is read
- **THEN** it states the same-repo workflow-with-secrets baseline, names
  content injection against an LLM reviewer as the residual risk, and
  documents the credential-isolated CLI step, the posting step's
  `GITHUB_PATH`/`GITHUB_ENV` insulation, base-ref-pinned instructions, the
  pinned CLI version, and `review_gate.py post` as the high-assurance path

#### Scenario: Verdict and strictness knob are documented
- **WHEN** the reference's verdict and strictness material is read
- **THEN** it states the last-non-empty-line classification with quoted
  markers never counting, and names `SHIPD_GATE_FAIL_OPEN` with the
  fail-open default, the `gh variable set` enable path, the session flow
  as the manual out, and the pair-with-token guidance

#### Scenario: Limits, report states, and scope are documented
- **WHEN** the reference is searched for the integration's limits
- **THEN** it states the fork-PR read-only-token limit, the poll-scoped
  private-repository note with the fail-soft setup checkout, the four
  report states with `--force`, the model-selection absence, and
  relevance-driven skill pickup

#### Scenario: Both docs carry their markers and fit their caps
- **WHEN** `docs_lint.py` runs over `docs/copilot-review.md` and
  `docs/copilot-review-reference.md`
- **THEN** it exits 0, with `docs/copilot-review.md` marked `how-to` at 150
  lines or fewer and `docs/copilot-review-reference.md` marked `reference`
  at 250 lines or fewer

#### Scenario: The pair cross-links and inbound links resolve
- **WHEN** the two docs' links are checked
- **THEN** the how-to links to `copilot-review-reference.md`, the reference
  links back to `copilot-review.md`, and `docs/guardrails.md`'s See-also
  entry resolves to the how-to
