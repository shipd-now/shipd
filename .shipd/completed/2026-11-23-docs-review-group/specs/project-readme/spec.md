## MODIFIED Requirements

### Requirement: Semantic review guide
id: semantic-review-doc
base: 06ddde91715b
Dropped: Every subcommand is named

`docs/semantic-review.md` SHALL be the main page for `/s:review`: a concept
guide opening with a `<!-- doc-type: concept -->` comment on its first line,
totalling 100 lines or fewer and passing `docs_lint.py`. It SHALL list no
command flag and no JSON field — that lookup material belongs to the nested
reference.

The page SHALL follow the main-page shape. Its opening says what the review
is: that it reads a change structurally through `semdiff`, that the engine
supplies the facts and the reviewer supplies the judgement, and that a
reviewer approves only from its own account, in one sentence linking
`agent-identity.md`. The sections `## What it looks for` and
`## Severity and the blocking rule` SHALL follow, then `## When to use it`,
`## How to run it`, and a closing `## Reference`, in that order. The page
SHALL carry no `## See also` and no `## What it reads` section, and SHALL NOT
hold the `semdiff` subcommand table, which the reference owns.

`## What it looks for` SHALL describe the three passes that look past the
changed lines: downstream impact on a changed contract, the values each call
site passes, and the risk-lens triggers. It SHALL name every trigger
`semantic-review`'s `review-risk-lenses` requirement defines, which owns how
many there are — this requirement SHALL NOT fix a count. It SHALL state that
a linter finding is corroboration the reviewer weighs rather than a review
finding in itself.

`## Severity and the blocking rule` SHALL state that `high` and `medium`
block and `low` never does, and the exposure floor — an exposed secret, and
an authorization boundary reached without a scope check, always rate `high`.

`## When to use it` SHALL say when to run `/s:review` on local changes before
a push, and when to run it against a pull request, and SHALL link
`copilot-review.md` as the way to run the review on every pull request.

`## How to run it` SHALL name the `/s:review` invocation and describe both
paths a review takes: a local run that ends at the report, and a run against
a named pull request that reads prior dispositions back before posting. It
SHALL state that a named pull request is posted to by default, that the
posted findings are left open for that pull request's owner, and that
implementing and resolving them is an opt-in the invoker asks for. It SHALL
state that the review omits a finding answered with a reasoned reply, that it
keeps a finding only a commit cleared, and that a finding's identity excludes
its line number. It SHALL carry the page's one mermaid diagram, of those two
paths, showing the local path ending at the report, the posting path, and the
opted-in disposition path looping back on a later push. It SHALL hold a
`### When a tool is missing` section stating the missing-tool behaviour
exactly as `semantic-review`'s `difft-required-docs` requirement states it —
that requirement owns it, so this one SHALL NOT restate it.

`## Reference` SHALL link `semantic-review-reference.md`, naming what it
lists, and `copilot-review.md`.

`docs/copilot-review.md` SHALL link `/s:review` to this guide rather than to a
README anchor.

#### Scenario: The guide passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/semantic-review.md` runs
- **THEN** it exits `0`, and the file is 100 lines or fewer opening with the
  concept marker

#### Scenario: The guide follows the main-page shape
- **WHEN** the level-2 headings of `docs/semantic-review.md` are listed
- **THEN** they are `## What it looks for`,
  `## Severity and the blocking rule`, `## When to use it`,
  `## How to run it`, and `## Reference`, in that order

#### Scenario: The subcommand table has moved
- **WHEN** the guide is inspected
- **THEN** it names `semdiff`, holds no table of subcommands, and links
  `semantic-review-reference.md`

#### Scenario: The blocking rule and the floor are stated
- **WHEN** the guide is inspected
- **THEN** it states that `high` and `medium` block while `low` does not, and
  that an exposed secret and an unguarded authorization boundary always rate
  `high`

