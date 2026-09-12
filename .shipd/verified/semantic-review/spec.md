# semantic-review

### Requirement: Structural diff subcommand
id: structural-diff

The system SHALL provide `semdiff diff <base> [<head>]` emitting a single
JSON object: resolved endpoint metadata (`base`, `head`, `mode` —
working-tree when head is omitted, merge-base three-dot by default with a
head, two-dot under `--linear`), a per-file list with `path`, `language`,
`kind` (added/deleted/modified), token-level `hunks`, and a `summary` with
file/hunk/kind counts, languages, and a best-effort `signature_changes`
estimate. When reviewing the working tree, untracked files SHALL be
included; whole-file adds/deletes with no hunks SHALL carry a `lines`
count; whitespace-only content edits SHALL be filtered out. Kind
classification SHALL distinguish a file that is present at an endpoint
with empty content from a file absent at that endpoint: emptying an
existing file classifies `modified`, never `deleted`, and adding content
to an existing empty file classifies `modified`, never `added`.

Every emitted hunk `line` SHALL be 1-based, counting the first line of the
file as line 1, under both the difftastic engine and the text engine, so
one file position carries one number whatever engine ran. Where the
difftastic engine reports a 0-based line, the system SHALL normalize it
before emission, and the signature-change estimate SHALL index the file
body consistently with the normalized numbering.

Where a file's `kind` is `added` and it carries no hunks, the entry SHALL
additionally carry `content` — the file's body, one line per line, each
prefixed with its 1-based line number — and a `content_truncated` boolean.
The system SHALL cap that body at 600 lines and 60 000 bytes, setting
`content_truncated` true when either cap elides part of the body. Both
engines SHALL attach it.

#### Scenario: Working-tree review against a base
- **WHEN** `semdiff diff main` runs in a repo with one modified tracked
  file and one untracked file
- **THEN** the JSON reports `mode: working-tree` and both paths, with kinds
  `modified` and `added`

#### Scenario: PR-style head comparison
- **WHEN** `semdiff diff main feature` runs
- **THEN** the JSON reports `mode: merge-base` with the resolved
  `merge_base`, and the after-side content comes from the `feature` ref,
  not the checkout

#### Scenario: Empty is not absent
- **WHEN** `semdiff diff HEAD` runs after emptying one committed non-empty
  file and writing content into another committed empty file
- **THEN** both files report kind `modified` — neither `deleted` nor
  `added`

#### Scenario: Both engines agree with git on a line number
- **WHEN** `semdiff diff HEAD` runs over a file whose tenth line is the
  only edited line, once with difftastic available and once without
- **THEN** the after-side hunk reports `line` 10 in both runs

#### Scenario: An added file carries its numbered body
- **WHEN** `semdiff diff HEAD` runs over a newly added three-line file
- **THEN** the entry carries `content` whose lines are prefixed `1`, `2`
  and `3`, and `content_truncated` is false

#### Scenario: An oversized added file is truncated, not dropped
- **WHEN** `semdiff diff HEAD` runs over a newly added file of more than
  600 lines
- **THEN** the entry carries `content` of 600 lines and
  `content_truncated` true

### Requirement: Text-engine degradation
id: text-fallback

If the `difft` binary is unavailable, then `semdiff diff` SHALL degrade to
a structural-text engine that parses `git diff` unified output into the
same JSON shape, stamping `engine: "text"` on affected file entries and in
the summary (`engine: "difft"` when syntax-aware), and SHALL NOT exit
non-zero solely because difftastic is missing. If difftastic output fails
to parse for a single file, then only that file SHALL fall back to the
text engine.

#### Scenario: Missing difft degrades instead of blocking
- **WHEN** `semdiff diff main` runs on a machine without `difft`
- **THEN** it exits zero and emits the diff JSON with `engine: "text"`

### Requirement: Cohort grouping subcommand
id: cohort-grouping

