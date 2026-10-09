# copilot-review-skill

### Requirement: Copilot review skill template
id: skill-template

The plugin SHALL carry a Copilot code-review skill template at
`integrations/copilot/SKILL.md` containing: YAML frontmatter with `name` and
`description` fields; the ownership marker line `<!-- shipd-copilot
v{version} -->` with the literal `{version}` placeholder; instructions that
direct the reviewing agent to run the bundled engine
(`python3 .github/skills/code-review/scripts/semdiff.py`) with its `files`,
`diff`, and `context` subcommands and to reason from that structural JSON
rather than raw file dumps; the severity rubric (`high`/`medium`/`low`) with
the ship-it/fix-required verdict rule (any high or medium finding blocks); an
instruction that the review body ends with a visible verdict line plus the
matching machine-readable marker — `<!-- shipd-verdict: ship-it -->` or
`<!-- shipd-verdict: fix-required -->` — on its own line as the body's last
line, stating that the marker is read from the last non-empty line by exact
equality; a statement that the skill is the review contract for both surfaces
that consume it; a statement that the engine is read-only and degrades to its
text engine when `difft` is unavailable; and documentation that the Copilot
code-review surface exposes no repository-side model selection and that the
verdict marker drives the required `semantic-review` commit status under the
repository's `SHIPD_GATE_FAIL_OPEN` setting.

The template SHALL additionally require the review body to open with a verdict
header and a severity summary table before any per-finding detail, and to keep
each finding's detail brief enough to be read at a glance. It SHALL require the
agent to write a machine-readable findings file beside the body, each finding
carrying its severity, its file path and line range, its prose detail, and —
only where the agent judges the fix confident and expressible as one or more
contiguous whole lines — a replacement for those lines.

The template's severity rubric SHALL state the same `low` definition and the
same impact floor that `semantic-review`'s `review-skill` requirement states
for `SKILL.md`, including the concrete instances that requirement names.
`review-skill` owns that wording; this requirement SHALL NOT restate it, so
the rubric has one source and the template cannot drift from the skill it
mirrors. The template SHALL carry that wording **inline**, because it is
vendored byte-for-byte into a GitHub Actions runner and can read no reference
file.

#### Scenario: Template exists with the placeholder marker
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it contains the literal line `<!-- shipd-copilot v{version} -->`
  and frontmatter `name` and `description` fields

#### Scenario: Template directs the agent to the bundled engine
- **WHEN** the template body is read
- **THEN** it names the `files`, `diff`, and `context` subcommands of the
  bundled `semdiff.py`, the high/medium/low rubric, and the no-model-pin
  documentation

#### Scenario: The marker instruction states last-line equality
- **WHEN** the template's report instructions are read
- **THEN** they require exactly one marker as the body's last line and state
  it is read from the last non-empty line by exact equality

#### Scenario: The report shape is mandated
- **WHEN** the template's report instructions are read
- **THEN** they require a verdict header and a severity summary table ahead of
  any per-finding detail

#### Scenario: The findings file is specified
- **WHEN** the template's report instructions are read
- **THEN** they require a machine-readable findings file whose entries carry
  severity, path, line range, and detail, and carry a replacement only for a
  fix the agent judges confident and expressible as contiguous whole lines

#### Scenario: The template's rubric matches the skill's
- **WHEN** the template's severity rubric is compared with the `low` bullet and
  impact floor in `plugins/s/skills/review/SKILL.md`
- **THEN** the template states the same `low` definition, the same floor, and
  the same concrete instances, with pure style excluded from findings at any
  severity

#### Scenario: This requirement restates no rubric wording
- **WHEN** this requirement's own text is read
- **THEN** it names `review-skill` as the owner of the `low` definition and the
  impact floor rather than reproducing either, so the two cannot disagree

### Requirement: Copilot review setup workflow template
id: setup-workflow-template