#### Scenario: Every trigger is named
- **WHEN** the guide is inspected
- **THEN** it names every risk-lens trigger `review-risk-lenses` defines, and
  `plugins/s/skills/review/tests/test_skill_references.py` passes

#### Scenario: The posting default is stated
- **WHEN** the guide is inspected
- **THEN** it states that a named pull request is posted to by default, that the
  findings stay open for that pull request's owner, and that dispositioning them
  is an opt-in

#### Scenario: The suppression rule is stated honestly
- **WHEN** the guide is inspected
- **THEN** it states that a reasoned reply suppresses a recurrence, that a
  commit-cleared finding is kept, and that the identity excludes the line
  number

#### Scenario: The guide carries one diagram
- **WHEN** the guide's mermaid fences are counted
- **THEN** exactly one is present, under `## How to run it`, and it shows the
  local path ending at the report and the opted-in disposition path looping
  back

#### Scenario: The missing-tool section survives
- **WHEN** the guide's `### When a tool is missing` section is read
- **THEN** it states that a review without `difft` stops

#### Scenario: The how-to points at the guide
- **WHEN** `docs/copilot-review.md` is inspected
- **THEN** its `/s:review` link resolves to `semantic-review.md`, and it
  links `copilot-review-reference.md`

### Requirement: Semantic review reference
id: semantic-review-reference-doc
base: d4e63f83a4a0

`docs/semantic-review-reference.md` SHALL be the nested reference of
`docs/semantic-review.md`: a lookup reference opening with a
`<!-- doc-type: reference -->` comment on its first line, totalling 250 lines
or fewer and passing `docs_lint.py`. It SHALL open by naming
`docs/semantic-review.md` as its main page. Among its sections it SHALL
carry: the engine's subcommands, the `--json` finding payload, the `lint`
configuration key, and the `prior` verb's output. Every other section the
page holds today SHALL survive unchanged.

The subcommands section SHALL be a table naming every `semdiff` subcommand
the review uses — `files`, `diff`, `context`, `change`, `lint`, and
`doctor` — with one line stating what each returns.

The payload section SHALL list every field of a finding — `id`, `severity`,
`category`, `location`, `what`, `why`, `fix`, `status`, `note` and the optional
`suggestion` — and SHALL name every `category` value the two payload
surfaces accept, those surfaces being the enumeration's source and
`semantic-review`'s `review-taxonomy-parity` requirement being what holds
them in agreement. This requirement SHALL NOT restate the enumeration or fix
its size. It SHALL state that `verdict` is `changes-requested` when any
finding is high or medium and `pass` otherwise, and SHALL state the
conditions a `suggestion` must meet to be committed rather than degraded to
prose.

The configuration section SHALL name both members of the `lint` key —
`run_scripts`, a boolean defaulting to false, and `disable`, a list of linter
names — and SHALL state each default.

The `prior` section SHALL list the fields each entry carries — `hash`, `path`,
`severity`, `what`, `thread_id`, `resolved` and `disposition` — and SHALL name
all four dispositions: `replied`, `autoreplied`, `commit-only` and `none`. It
SHALL state which one suppresses a recurrence and that the other three do not.
It SHALL state that a thread posted before the identity marker reports `hash`
as null, and that a null hash matches nothing.

`docs/semantic-review.md` SHALL link to this reference.

#### Scenario: The reference passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/semantic-review-reference.md` runs
- **THEN** it exits `0`, and the file is 250 lines or fewer opening with the
  reference marker

#### Scenario: Every subcommand is named
- **WHEN** the reference's subcommands section is inspected
- **THEN** its table names `files`, `diff`, `context`, `change`, `lint` and
  `doctor`, each with what it returns

#### Scenario: Every category value is listed
- **WHEN** the reference's payload section is inspected
- **THEN** it names every `category` value the payload surfaces accept

#### Scenario: The verdict rule and the suggestion conditions are stated
- **WHEN** the payload section is inspected
- **THEN** it states that any high or medium finding makes the verdict
  `changes-requested`, and states what a `suggestion` must satisfy to be
  committed