The system SHALL provide `semdiff files <base> [<head>]` grouping changed
paths into architectural cohorts using segment-aware rules (contracts,
database, api, frontend, tests; plus shipd-aware groups for content-dir
spec artifacts and plugin skills), falling back to the path's top-level
directory, and emitting JSON with the cohort map and file/cohort counts.

#### Scenario: Segment-aware grouping
- **WHEN** `semdiff files main` runs over changes touching
  `plugins/s/skills/review/SKILL.md` and `.shipd/planned/x/plan.md`
- **THEN** the two paths land in the skills and specs cohorts, not in a
  generic top-level bucket

### Requirement: Reference context subcommand
id: reference-context

The system SHALL provide `semdiff context <symbol> [--path] [--lang]`
returning candidate references as JSON via ripgrep when available, else
`git grep`, and the output SHALL carry an explicit note that matches are
best-effort candidates, never a complete call graph.

#### Scenario: Fallback lookup without ripgrep
- **WHEN** `semdiff context parse_spec` runs where `rg` is absent
- **THEN** matches come from `git grep` with file, line, and text, and the
  best-effort note is present

### Requirement: Planned-change review bridge
id: change-bridge

The system SHALL provide `semdiff change <name>` aggregating a planned shipd
change's review context as one JSON object: the change status, per-delta
entries (operation, capability, requirement id and text, scenario texts),
task checkbox states with progress counts, the change's lint findings, and
best-effort impact files extracted from `plan.md`. It SHALL resolve the
content directory through the engine's layered configuration and reuse the
engine's parser in-process, and SHALL exit non-zero with a clear message
when the change does not exist under `planned/`.

#### Scenario: Aggregated change context
- **WHEN** `semdiff change my-change` runs against a lint-clean planned
  change with two delta requirements and three tasks, one checked
- **THEN** the JSON lists both requirements with their scenarios and
  reports task progress 1 of 3 with no lint findings

#### Scenario: Unknown change fails clearly
- **WHEN** `semdiff change nope` runs and `planned/nope/` does not exist
- **THEN** it exits non-zero naming the missing change

### Requirement: Dependency doctor with tiered installer
id: doctor-provisioning

The system SHALL provide `semdiff doctor` reporting tool availability —
git required; difft recommended (absence degrades review, never blocks);
rg and gh optional — with actionable hints, exiting non-zero only when a
required tool is missing. Where `--fix` is given, the system SHALL install
difftastic by trying Homebrew, then cargo, then a prebuilt release binary
into the plugin's `bin/` (else `~/.local/bin`); network access SHALL occur
only under `--fix`. The release-binary path SHALL extract only an archive
member that is a regular file: a member named `difft` that is a symlink or
any other non-regular type SHALL be refused with a clear error and nothing
extracted.

#### Scenario: Doctor reports without installing
- **WHEN** `semdiff doctor` runs without `--fix` on a machine missing difft
- **THEN** difft is reported as recommended-missing with an install hint,
  no network access occurs, and the exit code is zero when git is present

#### Scenario: A non-regular archive member is refused
- **WHEN** the release-binary installer encounters an archive whose only
  `difft` member is a symlink
- **THEN** nothing is extracted and the failure names the non-regular
  member, while an archive with a regular-file `difft` member extracts it

### Requirement: Semantic review skill
id: review-skill

The plugin SHALL provide an `/s:review` skill that reviews local changes
against a base ref (default `main`, or a named base/head pair) by mapping
cohorts foundational-first, reasoning over the semdiff structural diff
rather than raw file dumps, chasing changed signatures through `semdiff
context`, and reporting findings by cohort, each with location, what, why,
a concrete fix, and a severity of high, medium, or low. The rendered
report SHALL carry an effort score (1–5), a findings header reading
`## Findings: ✅ Ship it` when no finding is high or medium and
`## Findings: ❌ Fix required` otherwise, a summary table rating findings
with 🔴/🟠/🟡 severity dots, a collapsible walkthrough, and an explicit
list of what could not be verified. Emoji SHALL appear only at those two
sites and, in the posted summary comment, the ☕ of the
`**☕ shipd** semantic review` brand line — the three sanctioned sites;
branding is shipd-only, and the skill SHALL NOT modify the repo.

