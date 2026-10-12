## MODIFIED Requirements

### Requirement: Copilot review guide
id: copilot-review-guide
base: c9499a95ed2e

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
SKILL.md, classifies the output into the strict `semantic-review` status by
the reader semantics `copilot-review-skill`'s `gate-workflow-template`
requirement states (that requirement owns the reading rule and this one SHALL
NOT restate it), posts the review text as a pull-request comment,
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
- **THEN** it states the classification as `gate-workflow-template` defines
  it, with quoted markers never counting, and names `SHIPD_GATE_FAIL_OPEN`
  with the
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

### Requirement: Command cheatsheet
id: cheatsheet-doc
base: 4c1a05aa27ff

`docs/cheatsheet.md` SHALL be a lookup reference opening with a
`<!-- doc-type: reference -->` comment on its first line, totalling 250
lines or fewer and passing `docs_lint.py`, listing every user-facing command
in two tables — one for the `/s:` commands, one for the `shipd` CLI verbs.
Each row SHALL carry the invocation including its argument and option forms,
a one-line description of what the command does, and exactly one short
example invocation. The `/s:` table SHALL carry one row for every directory
under `plugins/s/skills/`, and the `shipd` table SHALL carry one row for
every verb listed in the `shipd --help` banner. Where an option is accepted
by several verbs, the cheatsheet SHALL state it once in a conventions
preamble rather than repeating it on every row. Where a verb requires a
precondition this repository does not meet, its row SHALL name that
precondition rather than omit the verb or invent an invocation that avoids
it.

The file SHALL additionally carry exactly one mermaid diagram: a `venn-beta`
fence, above the `/s:` table and under its own level-2 heading, whose three
sets are the `README.md` **Skills** groups, named exactly as this
capability's `readme-catalogs-the-plugin-s-skills` requirement names them —
that requirement owns the group names and this one SHALL NOT restate them.
Enumerating them here is what left this requirement naming three groups the
README had renamed. Each of the fence's seven regions SHALL hold exactly
one `text` node naming what that region holds, in at most three words — and
in at most two for the three pairwise regions and the centre, whose area does
not carry more — and SHALL name no skill. The fence SHALL carry no `title` line and no `style`
line, so the corpus states content and the rendering surface states
presentation. Beneath the fence the file SHALL carry a list naming every
directory under `plugins/s/skills/` exactly once as `s:<name>`, grouped under
the region names the fence uses, so every skill the diagram places is legible
without reading the diagram.

#### Scenario: Cheatsheet passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/cheatsheet.md` runs
- **THEN** it exits 0, the first line is the reference marker, and the file
  is at most 250 lines

#### Scenario: Every skill has a row
- **WHEN** the `/s:` table's rows are compared against the directory names
  under `plugins/s/skills/`
- **THEN** every directory has exactly one row and no row names a command
  that has no directory

#### Scenario: Every shipd verb has a row
- **WHEN** the `shipd` table's rows are compared against the verb list
  printed by `shipd --help`
- **THEN** every listed verb has exactly one row and no row names a verb the
  banner does not list

#### Scenario: Each row carries one example
- **WHEN** a reader scans any row of either table
- **THEN** that row shows the invocation with its argument and option forms,
  a one-line description, and exactly one example invocation

#### Scenario: Read-only examples run as written
- **WHEN** the read-only examples in the `shipd` table whose rows name no
  precondition are executed verbatim from the repository root
- **THEN** each one runs and exits zero

#### Scenario: A precondition-gated row names its precondition
- **WHEN** a reader scans the row for a verb that cannot succeed here
  without setup — `workspace`, which resolves through the nearest ancestor
  `.shipd-config.json` declaring a `workspace` key
- **THEN** the row names that precondition, and its example is still the
  ordinary invocation rather than one contrived to exit zero

#### Scenario: Shared flags are stated once
- **WHEN** a reader looks for what `--json` or `--root` mean
- **THEN** they are explained in the conventions preamble, and the per-verb
  rows do not repeat that explanation

#### Scenario: Every skill appears in the list exactly once
- **WHEN** the `s:<name>` tokens in the list beneath the fence are collected
  and compared against the directory names under `plugins/s/skills/`
- **THEN** every directory appears exactly once and no token names a skill
  that has no directory

#### Scenario: The fence names regions, not skills
- **WHEN** the `venn-beta` fence is read
- **THEN** each of its seven `set` and `union` declarations is followed by
  exactly one indented `text` line of at most three words, and no `text` line
  contains the string `s:`