#### Scenario: Both lint members carry their defaults
- **WHEN** the configuration section is inspected
- **THEN** it names `run_scripts` and `disable` with each one's default

#### Scenario: All four dispositions are named with their effect
- **WHEN** the `prior` section is inspected
- **THEN** it names `replied`, `autoreplied`, `commit-only` and `none`, and
  states that only `replied` suppresses a recurrence

#### Scenario: The null hash is explained
- **WHEN** the `prior` section is inspected
- **THEN** it states that a thread predating the identity marker reports `hash`
  as null, and that such an entry matches nothing

#### Scenario: Existing sections survive
- **WHEN** the reference's level-2 headings are listed
- **THEN** `## The review event` and `## Room-reviewer flags` are still
  present

#### Scenario: The guide links the reference
- **WHEN** `docs/semantic-review.md` is inspected
- **THEN** it carries a link resolving to `semantic-review-reference.md`

### Requirement: Copilot review guide
id: copilot-review-guide
base: d1c929c511b6

The repository SHALL provide the review gate guide as two documents, each
conforming to the shipd documentation standard: a doc-type marker comment on
the first line and a total line count within that type's cap.

`docs/copilot-review.md` SHALL be the main page (marker `how-to`), titled
`# Review gate`, and SHALL follow the main-page shape: opening paragraphs
saying what the review gate is, then `## When to use it`, `## How to run it`,
and a closing `## Reference`, in that order, with no `## See also` section.
The opening SHALL name the `semantic-review` commit status and SHALL link
`/s:review` to `semantic-review.md`.

`## How to run it` SHALL cover, as level-3 steps in task order: the
prerequisites (a paid Copilot plan, GitHub hosting, `shipd` on the PATH),
with `/s:gate` named as the skill that runs the whole setup; installing with
`shipd copilot add` (naming all four managed file paths and `--root`);
committing and pushing the files because Copilot reads skills and workflows
from the pull request's head branch; enabling reviews per-PR (requesting
Copilot as a reviewer) and automatically (a GitHub branch ruleset), and that
the CLI reviewer mode requires neither; the reviewer-token recipe — the
`COPILOT_GITHUB_TOKEN` secret SHALL be documented as a dedicated minimal
fine-grained personal access token with no repository access and only the
account-level "Copilot Requests" permission, never a reused broad-scope
token, with the creation steps, the `gh secret set COPILOT_GITHUB_TOKEN`
storage path, a bounded expiry with fail-safe semantics, removal returning
the repository to the poll fallback, and the repository setting that lets
the CI reviewer submit a decision review; verifying via `shipd doctor`'s
`protection`, `automerge`, and `copilot-secret` lines and the bare
`shipd copilot` report; and maintenance — re-running `add` to upgrade,
`/s:gate update` to refresh a gated repository, `remove` to uninstall, and
editing the plugin's templates rather than the installed copies. A last step
SHALL cover the spec lint action as `ci-action`'s `ci-usage-docs` requirement
states it.

`## Reference` SHALL link `docs/copilot-review-reference.md`, naming what it
covers, and `semantic-review.md`.