The skill SHALL additionally carry three judgement passes. It SHALL treat a
changed limit, bound, timeout, retry count, buffer size or threshold as a
contract change and chase its consumers through `semdiff context`, and it
SHALL compare two or more parallel implementations the diff touches against
each other, naming any hardening applied to one and not the other. It SHALL
judge every function, class, guard or helper the diff introduces against its
own stated purpose — whether it measures the quantity its limit governs,
whether an escape hatch lapses its guarantee, whether it terminates cheaply
on hostile input, and whether its boundaries and its doc comment agree. It
SHALL run a test-coverage check over each finding it writes, at every
severity, asking whether an existing test would fail if that defect
regressed, and SHALL raise any gap as its own finding in a `test-coverage`
cohort, which the `--json` finding shape SHALL accept.

The skill SHALL review an added file's inlined `content` with the rigour it
applies to a hunk, and SHALL NOT pass such a file on its path and line count
alone. Where `content_truncated` is true, it SHALL read the remainder.

The skill SHALL bind its rendered report and its posted summary comment to
the shipd documentation standard, referencing that standard by path rather
than restating any rule, and SHALL name one finding a "finding" throughout.
The harness command body for the review SHALL carry the same three
judgement passes as the skill, so the two surfaces do not drift.

#### Scenario: Blocking verdict matches severities
- **WHEN** a review yields one medium and one low finding
- **THEN** the header reads `## Findings: ❌ Fix required` and the summary
  table rates them 🟠 and 🟡

#### Scenario: Machine mode for the gate
- **WHEN** the skill is invoked with `--json`
- **THEN** it emits only a JSON object — verdict `changes-requested` iff
  any finding is high or medium, else `pass`, with findings, optional
  spec_coverage, and could_not_verify arrays — and no emoji or prose

#### Scenario: The skill binds the standard by reference
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it names `skills/document/references/standard.md` by path and
  restates none of that file's numbered core rules

#### Scenario: The harness body carries the same passes
- **WHEN** `plugins/s/harness/bodies/review.md` is inspected
- **THEN** it instructs the reviewer to chase changed constants, to compare
  parallel sites against each other, to judge newly added code on its own
  terms, and to check test coverage per finding

### Requirement: Spec-aware verification
id: spec-aware-review

Where a planned change is named by the user or exactly one change exists
under `planned/`, the skill SHALL verify the diff against `semdiff change`
output: classify every delta scenario as Met (citing the satisfying hunk),
Unmet, or Can't-tell; report each unmet scenario as a high-severity
spec-coverage finding; flag checked tasks with no supporting change in the
diff; and surface behavioral changes no requirement or task describes as
observations, not blockers.

#### Scenario: Unmet scenario tops the findings
- **WHEN** a delta scenario's behavior is absent from the structural diff
- **THEN** the review reports it as a high-severity spec-coverage finding
  and the verdict is Fix required

### Requirement: Engine test coverage in ci
id: review-test-coverage

The semdiff script SHALL be covered by a unittest suite under
`plugins/s/skills/review/tests/` that builds fixture git repositories in
temporary directories, skips difft-dependent assertions when difftastic is
absent, performs no network access, and is discovered by the `ci`
workflow.

#### Scenario: ci discovers the review suite
- **WHEN** the ci workflow runs on a runner without difftastic
- **THEN** the review tests run via unittest discovery and pass,
  exercising the text engine

### Requirement: PR posting of a review verdict
id: gate-poster