The plugin SHALL carry a Copilot code-review environment workflow template
at `integrations/copilot/copilot-code-review.yml` containing: the
ownership marker line `# shipd-copilot v{version}` with the literal
`{version}` placeholder; a single job named `copilot-setup-steps` running
on `ubuntu-latest`; a repository checkout step that is marked
`continue-on-error: true` and carries a step `id`, so a checkout the
runner's token cannot perform (a private repository) never fails the
setup job; and steps that install the prebuilt `difft` release binary
onto the runner's `PATH` (the same release-tarball source `semdiff.py`'s
own installer uses) and install `ripgrep`, each conditioned on the
checkout step's outcome being `success`. If the extracted release archive
contains no `difft` binary, then the difftastic step SHALL fail with a
message naming the problem rather than invoking `install` with an empty
path. The template SHALL NOT reference any secret or
organization-specific value.

#### Scenario: Workflow defines the setup job
- **WHEN** `plugins/s/integrations/copilot/copilot-code-review.yml` is read
- **THEN** it contains the marker line `# shipd-copilot v{version}` and
  exactly one job, named `copilot-setup-steps`, on `ubuntu-latest`

#### Scenario: The checkout is fail-soft and gates the installs
- **WHEN** the template's steps are read
- **THEN** the checkout step carries `continue-on-error: true` and an
  `id`, and the difftastic and ripgrep steps each run only when that
  step's outcome is `success`

#### Scenario: A binary-less archive fails loudly
- **WHEN** the difftastic step's script is read
- **THEN** it tests the located binary path for emptiness and fails with
  a clear message when the archive held no `difft`, never invoking
  `install` with an empty path

#### Scenario: Workflow provisions the diff tooling
- **WHEN** the template's steps are read
- **THEN** one step installs the `difft` release binary onto `PATH` and one
  installs `ripgrep`

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template

The plugin SHALL carry a review-gate workflow template at
`integrations/copilot/copilot-review-gate.yml` that posts a terminal
`semantic-review` commit status for every reviewed head, reads the verdict
by scanning the review text backwards for the last line equal to a verdict
marker, honours the repository's `SHIPD_GATE_FAIL_OPEN` setting for a
marker-less review, and keeps the reviewer's credential and the repository
credential in separate steps so the reviewing agent holds no credential able
to post a status, comment, or push.

The backwards scan SHALL compare whole lines for equality and SHALL examine
at most the last 200 lines, so a marker quoted mid-sentence or inside the
reviewer transcript's own tool-call log is never read as a verdict and a
maximal body cannot make the scan walk the whole text. Taking the last
non-empty line instead fell open whenever the Copilot CLI streamed its
session narration after the report: the gate then posted `success` carrying
a description saying no verdict was parsed, reporting a pass over a review
it had not read. One residual window remains and SHALL be documented in the
workflow: a bare marker standing alone on its own line inside trailing
narration is still read as the verdict.

Where the workflow installs difftastic for the review engine, it SHALL
request a pinned release version rather than the unversioned
`releases/latest/download/` asset name, and SHALL fail the step when the
download itself fails. Difftastic stopped publishing the unversioned asset
after 0.65.0, so the unpinned fetch 404s and kills the job before the
reviewer starts, leaving `semantic-review` pending forever on a repository
that requires it.

The reviewer's instructions SHALL be pinned by overwriting the reviewed
checkout's own `.github/skills/code-review/SKILL.md` with the base ref's
copy, so the Copilot CLI's skill discovery finds the pinned contract without
being asked to prefer it. Materializing that copy elsewhere and instructing
the reviewer to read it leaves the pinning advisory: the CLI discovers the
workspace copy on its own, so a change editing the review rules could still
be reviewed under the rules it is asking for. The reviewer step SHALL also
pass `--add-dir` for the directory holding the findings file it must write,
which `--allow-all-tools` alone does not bring inside its sandbox.