`docs/copilot-review-reference.md` SHALL be the nested reference (marker
`reference`), titled `# Review gate reference`, opening with a link back to
the main page and covering: the four
managed files with each file's role; the merge gate's two reviewer modes —
the CLI reviewer mode selected by the `COPILOT_GITHUB_TOKEN` secret, in which
the gate posts `pending` first, runs headless GitHub Copilot CLI at a pinned
version following instructions materialized from the base ref's installed
SKILL.md, classifies the output into the strict `semantic-review` status by
the reader semantics `copilot-review-skill`'s `gate-workflow-template`
requirement states (that requirement owns the reading rule and this one SHALL
NOT restate it), posts the review text as a pull-request comment,
works on private repositories, consumes Copilot AI credits per review, and
leaves `pending` on a failed or timed-out run; and the poll fallback mode
used with no secret, including why its operative guarantee is fail-open, its
poll bounds, and that a changed skill reviews the pull request that changes
it on the poll surface only, the CLI reviewer pinning its instructions to
the base ref; a trust-boundary section stating the same-repository
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
token; the verdict classification shared by both modes, as
`gate-workflow-template` defines it, and — a property of the doc's content
rather than of the reading rule — that markers quoted elsewhere never count; that the session
review flow posts the same status context; the fork-PR read-only-token
limit; the private-repository note scoped to the poll mode, including the
setup workflow's fail-soft checkout; the `installed`/`stale`/`foreign`/
`absent` report states with `--force` as the foreign-file override; and the
integration's scope — no repository-side model selection, relevance-driven
skill pickup, and the engine's tool requirements exactly as `semantic-review`
states them: `difft-required-docs` owns `difft`'s documented status and forbids
calling it optional or claiming a review degrades, while
`doctor-provisioning` and `reference-context` own `ripgrep`'s optionality and
its `git grep` fallback. This requirement SHALL NOT restate any of them.
Every level-2 and level-3 heading the reference holds today SHALL keep its
text, so existing anchors resolve.

Each fact SHALL have one owning page. The main page owns the setup steps and
the token recipe; the reference owns the modes, the verdict, the trust
boundary, the limits, and the report states. The page that does not own a
fact SHALL state it in one sentence at most and link to the owner.

#### Scenario: Main page follows the shape
- **WHEN** the level-1 and level-2 headings of `docs/copilot-review.md` are
  listed
- **THEN** the title is `# Review gate`, and the level-2 headings are
  `## When to use it`, `## How to run it`, and `## Reference`, in that order

#### Scenario: How-to walks install, enable, token, and verify in task order
- **WHEN** `docs/copilot-review.md` is inspected
- **THEN** it shows `shipd copilot add`, names all four managed file paths,
  states the files must be committed and pushed because Copilot reads them
  from the PR head branch, covers both enable paths, carries the full
  reviewer-token recipe with the `gh secret set` storage path, names
  `shipd doctor` and bare `shipd copilot` as the verification surfaces, and
  names `/s:gate` and `/s:gate update`

#### Scenario: The reviewer-token recipe stays minimal and safe
- **WHEN** the main page's token step is read
- **THEN** it directs creating a dedicated fine-grained PAT with no
  repository access and only the "Copilot Requests" account permission,
  warns against reusing a broad-scope token, and states the fail-safe
  expiry semantics and that removing the secret restores the poll fallback

#### Scenario: Both reviewer modes stay documented end to end
- **WHEN** the reference's merge-gate material is read
- **THEN** the CLI reviewer mode (secret selection, pending-first,
  base-pinned instructions, pinned CLI version, strict status, review
  comment, private-repo support, credit cost, pending on failure or
  timeout) and the poll fallback (fail-open guarantee, poll bounds, and the
  changed-skill consequence) are both documented

#### Scenario: The trust boundary is documented honestly
- **WHEN** the reference's trust-boundary section is read
- **THEN** it states the same-repo workflow-with-secrets baseline, names
  content injection against an LLM reviewer as the residual risk, and
  documents the credential-isolated CLI step, the posting step's
  `GITHUB_PATH`/`GITHUB_ENV` insulation, base-ref-pinned instructions, the
  pinned CLI version, and `review_gate.py post` as the high-assurance path

#### Scenario: Verdict and strictness knob are documented
- **WHEN** the reference's verdict and strictness material is read
- **THEN** it states the classification as `gate-workflow-template` defines
  it, with quoted markers never counting, and names `SHIPD_GATE_FAIL_OPEN`
  with the fail-open default, the `gh variable set` enable path, the session
  flow as the manual out, and the pair-with-token guidance

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
- **THEN** the main page links to `copilot-review-reference.md`, the
  reference links back to `copilot-review.md`, and every `#` anchor either
  page uses resolves to a heading in its target