`review_gate.py post <pr> --from <json|->` SHALL publish a `/s:review --json`
object to the named pull request via `gh`: upserting a single summary comment
identified by the hidden marker `<!-- shipd-semantic-review -->` (editing the
existing marker comment in place on re-runs, and recognizing the legacy marker
`<!-- am-semantic-review -->` on lookup while writing only the current one),
posting inline comments only for findings whose `location` anchors to a
RIGHT-side commentable line of the pull request diff, folding unanchorable
findings into the summary, retrying once with no inline comments if the review
POST is rejected, submitting that review with the event `COMMENT`, and setting
a commit status with context `semantic-review` on the pull request's head SHA.

Where a finding declares its fix confident and supplies a replacement covering
one or more contiguous whole lines that anchor to a RIGHT-side commentable
line, its inline comment SHALL carry that replacement as a committable
`suggestion` block so the fix can be applied without retyping. A finding whose
replacement is absent, covers part of a line, spans a discontiguous range, or
does not anchor SHALL render as prose instead. Emitting a suggestion SHALL NOT
change the comment's leading severity marker, and the `--json` mode SHALL stay
free of emoji and prose.

#### Scenario: A confident whole-line fix becomes committable
- **WHEN** a finding declares its fix confident with a replacement covering
  contiguous whole lines that anchor to the diff
- **THEN** its inline comment contains a `suggestion` fenced block carrying
  that replacement

#### Scenario: A multi-line replacement is supported
- **WHEN** a confident finding's replacement covers more than one contiguous
  whole line
- **THEN** the suggestion block carries every one of those lines

#### Scenario: An unanchorable fix stays prose
- **WHEN** a finding declares its fix confident but its location does not
  anchor to a RIGHT-side commentable line
- **THEN** it is folded into the summary and carries no suggestion block

#### Scenario: A partial-line fix stays prose
- **WHEN** a confident finding's replacement covers part of a line rather than
  whole lines
- **THEN** its comment carries no suggestion block

#### Scenario: The review is submitted as a comment
- **WHEN** the poster publishes a review for any verdict
- **THEN** the submitted event is `COMMENT`

#### Scenario: The severity marker is unchanged by a suggestion
- **WHEN** an inline comment carries a suggestion block
- **THEN** its body still opens with the shared severity marker that
  `parse_severity` reads

#### Scenario: Pass verdict posts green
- **WHEN** `post` publishes a `pass` verdict to a pull request that carries no
  marker comment yet
- **THEN** a summary comment carrying the marker is created and the head SHA's
  `semantic-review` status state is `success`

#### Scenario: Red verdict anchors findings inline
- **GIVEN** a `changes-requested` verdict carrying one finding that anchors to
  the diff and one that does not
- **WHEN** `post` publishes it
- **THEN** the anchoring finding becomes an inline comment, the other is folded
  into the summary, and the status state is `failure`

#### Scenario: Re-post updates instead of stacking
- **WHEN** `post` runs twice against the same pull request
- **THEN** exactly one marker comment remains, the second run having edited the
  first rather than adding another

#### Scenario: Legacy-marker summary is updated, not duplicated
- **GIVEN** a pull request whose summary comment carries the legacy marker
  `<!-- am-semantic-review -->`
- **WHEN** `post` runs against it
- **THEN** that comment is edited in place, its new body carries the current
  marker, and exactly one summary remains

#### Scenario: High-only greens over mediums
- **WHEN** `post --disposition high-only` publishes a verdict whose findings
  are medium and low only
- **THEN** the status state is `success`, its description names the acting
  scope, and the summary carries both findings and a `Disposition:` line

#### Scenario: High-only stays red on a high
- **WHEN** `post --disposition high-only` publishes a verdict carrying a
  high-severity finding
- **THEN** the status state is `failure`

#### Scenario: None is always green and stays honest
- **WHEN** `post --disposition none --model <tier>` publishes a verdict
  carrying a high-severity finding
- **THEN** the status state is `success` and the summary still carries that
  finding, a `Disposition:` line, and a `Model:` line naming the tier verbatim

### Requirement: Required-check protection verb
id: required-check-protect