If the reviewer produced no output at all — the gate's own reviewer writing no
review body, or the poll reaching its bound with no review of the head — then
the workflow SHALL leave the `semantic-review` status `pending` and SHALL exit
non-zero, and its message SHALL name the reviewer step's log as where the cause
is reported. Nothing was judged, so no verdict is invented; the job's exit code
is what distinguishes a reviewer that broke from one that is merely slow.
Exiting zero on those paths reported a passing run over a review that never
happened and left the pull request blocked on a status that would never arrive.
`SHIPD_GATE_FAIL_OPEN` SHALL NOT be consulted on those paths: it governs a
review that ran and carried no verdict marker, which is a different condition
from one that never ran. Where instead the poll observes that the pull
request's head has moved on, the workflow SHALL exit zero, because that run is
not stalled — the newer push's run owns the gate.

Where the gate's own reviewer produced the review, the workflow SHALL publish
it as a pull-request review rather than as an issue comment, submitting the
event `COMMENT`, carrying the review body and one anchored inline comment per
finding whose severity is `high` or `medium` and whose path and line range the
workflow itself verifies against the diff it computed. That diff SHALL cover
every file the pull request changed, the workflow paginating the changed-files
read rather than taking a single page of it: a short read is indistinguishable
downstream from a finding that named a path the pull request never touched, so
a truncated diff silently withholds the anchoring a finding was computed for
instead of reporting that it could not be placed. A finding naming a path
or range outside that diff, and every finding whose severity is `low`, SHALL be
folded into the body as prose rather than anchored — an inline comment opens a
review thread, and a repository requiring conversation resolution would
otherwise let a `low` finding block a merge the rubric says it never blocks.
Where an anchored finding also carries a replacement, its inline comment SHALL
include that replacement as a committable `suggestion` block.

#### Scenario: The changed-files read is paginated
- **WHEN** the posting step's changed-files read is inspected
- **THEN** it carries the option that fetches every page, so the diff map is
  not capped at a single page's worth of files

#### Scenario: A reviewer that produced nothing fails the job
- **WHEN** the gate's own reviewer writes no review body
- **THEN** the `semantic-review` status is left `pending`, the job exits
  non-zero, and its message names the reviewer step's log

#### Scenario: A poll that found no review fails the job
- **WHEN** the poll reaches its bound without finding a review of the head
- **THEN** the `semantic-review` status is left `pending` and the job exits
  non-zero

#### Scenario: A moved head is a handoff, not a failure
- **WHEN** the poll observes that the pull request's head has moved on
- **THEN** the job exits zero, posting nothing further

#### Scenario: The gate's own review is posted as a review
- **WHEN** the workflow's own reviewer produces a review body for a pull
  request
- **THEN** it is published through the pull-request reviews API with the event
  `COMMENT`, not as an issue comment

#### Scenario: A verified high or medium finding is anchored
- **WHEN** a `high` or `medium` finding's path and line range are present in
  the diff the workflow computed
- **THEN** it is posted as an inline comment on that range

#### Scenario: A low finding is never anchored
- **WHEN** a `low` finding's path and line range are present in that diff
- **THEN** no inline comment is posted for it and it is folded into the review
  body as prose

#### Scenario: An unverifiable finding is not anchored
- **WHEN** a finding names a path or line range absent from that diff
- **THEN** it is folded into the review body as prose and no inline comment is
  posted for it

#### Scenario: A confident replacement becomes committable
- **WHEN** an anchored finding carries a replacement
- **THEN** its inline comment contains a `suggestion` fenced block carrying
  that replacement

#### Scenario: The credentials stay separated
- **WHEN** the template's steps are read
- **THEN** the reviewer step binds only the reviewer token and the posting
  step binds only the workflow token

#### Scenario: Template carries the marker, triggers, permissions, and concurrency
- **WHEN** the installed workflow template is read
- **THEN** it carries the version marker comment, triggers on `pull_request`
  and `pull_request_review`, declares `contents: read`, `statuses: write` and
  `pull-requests: write`, and runs under a per-pull-request concurrency group
  that cancels a superseded run