#### Scenario: The fence is content-only and singular
- **WHEN** `docs/cheatsheet.md` is read
- **THEN** it holds exactly one ```mermaid fence, that fence's first body
  line is `venn-beta`, and the fence carries no `title` line and no `style`
  line

#### Scenario: Every region name reappears in the list
- **WHEN** the region names in the fence's `text` lines are compared against
  the bolded group names in the list beneath it
- **THEN** each of the seven region names appears in the list, so a reader
  moving from a circle to the list finds the same word

### Requirement: Semantic review guide
id: semantic-review-doc
base: f77a9bdbfd67
Dropped: The five triggers are named

`docs/semantic-review.md` SHALL be a concept guide opening with a
`<!-- doc-type: concept -->` comment on its first line, totalling 100 lines or
fewer and passing `docs_lint.py`. It SHALL explain what the semantic review
reads and how it rates what it finds, and SHALL list no command flag and no
JSON field — that lookup material belongs to a reference doc.

The guide SHALL name every `semdiff` subcommand the review uses — `files`,
`diff`, `context`, `change`, `lint` and `doctor` — with one line stating what
each returns. It SHALL state that the engine supplies the facts and the
reviewer supplies the judgement.

The guide SHALL describe the three passes that look past the changed lines:
downstream impact on a changed contract, the values each call site passes, and
the risk-lens triggers. It SHALL name every trigger `semantic-review`'s
`review-risk-lenses` requirement defines, which owns how many there are —
this requirement SHALL NOT fix a count, having previously fixed it at five
after a sixth was added. It SHALL state
that a linter finding is corroboration the reviewer weighs rather than a
review finding in itself.

The guide SHALL state the blocking rule: `high` and `medium` block, and `low`
never does. It SHALL state the exposure floor — an exposed secret, and an
authorization boundary reached without a scope check, always rate `high`.

The guide SHALL describe both paths a review takes: a local run that ends at
the report, and a run against a named pull request that reads prior
dispositions back before posting. It SHALL state that a named pull request is
posted to by default, that the posted findings are left open for that pull
request's owner, and that implementing and resolving them is an opt-in the
invoker asks for. It SHALL state that the review omits a finding answered with
a reasoned reply, that it keeps a finding only a commit cleared, and that a
finding's identity excludes its line number.

The guide SHALL carry exactly one mermaid diagram, of those two paths, showing
the local path ending at the report, the posting path, and the opted-in
disposition path looping back on a later push. It SHALL state the missing-tool behaviour exactly as `semantic-review`'s
`difft-required-docs` requirement states it — that requirement owns it and
requires the guide say the review stops, so this one SHALL NOT restate it.

`docs/copilot-review.md` SHALL link `/s:review` to this guide rather than to a
README anchor.

#### Scenario: The guide passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/semantic-review.md` runs
- **THEN** it exits `0`, and the file is 100 lines or fewer opening with the
  concept marker

#### Scenario: Every subcommand is named
- **WHEN** the guide is inspected
- **THEN** it names `files`, `diff`, `context`, `change`, `lint` and `doctor`,
  each with what it returns

#### Scenario: The blocking rule and the floor are stated
- **WHEN** the guide is inspected
- **THEN** it states that `high` and `medium` block while `low` does not, and
  that an exposed secret and an unguarded authorization boundary always rate
  `high`

#### Scenario: Every trigger is named
- **WHEN** the guide is inspected
- **THEN** it names every risk-lens trigger `review-risk-lenses` defines, and
  this requirement fixes no count of its own

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
- **THEN** exactly one is present, and it shows the local path ending at the
  report and the opted-in disposition path looping back

#### Scenario: The how-to points at the guide
- **WHEN** `docs/copilot-review.md` is inspected
- **THEN** its `/s:review` link resolves to `semantic-review.md`, and its link
  to `docs/copilot-review-reference.md` is unchanged

### Requirement: Semantic review reference
id: semantic-review-reference-doc
base: eaf214c41d9a

`docs/semantic-review-reference.md` SHALL be a lookup reference opening with a
`<!-- doc-type: reference -->` comment on its first line, totalling 250 lines or
fewer and passing `docs_lint.py`. It SHALL open by naming
`docs/semantic-review.md` as its concept guide, and SHALL carry three sections:
the `--json` finding payload, the `lint` configuration key, and the `prior`
verb's output.

The payload section SHALL list every field of a finding — `id`, `severity`,
`category`, `location`, `what`, `why`, `fix`, `status`, `note` and the optional
`suggestion` — and SHALL name every `category` value the two payload
surfaces accept, those surfaces being the enumeration's source and
`semantic-review`'s `review-taxonomy-parity` requirement being what holds
them in agreement. This requirement SHALL NOT restate the enumeration or fix
its size, having previously named ten after `description-drift` made eleven. It SHALL state that `verdict`
is `changes-requested` when any finding is high or medium and `pass` otherwise,
and SHALL state the conditions a `suggestion` must meet to be committed rather
than degraded to prose.

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

#### Scenario: The guide links the reference
- **WHEN** `docs/semantic-review.md` is inspected
- **THEN** it carries a link resolving to `semantic-review-reference.md`