`review_gate.py protect` SHALL read the default branch's protection,
union `semantic-review` into the required status checks, set
`required_conversation_resolution` to true, and write back preserving
`strict` and every other protection field; `protect --remove` SHALL
remove the check and clear the conversation-resolution requirement the
same way.

The write SHALL express the required status checks as `checks`, carrying one
entry per context with an explicit `app_id` of null, rather than as the legacy
`contexts` field. A null `app_id` states that any source may report the check,
which is what lets a status posted by a person — a review produced by hand when
the configured reviewer could not run — satisfy the requirement. Writing
`contexts` leaves that to GitHub's own translation, so the same outcome held
only by accident and said nothing about the intent; a branch whose check is
pinned to one app silently ignores every status from any other source.

If the protection read reports the branch as not protected (the
404 an unprotected branch returns), then `protect` SHALL create the
protection instead of failing: a write whose required status checks are
`strict` false and one `semantic-review` check with a null `app_id`, with
conversation resolution required and every other protection field null or
absent. Any other protection-read failure SHALL still fail the verb. Both
directions SHALL be idempotent — already in the desired
state means no write and exit zero — and the verb SHALL print the
resulting contexts and conversation-resolution state.

#### Scenario: The write names any app as the reporting source
- **WHEN** `protect` builds its protection write
- **THEN** the body carries a `checks` list whose `semantic-review` entry has
  an `app_id` of null, and carries no legacy `contexts` field

#### Scenario: Protect adds the check and the resolution requirement
- **GIVEN** required contexts `["ci"]` and conversation resolution off
- **WHEN** `protect` runs
- **THEN** the required checks become `ci` and `semantic-review`, conversation
  resolution is required, and `strict` is preserved

#### Scenario: Remove restores the prior gate
- **WHEN** `protect --remove` runs on a protected branch
- **THEN** `semantic-review` leaves the required checks and conversation
  resolution is no longer required

#### Scenario: Unprotected branch gains minimal protection
- **GIVEN** a default branch whose protection read returns the
  not-protected 404
- **WHEN** `protect` runs
- **THEN** protection is created requiring `semantic-review` with `strict`
  false and a null `app_id`, conversation resolution required, and the verb
  prints the resulting state

#### Scenario: Other read failures still fail
- **WHEN** the protection read fails for any reason other than the
  not-protected 404
- **THEN** the verb fails naming the read error, and no write is performed

### Requirement: Skill post-to-PR flow
id: skill-post-flow

Where the user explicitly asks for a review to be posted, the `/s:review`
skill SHALL run the review, emit the machine verdict, and publish it via the
poster, passing through the disposition scope and model tier when the invoker
supplied them (defaults: scope `all`, no tier). The skill SHALL then
disposition findings by scope. Under `all`, the flow SHALL run the full loop
over every posted finding regardless of severity: implement the suggestion
when it is correct — by editing, committing and pushing, or by the finding's
committable suggestion having been applied on the pull request, which counts
as the same implement branch and needs no separate reply — otherwise reply on
the finding's thread with the concrete reason via the gate's reply verb, never
leaving a finding with neither. Under `high-only`, the flow SHALL implement (or
push back with a reasoned reply) only the high-severity findings, re-reviewing
and re-posting after any push, and SHALL then run the gate's autoreply verb so
the remaining threads carry disposition evidence. Under `none`, the flow SHALL
perform no per-finding judgment and SHALL run the autoreply verb over every
gate thread. Every scope SHALL finish by running the gate's resolve verb and
reporting the posted status state, the summary comment URL, the acting scope
when it is not `all`, and the unresolved count, which SHALL be zero on a
completed disposition.

#### Scenario: An applied suggestion needs no reply
- **WHEN** a posted finding's committable suggestion has been applied on the
  pull request and the disposition loop runs under scope `all`
- **THEN** that finding is treated as implemented, no reply is required on its
  thread, and the completed disposition still reports an unresolved count of
  zero

#### Scenario: An unimplemented finding still needs a reason
- **WHEN** a posted finding is neither implemented nor carries an applied
  suggestion