#### Scenario: Reviewer instructions come from the base ref
- **WHEN** the CLI reviewer prepares its prompt
- **THEN** the reviewer skill is materialized from the base ref, a base that
  cannot be resolved fails the step, and the head's copy is used only where the
  file is confirmed absent at the base

#### Scenario: The CLI install is pinned
- **WHEN** the provisioning step installs the reviewer CLI
- **THEN** it installs an exact pinned version rather than a floating tag

#### Scenario: The posting step's environment is credential-isolated
- **WHEN** the posting step runs after the reviewer step
- **THEN** it invokes its tools by absolute path, re-binds the strictness
  setting from repository variables in its own step environment, and reads the
  review text from a workspace file rather than an inherited variable

#### Scenario: The classified text is never piped nor env-passed
- **WHEN** the workflow classifies a review body on the CLI or poll path
- **THEN** the body reaches the classifier as a file read rather than a pipe,
  and the verdict is extracted by bounded in-shell string comparison

#### Scenario: Marker verdicts map to terminal status states
- **WHEN** a review's last non-empty line is the fix-required marker, and
  separately the ship-it marker
- **THEN** the `semantic-review` status is `failure` for the first and
  `success` for the second

#### Scenario: Strict mode posts no status but still posts the comment
- **WHEN** the fail-open setting is explicitly `false` and a reviewer run
  produces no verdict marker
- **THEN** no `semantic-review` status is posted while the CLI path still posts
  its review comment

#### Scenario: Pull-request events post pending first
- **WHEN** the workflow runs on a `pull_request` event
- **THEN** a `pending` `semantic-review` status is posted before the reviewer
  runs

#### Scenario: The review-event bridge guards reviewer and head commit
- **WHEN** the workflow runs on a `pull_request_review` event
- **THEN** it acts only where the review's author is the configured reviewer
  and its commit is the pull request's current head

#### Scenario: The CLI fail-open description names its source
- **WHEN** the gate's own CLI review produces no verdict marker and the
  fail-open setting is anything other than `false`, so the fail-open default
  stands
- **THEN** the posted `success` description names the CLI review as what
  produced no marker, distinguishing it from the other paths' shared wording

#### Scenario: A marker above trailing narration is still the verdict
- **GIVEN** a review body whose verdict marker is followed by the reviewer's
  own narration about writing its findings file
- **WHEN** the workflow classifies the reviewed text
- **THEN** the marker is read as the verdict, not treated as absent

#### Scenario: A quoted marker is not a verdict
- **GIVEN** a review body quoting a verdict marker mid-sentence and inside a
  transcript tool-call line, with no marker alone on its own line
- **WHEN** the workflow classifies the reviewed text
- **THEN** no verdict is parsed

#### Scenario: The difftastic download is pinned and guarded
- **WHEN** the workflow's difftastic install step is inspected
- **THEN** it requests a pinned release version rather than
  `releases/latest/download/`, and a failed download fails the step

#### Scenario: Skill discovery finds the pinned contract
- **WHEN** the reviewer step runs on a pull request that edits
  `.github/skills/code-review/SKILL.md`
- **THEN** the checkout's copy of that path holds the base ref's content, so
  the reviewed change cannot govern its own review

#### Scenario: The findings directory is inside the reviewer's sandbox
- **WHEN** the reviewer invocation is inspected
- **THEN** it passes `--add-dir` for the directory holding the findings file

### Requirement: Copilot skill clean-verdict wording
id: copilot-clean-wording

The Copilot review skill template SHALL instruct the reviewing agent to write `No problems found.` in place of the severity summary table when the review carries no findings, SHALL state that the gate workflow's posting step closes the posted body with the `Reviewed N files, +A -D lines.` stat line, and SHALL instruct the agent not to write that line itself. The template SHALL NOT carry the retired `No findings.` sentence.

#### Scenario: The template mandates the wording
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it contains `No problems found.`, contains `Reviewed N files, +A -D lines.`, and does not contain `No findings.`

### Requirement: Gate workflow posted-body footer
id: gate-body-footer

Where the gate's own reviewer produced the review, the review-gate workflow's posting step SHALL append one stat line, `Reviewed N files, +A -D lines.`, to the body it posts, counted from the changed-files read that step performs itself, and SHALL fold it above the verdict marker so the marker remains the last line equal to a marker. The line's format SHALL match `review_footer` in `review_gate.py` for every file list, including the singular noun, the count-less form, and the empty list, so a review reads the same whichever surface posted it. When the changed-files read failed, no footer SHALL be appended.

#### Scenario: Workflow footer matches the poster
- **WHEN** the posting step's `footer` function is executed from the workflow source against a file list
- **THEN** it returns an empty block when `review_footer` returns none, and otherwise a block whose last line equals `review_footer`'s line

#### Scenario: Footer stays above the marker
- **WHEN** the posting step folds the footer into a body ending in a verdict marker
- **THEN** the marker is still the body's last non-blank line

#### Scenario: Unreadable diff appends nothing
- **WHEN** the changed-files file is empty or not a list
- **THEN** the posting step appends no `Reviewed` line

### Requirement: Fast-pass marker and workflow arming
id: fast-pass-workflow-arming

The Copilot code-review skill template at `integrations/copilot/SKILL.md`
SHALL instruct the reviewing agent to emit the line
`<!-- shipd-fast-pass: eligible -->` directly above the verdict marker, and
only where the reviewed pull request carries a completed shipd change
directory whose every delta scenario the agent judged met. The template SHALL
state that the verdict marker remains the body's last line, so the fast-pass
line never displaces it and the gate's backwards verdict scan — which breaks on
the first verdict marker it meets — classifies exactly as before.

The review-gate workflow template at
`integrations/copilot/copilot-review-gate.yml` SHALL read the repository
Actions variable `SHIPD_FAST_PASS` from `vars` in the step environment, the way
it already reads `SHIPD_GATE_FAIL_OPEN`, and SHALL arm auto-merge with
`gh pr merge --auto --squash --delete-branch` only where **all** of these hold:
the variable reads exactly `true`; the classified state is `success`; that
state came from a matched `ship-it` verdict marker rather than from the
marker-less fail-open path; and the reviewed body carries the fast-pass line,
found by the same whole-line equality scan bounded to the final 200 lines. The
arming SHALL run after the commit status is posted, and SHALL log which
condition was unmet where it does not run.

If the arming call fails, then the workflow SHALL log the failure and SHALL NOT
fail the job — the posted status is the gate, and a refused merge arming is not
a broken review. The poll fallback SHALL never arm the fast-pass, because
GitHub's own reviewer authors no shipd marker and so can satisfy neither the
verdict nor the fast-pass condition.

#### Scenario: The template pins the fast-pass line above the verdict
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it names `<!-- shipd-fast-pass: eligible -->`, places it directly
  above the verdict marker, and states the verdict marker is still the last
  line

#### Scenario: An eligible reviewed body arms the merge
- **GIVEN** `SHIPD_FAST_PASS` reads `true`
- **WHEN** the workflow classifies a body whose matched verdict marker is
  `ship-it` and which carries the fast-pass line
- **THEN** it posts `success` and runs `gh pr merge --auto --squash
  --delete-branch`

#### Scenario: A fail-open pass arms nothing
- **GIVEN** `SHIPD_FAST_PASS` reads `true` and `SHIPD_GATE_FAIL_OPEN` is unset
- **WHEN** the workflow classifies a body carrying no verdict marker and posts
  `success` fail-open
- **THEN** no merge arming is run and the step logs that no verdict marker was
  matched

#### Scenario: An unset variable arms nothing
- **GIVEN** `SHIPD_FAST_PASS` is unset
- **WHEN** the workflow classifies a `ship-it` body carrying the fast-pass line
- **THEN** no merge arming is run

#### Scenario: A failed arming does not fail the job
- **WHEN** the merge arming call exits non-zero
- **THEN** the workflow logs the failure and the job's exit code is unchanged