- **THEN** the flow replies on its thread with the concrete reason before
  resolving

#### Scenario: Sensible suggestion is implemented before merge
- **WHEN** a posted finding's fix is correct and the disposition loop runs
  under scope `all`
- **THEN** the fix is edited, committed and pushed, and the review is re-run
  and re-posted against the new head

#### Scenario: High-only spends judgment only on highs
- **GIVEN** a posted review carrying one high finding and two medium findings
- **WHEN** the disposition loop runs under scope `high-only`
- **THEN** the high finding is implemented or answered individually, the
  autoreply verb covers the medium threads, and the resolve verb reports an
  unresolved count of zero

#### Scenario: None costs no disposition judgment
- **WHEN** the disposition loop runs under scope `none`
- **THEN** no finding receives an individually authored disposition, the
  autoreply verb covers every gate thread, and the resolve verb reports an
  unresolved count of zero

### Requirement: Poster test coverage in ci
id: gate-test-coverage

The `review_gate.py` script SHALL be covered by a unittest suite under
`plugins/s/skills/review/tests/` that injects a fake `gh` command seam,
performs no network access, and covers marker upsert versus create, inline
anchor computation from patch text, status state mapping including the
per-disposition-scope mapping and provenance lines, the no-inline
fallback, protect add/remove idempotency, and the autoreply verb's
severity selection, idempotent re-run, and round-trip between the inline
body renderer and the severity parser; the suite SHALL be discovered by
the existing `ci` review-tests step.

#### Scenario: ci discovers the poster suite
- **WHEN** the ci workflow's review test step runs
- **THEN** the poster tests run via unittest discovery with no network
  access and pass

### Requirement: Finding-thread reply verb
id: thread-reply-verb

`review_gate.py reply <pr> <comment-id> --body <text>` SHALL post a reply
onto the finding thread rooted at the given review comment, through the
same injectable `gh` seam as the poster, and SHALL print the created
reply's URL. An unknown PR or comment id SHALL exit non-zero.

#### Scenario: Push-back lands on the thread
- **WHEN** `reply 54 12345 --body "Deferred: pagination cap is documented"`
  runs
- **THEN** the thread rooted at comment 12345 gains that reply and its URL
  prints

### Requirement: Evidence-gated thread resolution
id: thread-resolution-verb

`review_gate.py resolve <pr>` SHALL resolve only review threads whose root
comment the gate authored, and only those carrying disposition evidence —
a reply exists on the thread, or the PR gained a commit after the thread
was created. Threads without evidence SHALL be listed as undispositioned
and the verb SHALL exit non-zero, resolving nothing else silently.
`resolve <pr> --check` SHALL mutate nothing, print `unresolved=<n>`
counting unresolved gate-authored threads, and exit zero only when the
count is zero. Human-authored threads SHALL never be touched.

#### Scenario: Replied thread resolves
- **GIVEN** a gate-authored thread carrying a push-back reply
- **WHEN** `resolve` runs
- **THEN** that thread is resolved

#### Scenario: Undispositioned thread refuses
- **GIVEN** a gate-authored thread with one comment and no later commit
- **WHEN** `resolve` runs
- **THEN** the thread is listed as undispositioned, left unresolved, and
  the exit code is non-zero

#### Scenario: Check counts without mutating
- **GIVEN** two unresolved gate-authored threads
- **WHEN** `resolve --check` runs
- **THEN** `unresolved=2` prints, nothing is resolved, and the exit code
  is non-zero

#### Scenario: Human threads are untouched
- **WHEN** `resolve` runs on a PR carrying an unresolved human-authored
  thread
- **THEN** that thread is neither resolved nor counted

### Requirement: Auto-disposition reply verb
id: auto-disposition-verb

`review_gate.py autoreply <pr> --disposition <scope>` SHALL, through the
same injectable `gh` seam as the poster, post a canonical policy reply
onto gate-authored, unresolved finding threads that carry no reply yet,
where `<scope>` is `high-only` or `none`: under `high-only` it SHALL
reply only to threads whose root comment's severity — parsed from the
gate's own inline-body format, whose leading severity marker SHALL be
shared as one constant with the body renderer — is `medium` or `low`,
leaving `high` and unparseable roots untouched and reporting them; under
`none` it SHALL reply to every such thread without consulting severity.
The default reply body SHALL name the acting disposition scope and MAY be
overridden with `--body <text>`. The verb SHALL print `replied=<n>`,
SHALL skip threads already carrying a reply so re-runs are idempotent,
SHALL never touch human-authored threads, and SHALL exit zero on a
successful pass.

#### Scenario: High-only replies below the threshold
- **GIVEN** unreplied gate-authored threads rooted at one high, one
  medium, and one low finding comment
- **WHEN** `autoreply <pr> --disposition high-only` runs
- **THEN** the medium and low threads each gain a reply naming the
  policy, the high thread is untouched, and `replied=2` prints

#### Scenario: None replies to everything
- **WHEN** `autoreply <pr> --disposition none` runs over three unreplied
  gate-authored threads of mixed severity
- **THEN** all three threads gain the policy reply and `replied=3` prints

#### Scenario: Re-run is idempotent
- **GIVEN** a thread already carrying an autoreply
- **WHEN** `autoreply <pr> --disposition none` runs again
- **THEN** that thread gains no second reply and `replied=0` prints

#### Scenario: Unparseable root is left for judgment
- **GIVEN** a gate-authored thread whose root body does not start with
  the gate's severity marker
- **WHEN** `autoreply <pr> --disposition high-only` runs
- **THEN** the thread is untouched and reported as unparsed

### Requirement: Summary comment brand mark
id: summary-brand-mark

When `review_gate.py post` renders the marker-tagged summary comment, the system SHALL open the comment's visible body with the brand line `**☕ shipd** semantic review` — after the hidden `<!-- shipd-semantic-review -->` marker and before the `## Findings:` verdict header — on fresh posts and in-place re-post edits alike, leaving the marker line itself byte-identical.

#### Scenario: Summary opens with the brand line
- **WHEN** the summary body is rendered for any review JSON
- **THEN** the first non-blank line after the hidden marker is `**☕ shipd** semantic review`, and the `## Findings:` verdict header follows it

#### Scenario: Machine surfaces stay unbranded
- **WHEN** `post` sets the commit status for a review
- **THEN** the status context is exactly `semantic-review`, with no brand mark in the context or the hidden marker

### Requirement: Review-start difftastic auto-fix
id: review-difft-autofix

When the `/s:review` skill begins a review and `difft` is not on PATH, the
skill SHALL run the tiered installer (`semdiff doctor --fix`) once before
any analysis and re-probe for `difft` afterwards — reaching the network
solely through `--fix`, preserving the installer's network invariant. If
`difft` is still missing after that attempt, then the skill SHALL inform
the user prominently — naming the text-engine degradation and a manual
install hint — and SHALL record the degradation in the review's
could-not-verify output in both human and `--json` modes, and SHALL then
complete the review on the text engine; a missing difftastic never blocks
the review and the installer is attempted at most once per review.

#### Scenario: Successful auto-install restores the syntax-aware engine
- **WHEN** a review starts with `difft` absent and the tiered installer
  succeeds
- **THEN** the review proceeds on the syntax-aware engine with no
  degradation notice

#### Scenario: Failed auto-install informs and degrades loudly
- **WHEN** a review starts with `difft` absent and the tiered installer
  leaves it missing
- **THEN** the user is informed with the text-engine degradation and a
  manual install hint, the degradation is recorded in the could-not-verify
  output, and the review still completes on the text engine

#### Scenario: Present difft skips the installer
- **WHEN** a review starts with `difft` already on PATH
- **THEN** the installer is not invoked and the review proceeds directly
