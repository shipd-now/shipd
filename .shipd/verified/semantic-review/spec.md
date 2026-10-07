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

### Requirement: Required difftastic with per-file parse retry
id: text-fallback

If the `difft` binary is unavailable, then `semdiff diff` SHALL exit
non-zero with a message naming the install remedy and SHALL emit no diff
JSON, rather than degrading to the text engine. A review whose engine
varies silently produces a verdict nobody can reproduce or audit, and the
gate never reads the `engine` field that would have disclosed it. If
difftastic output fails to parse for a single file, then only that file
SHALL fall back to the text engine, stamping `engine: "text"` on that file
entry and on the summary, so a single unparseable file still degrades
rather than failing the run.

#### Scenario: Missing difft fails the diff
- **WHEN** `semdiff diff main` runs on a machine without `difft`
- **THEN** it exits non-zero, emits no diff JSON, and its message names how
  to install difftastic

#### Scenario: A single unparseable file still falls back
- **GIVEN** difftastic is installed but produces output that cannot be
  parsed for one file of several
- **WHEN** `semdiff diff main` runs
- **THEN** it exits zero, that file's entry carries `engine: "text"`, and
  the remaining files stay syntax-aware

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

The system SHALL provide `semdiff change <name>` aggregating a shipd change's
review context as one JSON object: the change status, per-delta entries
(operation, capability, requirement id and text, scenario texts), task
checkbox states with progress counts, the change's lint findings, and
best-effort impact files extracted from `plan.md`. It SHALL resolve the
content directory through the engine's layered configuration and reuse the
engine's parser in-process.

The verb SHALL resolve the change directory as `planned/<name>/` when that
directory exists and otherwise as the newest `completed/<date>-<name>/`
archive, the same order the status CLI's `cat change` uses, and SHALL report
the pick in two top-level JSON keys: `location` (`planned` or `completed`)
and `dir` (the change directory relative to the repo root). While the change
resolves to an archive, the verb SHALL NOT run the change linter and SHALL
report `lint.findings` as an empty list beside a `lint.skipped` sentence
stating why. If the change exists under neither directory, then the verb
SHALL exit non-zero with a message naming the change and both directories.

#### Scenario: Aggregated change context
- **WHEN** `semdiff change my-change` runs against a lint-clean planned
  change with two delta requirements and three tasks, one checked
- **THEN** the JSON lists both requirements with their scenarios, reports
  task progress 1 of 3 with no lint findings, and carries `location`
  `planned` with no `lint.skipped` key

#### Scenario: Archived change resolves
- **WHEN** `semdiff change my-change` runs and `planned/my-change/` is absent
  while `completed/2026-01-01-my-change/` holds the archived change
- **THEN** it exits zero, carries `location` `completed` and a `dir` ending
  in `completed/2026-01-01-my-change`, lists the archive's delta scenarios
  and task counts, and reports empty lint findings with a `lint.skipped`
  sentence

#### Scenario: Newest archive wins
- **WHEN** `semdiff change my-change` runs and both
  `completed/2026-01-01-my-change/` and `completed/2026-02-01-my-change/`
  exist with no planned copy
- **THEN** the JSON `dir` names `completed/2026-02-01-my-change`

#### Scenario: Unknown change fails clearly
- **WHEN** `semdiff change nope` runs and neither `planned/nope/` nor any
  `completed/*-nope/` exists
- **THEN** it exits non-zero naming the missing change and both `planned/`
  and `completed/`

### Requirement: Dependency doctor with tiered installer
id: doctor-provisioning

The system SHALL provide `semdiff doctor` reporting tool availability —
git and difft required; rg and gh optional — with actionable hints,
exiting non-zero only when a required tool is missing. Where `--fix` is
given, the system SHALL install difftastic by trying Homebrew, then cargo,
then a prebuilt release binary into the plugin's `bin/` (else
`~/.local/bin`); network access SHALL occur only under `--fix`. The
release-binary path SHALL request a pinned release version rather than the
unversioned `releases/latest/download/` asset name, which difftastic
stopped publishing after 0.65.0 and which therefore 404s. The
release-binary path SHALL extract only an archive member that is a regular
file: a member named `difft` that is a symlink or any other non-regular
type SHALL be refused with a clear error and nothing extracted.

#### Scenario: Doctor reports without installing
- **WHEN** `semdiff doctor` runs without `--fix` on a machine missing difft
- **THEN** difft is reported as required-missing with an install hint, no
  network access occurs, and the exit code is non-zero

#### Scenario: A non-regular archive member is refused
- **WHEN** the release-binary installer encounters an archive whose only
  `difft` member is a symlink
- **THEN** nothing is extracted and the failure names the non-regular
  member, while an archive with a regular-file `difft` member extracts it

#### Scenario: The installer requests a pinned version
- **WHEN** the release-binary installer's download URL is inspected
- **THEN** it names a pinned release version rather than
  `releases/latest/download/`

### Requirement: Semantic review skill
id: review-skill

The plugin SHALL provide an `/s:review` skill that reviews local changes
against a base ref (default `main`, or a named base/head pair) by mapping
cohorts foundational-first, reasoning over the semdiff structural diff
rather than raw file dumps, chasing changed signatures through `semdiff
context`, and reporting findings by cohort, each with one or more locations,
what, why, a concrete fix, and a severity of high, medium, or low. The
rendered report SHALL carry an effort score (1–5), a findings header reading
`## Findings: ✅ Ship it` when no finding is high or medium and
`## Findings: ❌ Fix required` otherwise, a summary table rating findings
with 🔴/🟠/🟡 severity dots, a collapsible walkthrough, and an explicit
list of what could not be verified.

A finding's location SHALL name the line its own fix would change — never a
caller or symptom site the fix does not touch. Where the same defect recurs
at more than one call site, the skill SHALL report one finding whose
locations name every recurring site, rather than one finding per site.

A `low`-severity finding SHALL be a real but minor defect — a swallowed or
silently-dropped error, a resource or file leak on a rare or cleanup path,
dead or duplicated code, a field or variable declared but never read, an
unstable or incorrect identity such as a list/row key derived from array
index instead of a stable id, or a blocking/synchronous call where the
surrounding context is async or event-driven — never pure style, naming
preference, or formatting, which SHALL NOT be reported as a finding at any
severity. The skill SHALL run a breadth sweep, after judging new code and
applying the risk lenses, that revisits each changed file once more, end to
end, for a remaining low-severity defect of those kinds that the targeted
structural and signature-chasing passes above would not otherwise surface.

Emoji SHALL appear at four sanctioned sites and nowhere else: the ✅/❌ verdict
marker, the 🔴/🟠/🟡 severity dots of the summary table, the ☕ of the posted
summary comment's `**☕ shipd** semantic review` brand line, and the 🔴/🟠/🟡
dot that prefixes a severity wherever a posted finding names its own severity —
the leading marker of an anchored inline comment, and each bullet of the summary
comment's folded-findings section. Both posting surfaces — `review_gate.py` and
the vendored review-gate workflow at
`plugins/s/integrations/copilot/copilot-review-gate.yml` — SHALL render that
dot, so one finding reads the same whichever surface posted it. The `--json`
payload SHALL stay free of emoji: the dot is added when a finding is rendered,
never carried in the machine object. Branding is shipd-only, and the skill SHALL
NOT modify the repo.

The skill SHALL additionally carry four judgement passes. It SHALL treat a
changed limit, bound, timeout, retry count, buffer size or threshold as a
contract change and chase its consumers through `semdiff context`, and it
SHALL compare two or more parallel implementations the diff touches against
each other, naming any hardening applied to one and not the other. It SHALL
judge every function, class, guard or helper the diff introduces against its
own stated purpose — whether it measures the quantity its limit governs,
whether an escape hatch lapses its guarantee, whether it terminates cheaply
on hostile input, and whether its boundaries and its doc comment agree. It
SHALL run the breadth sweep described above. It SHALL run a test-coverage
check over each finding it writes, at every severity, asking whether an
existing test would fail if that defect regressed, and SHALL raise any gap
as its own finding in the `test-coverage` category, which the `--json`
finding shape SHALL accept.

The `--json` finding shape's taxonomy field SHALL be named `category`. The
name `cohort` SHALL denote only the architectural grouping `semdiff files`
emits, and the name `kind` SHALL denote only a file's added, deleted or
modified state in `semdiff diff`; no surface SHALL use either word for the
finding taxonomy.

The skill SHALL review an added file's inlined `content` with the rigour it
applies to a hunk, and SHALL NOT pass such a file on its path and line count
alone. Where `content_truncated` is true, it SHALL read the remainder.

The skill SHALL bind its rendered report and its posted summary comment to
the shipd documentation standard, referencing that standard by path rather
than restating any rule, and SHALL name one finding a "finding" throughout.
The harness command body for the review SHALL carry the same four
judgement passes as the skill, so the two surfaces do not drift.

#### Scenario: Blocking verdict matches severities
- **WHEN** a review yields one medium and one low finding
- **THEN** the header reads `## Findings: ❌ Fix required` and the summary
  table rates them 🟠 and 🟡

#### Scenario: A posted finding names its severity with its dot
- **WHEN** `review_gate.py post` renders an anchored inline comment for a high
  finding
- **THEN** the comment's leading severity marker carries 🔴 directly before the
  word `high`

#### Scenario: A folded finding carries the dot too
- **WHEN** the summary comment's folded-findings section renders a medium
  finding
- **THEN** that bullet's severity is prefixed with 🟠

#### Scenario: Both posting surfaces render the dot
- **WHEN** `plugins/s/skills/review/scripts/review_gate.py` and
  `plugins/s/integrations/copilot/copilot-review-gate.yml` are inspected
- **THEN** each renders an inline finding comment whose severity carries the
  matching 🔴/🟠/🟡 dot

#### Scenario: Machine mode for the gate
- **WHEN** the skill is invoked with `--json`
- **THEN** it emits only a JSON object — verdict `changes-requested` iff
  any finding is high or medium, else `pass`, with findings, optional
  spec_coverage, and could_not_verify arrays — and no emoji or prose

#### Scenario: The taxonomy field is named category
- **WHEN** a `--json` review emits a finding
- **THEN** the finding's taxonomy is carried on a `category` key, and no
  finding carries a `cohort` or `kind` key

#### Scenario: The architectural cohort keeps its name
- **WHEN** `semdiff files` output and the skill's reporting instructions are
  inspected
- **THEN** both still name the architectural grouping `cohort`, unchanged by
  the finding-taxonomy rename

#### Scenario: The skill binds the standard by reference
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it names `skills/document/references/standard.md` by path and
  restates none of that file's numbered core rules

#### Scenario: The harness body carries the same passes
- **WHEN** `plugins/s/harness/bodies/review.md` is inspected
- **THEN** it instructs the reviewer to chase changed constants, to compare
  parallel sites against each other, to judge newly added code on its own
  terms, to sweep each changed file once more for remaining low-severity
  defects, and to check test coverage per finding

#### Scenario: A finding anchors at its fix site
- **WHEN** a defect's symptom is observable at a caller but the fix changes a
  different line
- **THEN** the finding's location names the line the fix would change, not
  the caller

#### Scenario: A recurring defect is one finding with every site
- **WHEN** the same defect recurs at more than one call site in the diff
- **THEN** the review reports one finding whose locations name every
  recurring site, not one finding per site

#### Scenario: A real minor defect is rated low, not waved through
- **WHEN** the diff carries a swallowed error, a dead or duplicated block, an
  unread field, or an index-derived list key
- **THEN** the review reports it as a low-severity finding rather than
  omitting it as style

#### Scenario: Pure style stays out of the findings
- **WHEN** a diff carries only a naming preference, a formatting choice, or
  other pure style difference with no functional effect
- **THEN** the review reports no finding for it, at any severity

#### Scenario: The breadth sweep runs after the targeted passes
- **WHEN** a changed file carries a low-severity defect that sits beside a
  hunk rather than inside it — so the structural diff and signature-chasing
  passes would not surface it on their own
- **THEN** the breadth sweep still reports it, after the new-code judgement
  and risk-lens passes have run

### Requirement: Spec-aware verification
id: spec-aware-review

Where a change is in scope, the skill SHALL verify the diff against
`semdiff change` output: classify every delta scenario as Met (citing the
satisfying hunk), Unmet, or Can't-tell; report each unmet scenario as a
high-severity spec-coverage finding; flag checked tasks with no supporting
change in the diff; and surface behavioral changes no requirement or task
describes as observations, not blockers.

A change is in scope when the user names one, when exactly one change exists
under `planned/`, or when the diff adds or edits a change directory under
`planned/` or `completed/`; in the last case the skill SHALL read the slug
from the directory name in the `files` output, stripping any leading
`YYYY-MM-DD-` date prefix. The spec-aware reference, the `SKILL.md`
references table, and the gate body under `plugins/s/harness/bodies/` SHALL
each state that three-part trigger.

#### Scenario: Unmet scenario tops the findings
- **WHEN** a delta scenario's behavior is absent from the structural diff
- **THEN** the review reports it as a high-severity spec-coverage finding
  and the verdict is Fix required

#### Scenario: An archived change in the diff is in scope
- **WHEN** a pull request's diff adds `.shipd/completed/2026-09-25-my-change/`
  and nothing sits under `planned/`
- **THEN** the review runs `semdiff change my-change` and reports a Spec
  coverage section for its scenarios

#### Scenario: Every trigger surface agrees
- **WHEN** `plugins/s/skills/review/references/spec-aware.md`,
  `plugins/s/skills/review/SKILL.md`, and
  `plugins/s/harness/bodies/review.md` are inspected
- **THEN** each names a change directory carried by the diff under
  `planned/` or `completed/` as a trigger, beside the named-change and
  single-planned-change triggers

### Requirement: Engine test coverage in ci
id: review-test-coverage

The semdiff script SHALL be covered by a unittest suite under
`plugins/s/skills/review/tests/` that builds fixture git repositories in
temporary directories, performs no network access, and is discovered by the
`ci` workflow. The `ci` workflow SHALL install difftastic before running
that suite, so the difft-gated assertions execute in the gating pipeline
rather than being skipped there. The suite SHALL cover the text engine
through the per-file parse-failure retry, which stays reachable, so the
fallback path ships tested even though no review may run wholly on it.

#### Scenario: ci installs difftastic and runs every assertion
- **WHEN** the ci workflow runs the review suite
- **THEN** difftastic is installed first and no test is skipped for its
  absence

#### Scenario: The text engine keeps its coverage
- **WHEN** the review suite runs
- **THEN** at least one test exercises the per-file parse-failure retry and
  asserts the `engine: "text"` stamp it produces

### Requirement: PR posting of a review verdict
id: gate-poster

`review_gate.py post <pr> --from <json|->` SHALL publish a `/s:review --json`
object to the named pull request via `gh`: upserting a single summary comment
identified by the hidden marker `<!-- shipd-semantic-review -->` (editing the
existing marker comment in place on re-runs, and recognizing the legacy marker
`<!-- am-semantic-review -->` on lookup while writing only the current one),
posting one inline comment for every location, across every finding's
`locations` array, that anchors to a RIGHT-side commentable line of the pull
request diff, folding into the summary any finding none of whose locations
anchor, retrying once with no inline comments if the review POST is rejected,
submitting that review with the event `COMMENT`, and setting a commit status
with context `semantic-review` on the pull request's head SHA.

A finding declaring more than one location SHALL carry a stable identity per
location — so each recurring site is dispositioned independently of its
siblings — while a finding declaring exactly one location SHALL keep the same
identity it carried before this requirement's locations array existed, so
prior disposition continuity is unaffected. An inline comment for a location
other than `locations[0]` SHALL additionally name the finding's other
locations, so a reader reaches the full recurrence from any one posted
comment.

An anchored inline comment's leading severity marker SHALL carry the severity's
🔴/🟠/🟡 dot directly before the severity word, and each bullet of the summary
comment's folded-findings section SHALL carry that same dot before its severity.
The marker's literal format SHALL live in exactly one place, shared by the body
renderer and by `parse_severity`, so the pair cannot drift. `parse_severity`
SHALL read a severity whether or not the marker carries the dot, so a finding
comment posted before this change is still classified rather than reported as
unparseable.

Where a finding declares its fix confident and supplies a replacement covering
one or more contiguous whole lines that anchor `locations[0]` to a RIGHT-side
commentable line, that location's inline comment SHALL carry the replacement
as a committable `suggestion` block so the fix can be applied without
retyping. A suggestion SHALL NOT attach to any location other than
`locations[0]` — a suggestion is a single-range edit that cannot replay
identically across sites whose surrounding code differs. A finding whose
replacement is absent, covers part of a line, spans a discontiguous range, or
whose `locations[0]` does not anchor SHALL render as prose instead. Emitting a
suggestion SHALL NOT change the comment's leading severity marker, and the
`--json` mode SHALL stay free of emoji and prose.

#### Scenario: The marker round-trips with its dot
- **WHEN** an inline body is rendered for each of `high`, `medium` and `low` and
  read back with `parse_severity`
- **THEN** each body's marker carries the matching dot and each parse returns
  the severity it was rendered from

#### Scenario: A dotless marker still parses
- **WHEN** `parse_severity` reads an inline comment body whose marker carries no
  dot, as posted before this change
- **THEN** it returns that body's severity rather than nothing

#### Scenario: A confident whole-line fix becomes committable
- **WHEN** a finding declares its fix confident with a replacement covering
  contiguous whole lines that anchor `locations[0]` to the diff
- **THEN** its inline comment contains a `suggestion` fenced block carrying
  that replacement

#### Scenario: A multi-line replacement is supported
- **WHEN** a confident finding's replacement covers more than one contiguous
  whole line
- **THEN** the suggestion block carries every one of those lines

#### Scenario: An unanchorable fix stays prose
- **WHEN** a finding declares its fix confident but none of its locations
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
- **WHEN** `post` publishes a `changes-requested` verdict whose findings each
  name one location that anchors to the diff
- **THEN** one inline comment is posted per finding at its anchored location

#### Scenario: Re-post updates instead of stacking
- **WHEN** `post` runs twice for the same pull request
- **THEN** the second run edits the existing marker summary comment rather
  than creating a second one

#### Scenario: Legacy-marker summary is updated, not duplicated
- **WHEN** a pull request already carries a summary comment with the legacy
  marker
- **THEN** `post` edits that comment in place and writes only the current
  marker

#### Scenario: High-only greens over mediums
- **WHEN** `post` runs with `--disposition high-only` over a review carrying
  only medium and low findings
- **THEN** the commit status is `success`

#### Scenario: High-only stays red on a high
- **WHEN** `post` runs with `--disposition high-only` over a review carrying
  one high finding
- **THEN** the commit status is `failure`

#### Scenario: None is always green and stays honest
- **WHEN** `post` runs with `--disposition none` over a review carrying a
  `changes-requested` verdict
- **THEN** the commit status is `success` and the findings still render in
  full

#### Scenario: A multi-location finding posts one comment per anchorable site
- **WHEN** a finding's `locations` array names two sites that both anchor to
  RIGHT-side commentable lines in two different files
- **THEN** the poster submits one inline comment for each site, each carrying
  the finding's what/why/fix and each carrying its own distinct identity
  marker

#### Scenario: A partly-anchorable multi-location finding keeps its anchorable site
- **WHEN** a finding's `locations` array names one site that anchors and one
  that does not
- **THEN** the poster posts an inline comment for the anchorable site alone,
  and the finding is not folded into the summary's "Additional findings"
  section

#### Scenario: A fully off-diff multi-location finding is folded whole
- **WHEN** none of a finding's `locations` anchor to a RIGHT-side commentable
  line
- **THEN** the finding is folded into the summary's "Additional findings"
  section and no inline comment is posted for it

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

Where the review's target is a named pull request — a pull request URL, a
`#<number>` or a bare number, or a branch the invoker points at a pull request —
the `/s:review` skill SHALL review that pull request's head against its base
with merge-base semantics, emit the machine verdict, and publish it via the
poster without being asked to. Where the invocation names no pull request, the
skill SHALL review locally and SHALL post nothing.

The skill SHALL pass the disposition scope and the model tier through to the
poster only where the invoker supplied them. A default posted review therefore
carries no `--disposition` flag, so the poster's own default scope `all` maps the
`semantic-review` commit status severity-honestly.

Where the invoker asks for the posted findings to be dispositioned — a driving
session declaring a disposition scope, or the user asking for the findings to be
implemented or answered — the skill SHALL run the disposition loop by scope and
SHALL finish by running the gate's resolve verb. Under `all`, the loop SHALL
cover every posted finding regardless of severity: implement the suggestion when
it is correct, by editing, committing and pushing, or by the finding's
committable suggestion having been applied on the pull request, which counts as
the same implement branch and needs no separate reply; otherwise reply on the
finding's thread with the concrete reason via the gate's reply verb, never
leaving a finding with neither. Under `high-only`, the loop SHALL implement or
answer only the high-severity findings, re-reviewing and re-posting after any
push, and SHALL then run the gate's autoreply verb over the remaining threads.
Under `none`, the loop SHALL perform no per-finding judgment and SHALL run the
autoreply verb over every gate thread.

Where no such ask was made, the skill SHALL implement no finding, author no
reply, run neither the autoreply verb nor the resolve verb, and SHALL leave every
posted thread open for the pull request's owner to action and resolve.

Every posted review SHALL report the posted status state, the summary comment
URL, and the acting disposition scope when it is not `all`; where the
disposition loop ran, it SHALL additionally report the unresolved count, which
SHALL be zero on a completed disposition.

The two surfaces that cannot read a file under `skills/review/references/` —
`plugins/s/harness/bodies/review.md` and `plugins/s/harness/references/review.md`
— SHALL state the same posting default and the same opt-in disposition rule in
their own bodies.

#### Scenario: A named pull request is posted to without being asked
- **WHEN** the skill is invoked naming a pull request by URL and the user asks
  for nothing beyond the review
- **THEN** the verdict is published to that pull request through the poster, with
  no `--disposition` flag, and the `semantic-review` status is `success` iff the
  verdict is `pass`

#### Scenario: A local review still posts nothing
- **WHEN** the skill is invoked naming no pull request
- **THEN** the review ends at the rendered report, and no `gh` write is performed

#### Scenario: A default posted review leaves the threads open
- **WHEN** a posted review runs with no disposition asked for
- **THEN** no finding is implemented, no reply is authored, neither the autoreply
  verb nor the resolve verb runs, and every posted thread is left unresolved

#### Scenario: An unimplemented finding still needs a reason
- **GIVEN** the invoker asked for the findings to be dispositioned under scope
  `all`
- **WHEN** a posted finding is neither implemented nor carries an applied
  suggestion
- **THEN** the flow replies on its thread with the concrete reason before
  resolving

#### Scenario: Sensible suggestion is implemented before merge
- **GIVEN** the invoker asked for the findings to be dispositioned under scope
  `all`
- **WHEN** a posted finding's fix is correct
- **THEN** the fix is edited, committed and pushed, and the review is re-run and
  re-posted against the new head

#### Scenario: An applied suggestion needs no reply
- **WHEN** a posted finding's committable suggestion has been applied on the pull
  request and the disposition loop runs under scope `all`
- **THEN** that finding is treated as implemented, no reply is required on its
  thread, and the completed disposition still reports an unresolved count of zero

#### Scenario: High-only spends judgment only on highs
- **GIVEN** a posted review carrying one high finding and two medium findings,
  and a driving session declaring scope `high-only`
- **WHEN** the disposition loop runs
- **THEN** the high finding is implemented or answered individually, the autoreply
  verb covers the medium threads, and the resolve verb reports an unresolved
  count of zero

#### Scenario: None costs no disposition judgment
- **GIVEN** a driving session declaring scope `none`
- **WHEN** the disposition loop runs
- **THEN** no finding receives an individually authored disposition, the autoreply
  verb covers every gate thread, and the resolve verb reports an unresolved count
  of zero

#### Scenario: The reference-free surfaces carry the default
- **WHEN** `plugins/s/harness/bodies/review.md` and
  `plugins/s/harness/references/review.md` are inspected
- **THEN** neither instructs the reviewer to post only on an explicit request,
  and each states that a named pull request is posted to by default while
  dispositioning and resolving are opt-in

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
`difft` is still missing after that attempt, then the skill SHALL stop
without reviewing, reporting prominently that difftastic is required, how
to install it manually, and that no verdict was produced. It SHALL NOT
complete the review on the text engine: a review the engine could not
judge syntax-aware is one nobody can reproduce, and reporting it as a
review is worse than reporting nothing. The installer is attempted at most
once per review.

#### Scenario: Successful auto-install restores the syntax-aware engine
- **WHEN** a review starts with `difft` absent and the tiered installer
  succeeds
- **THEN** the review proceeds on the syntax-aware engine with no
  degradation notice

#### Scenario: Failed auto-install stops the review
- **WHEN** a review starts with `difft` absent and the tiered installer
  leaves it missing
- **THEN** the skill stops without analysing, reports that difftastic is
  required with a manual install hint, and produces no verdict

#### Scenario: Present difft skips the installer
- **WHEN** a review starts with `difft` already on PATH
- **THEN** the installer is not invoked and the review proceeds directly

### Requirement: Skill reference loading
id: review-skill-references

The `/s:review` skill SHALL carry its condition-gated guidance in reference
files under `plugins/s/skills/review/references/` rather than inline in its
`SKILL.md`, and `SKILL.md` SHALL name every file in that directory by its
`${CLAUDE_PLUGIN_ROOT}` path beside the condition under which the skill reads
it. The spec-aware verification guidance, the `--json` machine output guidance,
and the PR posting guidance SHALL each occupy one such file, read only when a
planned change is in scope, when `--json` is requested, and when a pull request
is in scope for the review, respectively. The posting reference SHALL carry the
resolution of a named pull request into a base and a head, so `SKILL.md` names
that flow rather than restating it.

Guidance that runs on every review SHALL stay inline in `SKILL.md`: the
workflow steps, the severity rubric, the presentation shape, the review-start
difftastic probe and its degradation ladder, the base-freshness block, and the
guardrails. `SKILL.md` SHALL stay under 330 lines.

Each reference file SHALL open with a level-1 title and state its own load
condition, so a file read on its own explains why it was read. Moving guidance
into a reference SHALL NOT change that guidance's substance.

#### Scenario: Every reference is reachable from the skill
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it names every file under `plugins/s/skills/review/references/` by
  path, and every reference path it names resolves to an existing file

#### Scenario: The posting reference is loaded on a pull request
- **WHEN** the References table row for `posting.md` is compared with that
  file's own condition sentence
- **THEN** both state that the file is read when a pull request is in scope for
  the review, rather than when posting was explicitly requested

#### Scenario: Conditional guidance left the skill body
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it carries no `## Machine output mode`, `## Posting to a PR`, or
  `## Spec-aware review` section, and the three reference files carry that
  guidance instead

#### Scenario: Hot-path guidance stayed inline
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** the workflow steps, the high/medium/low severity rubric, the
  `command -v difft` probe, and the base-freshness block are present in the file
  itself, behind no reference

#### Scenario: The skill body fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is under 330 lines

#### Scenario: A reference states its own trigger
- **WHEN** a file under `plugins/s/skills/review/references/` is read on its own
- **THEN** its opening lines give a level-1 title and the condition under which
  the skill loads it

#### Scenario: The other rubric surfaces are untouched
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` and
  `plugins/s/harness/bodies/review.md` are inspected
- **THEN** neither references a file under `plugins/s/skills/review/references/`,
  since neither runs where `${CLAUDE_PLUGIN_ROOT}` resolves

### Requirement: Risk lenses
id: review-risk-lenses

The `/s:review` skill SHALL carry four risk lenses alongside its existing
judgement passes — security, performance, stability, and data integrity —
expressed as five triggers: secret or credential exposure, authorization
boundary, unbounded work, resource release, and migration reversibility. The
triggers SHALL be stated inline in `SKILL.md`, read on every review, and SHALL
NOT be gated on a cohort, a file type, or any other condition. The detailed
guidance and worked examples for the lenses SHALL live in
`plugins/s/skills/review/references/risk-lenses.md`, read when a trigger fires.

A finding of secret or credential exposure, or of an authorization boundary
reached without the caller's scope check, SHALL carry severity `high`
regardless of the reviewer's confidence. Findings from the remaining triggers
SHALL rate on the existing high, medium and low rubric with no floor.

The `--json` finding taxonomy SHALL accept the values `security`,
`performance`, `stability`, and `data-integrity` in addition to those it
already accepts.

Both surfaces that cannot read a reference file — the harness command body at
`plugins/s/harness/bodies/review.md` and the vendored template at
`plugins/s/integrations/copilot/SKILL.md` — SHALL carry the lens guidance and
the exposure severity floor inline. `SKILL.md` SHALL stay under 300 lines.

#### Scenario: Every trigger is inline and ungated
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** all five triggers appear in the workflow itself, and no trigger is
  stated only in the References table or only in a reference file

#### Scenario: A leaked credential is high
- **WHEN** a review finds a new literal, log line, or error message carrying a
  key, token, or personal data
- **THEN** the finding's severity is `high` and the verdict is Fix required

#### Scenario: An unguarded authorization boundary is high
- **WHEN** a review finds a new route, handler, or query reaching data without
  the caller's scope check
- **THEN** the finding's severity is `high`

#### Scenario: The remaining lenses carry no floor
- **WHEN** a review finds an unbounded loop whose cost the reviewer judges
  minor
- **THEN** the finding may rate `low` or `medium`, since only the two exposure
  triggers carry a floor

#### Scenario: The taxonomy accepts the lens values
- **WHEN** a `--json` review emits a finding from the data-integrity trigger
- **THEN** `data-integrity` is a value the finding shape accepts

#### Scenario: The reference-free surfaces carry the lenses inline
- **WHEN** `plugins/s/harness/bodies/review.md` and
  `plugins/s/integrations/copilot/SKILL.md` are inspected
- **THEN** each names all five triggers and the exposure severity floor in its
  own body, referencing no file under `skills/review/references/`

#### Scenario: The new reference is pinned like the others
- **WHEN** the review skill's test suite runs
- **THEN** `risk-lenses.md` is named in the References table, its path
  resolves, and its `Load when` cell and its condition sentence share at least
  the required content words

#### Scenario: The skill body still fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is under 300 lines

### Requirement: Taxonomy parity across payload surfaces
id: review-taxonomy-parity

The `--json` finding payload is documented on two surfaces: the plugin skill's
reference at `plugins/s/skills/review/references/json-output.md`, and the
harness command reference at `plugins/s/harness/references/review.md`, which
ships to every harness declaring the `file-references` feature. Both SHALL
state the same taxonomy field name and the same set of accepted values, and a
test SHALL assert that equality so a value added to one cannot silently skip
the other.

#### Scenario: Both payload surfaces accept the same values
- **WHEN** the taxonomy enums of the plugin reference and the harness
  reference are compared
- **THEN** the two value sets are equal, and both name the field `category`

#### Scenario: A value added to one surface alone fails the pin
- **WHEN** a taxonomy value is added to the plugin reference and not to the
  harness reference
- **THEN** the parity test fails, naming the values present on one surface and
  absent from the other

#### Scenario: The harness reference carries the values it had drifted behind
- **WHEN** `plugins/s/harness/references/review.md` is inspected
- **THEN** its taxonomy accepts `test-coverage`, `security`, `performance`,
  `stability` and `data-integrity` alongside the values it already carried

### Requirement: Static analysis subcommand
id: review-lint-subcommand

The system SHALL provide `semdiff lint <base> [<head>]`, resolving its
endpoints exactly as `diff` and `files` do, and emitting a single JSON object
carrying the resolved `base`, `head` and `mode`, a `linters` list, and a
`summary`.

The subcommand SHALL detect a linter when its conventional marker file is
present **and** its binary resolves, checking `node_modules/.bin/<tool>` from
the repository root before `PATH`. It SHALL detect `ruff` (`ruff.toml`,
`.ruff.toml`, or a `[tool.ruff]` section in `pyproject.toml`), `flake8`
(`.flake8`, or a `[flake8]` section in `setup.cfg` or `tox.ini`), `pylint`
(`.pylintrc`, or a `[tool.pylint]` section in `pyproject.toml`) and `eslint`
(any `eslint.config.*` or `.eslintrc*`). A marker present with no resolvable
binary SHALL be reported with state `unavailable` rather than omitted.

The subcommand SHALL execute only an argv it constructs itself, requesting each
linter's machine-readable format, and SHALL run each linter over **only** the
changed paths whose extension that linter owns — `.py` for the three Python
linters, and the JavaScript and TypeScript extensions for `eslint`. A detected
linter owning no changed path SHALL be reported with state `skipped` and SHALL
NOT run. No linter SHALL receive a fix or write flag.

The subcommand SHALL NOT execute a repository-defined script by default. A
`lint` script declared in `package.json` SHALL be reported with state
`not-run`, and SHALL be executed only where the resolved configuration's `lint`
key declares `run_scripts` true.

Each `linters` entry SHALL carry the linter's `name`, its `state` (one of
`ran`, `unavailable`, `skipped`, `not-run`, `failed`), the `argv` executed when
one was, and its `findings`, each with `path`, `line`, `rule`, `message` and
`severity`. Each linter SHALL run under a per-linter timeout. A timeout, a
crash, or output that does not parse SHALL set state `failed` with a captured
stderr excerpt, and the subcommand SHALL still exit `0` — a failing linter
never blocks a review.

#### Scenario: A detected linter runs over changed paths only
- **WHEN** `semdiff lint` runs in a repository carrying a `ruff.toml`, with
  `ruff` resolvable and two changed Python files among several unchanged ones
- **THEN** the entry for `ruff` has state `ran`, its `argv` names only the two
  changed paths, and its findings carry `path`, `line`, `rule`, `message` and
  `severity`

#### Scenario: A marker without a binary is reported, not dropped
- **WHEN** a repository carries a `.flake8` file and `flake8` resolves on
  neither `node_modules/.bin` nor `PATH`
- **THEN** the `flake8` entry is present with state `unavailable`, and the exit
  code is `0`

#### Scenario: A detected linter owning no changed path is skipped
- **WHEN** `eslint` is detected and the diff changes only Python files
- **THEN** the `eslint` entry has state `skipped` and no `argv` is executed

#### Scenario: A repo script is not run without the opt-in
- **WHEN** `package.json` declares a `lint` script and the resolved
  configuration does not declare `lint.run_scripts` true
- **THEN** the entry has state `not-run` and no script is executed

#### Scenario: The opt-in permits the script
- **WHEN** the resolved configuration declares `lint.run_scripts` true and
  `package.json` declares a `lint` script
- **THEN** the script is executed and its entry reports the state of that run

#### Scenario: A failing linter degrades rather than blocks
- **WHEN** a detected linter exceeds its timeout or emits output that does not
  parse
- **THEN** its entry has state `failed` carrying a stderr excerpt, and
  `semdiff lint` exits `0`

#### Scenario: The project's own install wins
- **WHEN** both `node_modules/.bin/eslint` and a `PATH` `eslint` resolve
- **THEN** the executed `argv` names the `node_modules/.bin` binary

### Requirement: Linter output in the review
id: review-lint-step

The `/s:review` skill SHALL carry an inline workflow step directing the
reviewer to run `semdiff lint` over the same endpoints as the diff and to read
its output, with the detailed guidance in
`plugins/s/skills/review/references/linters.md` named by its
`${CLAUDE_PLUGIN_ROOT}` path beside its load condition. The inline step SHALL
state that a linter finding is corroboration the reviewer weighs, reported only
where it bears on the change, and never promoted to a review finding
automatically. `SKILL.md` SHALL stay under 300 lines.

#### Scenario: The step is inline and the detail is referenced
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it carries the `semdiff lint` step in the workflow itself and names
  `linters.md` in the References table with its load condition

#### Scenario: A linter hit is not automatically a finding
- **WHEN** the skill's linter step is read
- **THEN** it states that a linter finding is weighed as corroboration and
  reported only where it bears on the change

#### Scenario: The skill body still fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is under 300 lines

### Requirement: Incremental gate review
id: review-incremental

Each inline finding comment the poster renders SHALL carry a hidden identity
marker of the form `<!-- shipd-finding <hash> -->`, where `<hash>` is the first
twelve hexadecimal characters of the SHA-256 of the finding's `location` path,
a newline, and its `what` text lowercased with whitespace runs collapsed to a
single space. The marker SHALL be the body's last element, never its first, so
the severity marker stays the opening token `parse_severity` reads. The hash
SHALL NOT incorporate a line number, so a finding whose line moved still
matches.

The system SHALL provide `review_gate.py prior <pr>`, emitting one JSON entry
per gate-authored review thread carrying the thread's `hash` (or null where the
body has no marker), `path`, `severity`, `what`, `thread_id`, `resolved`, and a
`disposition` of `replied`, `autoreplied`, `commit-only`, or `none`. A thread
whose non-root comments are all exactly one of the canonical `autoreply` bodies
SHALL classify `autoreplied`; a thread carrying any other reply SHALL classify
`replied`; a thread with no reply but a commit landed after its creation SHALL
classify `commit-only`; a thread with neither SHALL classify `none`. The verb
SHALL decide nothing about suppression and SHALL mutate nothing.

The `/s:review` skill, **when and only when posting to a pull request**, SHALL
read `prior` back before reporting and omit a finding whose hash matches a
thread classified `replied`. It SHALL NOT omit a finding matching any other
classification, and SHALL state in its report how many findings it omitted and
which pull request answered them. A review that is not posting SHALL read
nothing back and omit nothing.

`SKILL.md` SHALL state this trigger in the `Load when` cell of its existing
`posting.md` References row, adding no line, and SHALL stay under 300 lines.

#### Scenario: A reworded finding is reported again
- **WHEN** a prior thread was answered with a reasoned reply and the new review
  produces a finding at the same path whose `what` text differs
- **THEN** the hashes differ and the new finding is reported

#### Scenario: A dismissed finding is omitted on the next head
- **WHEN** a prior thread carries a reasoned reply and the new review produces
  a finding whose path and `what` match it
- **THEN** the finding is omitted and the report states one finding was omitted
  and names the pull request

#### Scenario: An implemented finding that recurs is reported
- **WHEN** a prior thread's only disposition evidence is a commit landed after
  its creation, and the same finding recurs
- **THEN** the thread classifies `commit-only` and the finding is reported,
  because a recurrence after a fix is a regression

#### Scenario: An auto-dispositioned finding is reported
- **WHEN** a prior thread's only replies are the canonical `autoreply` body
- **THEN** the thread classifies `autoreplied` and the finding is reported

#### Scenario: A moved line still matches
- **WHEN** a dismissed finding recurs at the same path with identical `what`
  text but a different line number
- **THEN** the hashes match and the finding is omitted

#### Scenario: The severity marker survives the identity marker
- **WHEN** a body rendered with an identity marker is passed to
  `parse_severity`
- **THEN** it returns the finding's severity, unchanged by the marker

#### Scenario: A pre-push review reads nothing back
- **WHEN** a review runs without a posting request
- **THEN** no `prior` call is made and no finding is omitted

#### Scenario: The trigger costs no line
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured and its References
  table inspected
- **THEN** the file is under 300 lines and the `posting.md` row's `Load when`
  cell states the read-back trigger

### Requirement: Documentation states difftastic as required
id: difft-required-docs

The repository's documentation SHALL describe difftastic as required for a
semantic review, and SHALL carry no claim that a review degrades, falls back
to the text engine, or completes without it. `docs/semantic-review.md`'s
missing-tool section SHALL say the review stops without `difft`, and
`docs/copilot-review-reference.md` SHALL NOT list `difft` among optional
tools. Each page SHALL stay within its own doc-type line cap and SHALL read
as a statement of current behaviour, naming no change, no previous
behaviour, and no migration.

#### Scenario: The concept guide says the review stops
- **WHEN** `docs/semantic-review.md`'s missing-tool section is read
- **THEN** it states that a review without `difft` stops, and makes no claim
  that it degrades or falls back

#### Scenario: The reference no longer calls difftastic optional
- **WHEN** `docs/copilot-review-reference.md` is read
- **THEN** `difft` is not described as optional and no text-engine fallback
  is offered for its absence

#### Scenario: The pages stay within their caps
- **WHEN** the documentation lint runs over `docs/semantic-review.md` and
  `docs/copilot-review-reference.md`
- **THEN** it reports no finding

### Requirement: Summary comment clean-verdict wording
id: summary-clean-wording

When a review carries no findings, `review_gate.py post` SHALL render `No problems found.` in place of the findings table, and the review skill's report rules SHALL instruct the same sentence, so a clean review reads identically from either surface. The sentence SHALL be defined once, as the `NO_PROBLEMS` constant in `review_gate.py`, and the retired `No findings.` sentence SHALL appear on neither surface.

#### Scenario: Clean review says no problems found
- **WHEN** the summary body is rendered for a review JSON whose `findings` list is empty
- **THEN** the body carries `No problems found.` below the effort line, carries no `| # |` table header, and carries no `No findings` text

#### Scenario: The skill body quotes the constant
- **WHEN** `plugins/s/skills/review/SKILL.md` is read
- **THEN** it contains `No problems found.` and does not contain `No findings.`

### Requirement: Summary comment review footer
id: summary-review-footer

`review_gate.py post` SHALL close the summary comment it upserts with one stat line, `Reviewed N files, +A -D lines.`, where N is the number of entries in the pull request's file list and A and D are the sums of those entries' integer `additions` and `deletions`. The footer SHALL be the body's last line on every verdict, after any "Additional findings" section, on the first upsert and on the folded re-post alike. When no entry carries an integer count the line SHALL read `Reviewed N files.`; when N is 1 the noun SHALL be singular; when the file list is empty or absent no footer SHALL be rendered. A boolean SHALL NOT count as a line count.

#### Scenario: Footer closes a clean summary
- **GIVEN** a pull request whose file list holds two entries with 12/3 and 100/0 additions/deletions
- **WHEN** `post` publishes a review with no findings
- **THEN** the summary body's last non-blank line is `Reviewed 2 files, +112 -3 lines.` and `No problems found.` precedes it

#### Scenario: Footer follows the folded findings
- **GIVEN** a review with one unanchored medium finding and the same file list
- **WHEN** the summary body is rendered
- **THEN** the "Additional findings" section appears before the footer and the footer is the last non-blank line

#### Scenario: Footer survives the folded re-post
- **GIVEN** the inline review POST is rejected once
- **WHEN** `post` folds the findings and re-upserts the summary
- **THEN** the re-posted body still ends with the footer

#### Scenario: Singular file and missing counts
- **WHEN** the file list holds one entry carrying no `additions` or `deletions`
- **THEN** the footer reads `Reviewed 1 file.`

#### Scenario: No file list, no footer
- **WHEN** `render_summary` is called with `files` omitted, empty, or holding no dict entries
- **THEN** the body carries no `Reviewed` line

### Requirement: Base resolution to the remote-tracking counterpart
id: base-resolution

Where a `<base>` given to `semdiff diff`, `files`, or `lint` names a short local
branch carrying a remote-tracking counterpart — the branch's configured
upstream, else `refs/remotes/origin/<base>` — the system SHALL resolve the base
to that counterpart's commit, so a local branch behind its remote is never read
as a review's base. Where the base is a fully-qualified ref, a commit id, a tag,
or an already-remote ref, the system SHALL take it as given and SHALL NOT
resolve it further, which is the invoker's unambiguous opt-out.

While reviewing the working tree — no `<head>` given — the system SHALL anchor
the before side on the merge base of the resolved base and `HEAD`, never on the
resolved base's tip, so the base's own advance is never rendered as reversions.

The system SHALL perform no fetch, no checkout, and no write of any kind while
resolving: it reads already-fetched refs and reads every base-side blob from the
object database, so no worktree is materialized.

#### Scenario: A stale local base no longer sweeps in the base's own commits
- **GIVEN** local `main` is three commits behind `origin/main` and `feature`
  branches from `origin/main`
- **WHEN** `semdiff diff main feature` runs
- **THEN** only the files `feature` changed are reported, and the emitted base
  names the remote-tracking counterpart rather than the local branch

#### Scenario: Working-tree mode anchors on the fork point
- **GIVEN** the checkout sits on a local `main` three commits behind
  `origin/main`, with one edited file
- **WHEN** `semdiff diff main` runs
- **THEN** only the edited file is reported, and none of the files those three
  commits changed

#### Scenario: An explicitly qualified base is taken as given
- **GIVEN** local `main` is behind `origin/main`
- **WHEN** `semdiff diff refs/heads/main feature` runs
- **THEN** the base resolves to the local branch's own commit

#### Scenario: A base with no counterpart resolves unchanged
- **WHEN** `semdiff diff <commit-id> feature` runs in a repository with no
  remote
- **THEN** the base resolves to that commit and the run reports it unchanged

### Requirement: Endpoint disclosure on every review
id: endpoint-disclosure

The endpoint metadata `semdiff diff`, `files`, and `lint` emit SHALL additionally
carry `base_given` (the ref as invoked), `base_sha`, and `head_sha`, and SHALL
carry `merge_base` in working-tree mode — where it is the fork point — as well as
in merge-base mode. Under `--linear` no `merge_base` SHALL be emitted. Where the
after side is the working tree, `head_sha` SHALL be null.

The rendered report SHALL state the resolved endpoints as commit ids before the
findings, and the `--json` payload SHALL carry an `endpoints` object holding the
same `base_given`, `base`, `base_sha`, `head`, `head_sha`, `merge_base`, and
`mode` values, so a reader and the poster alike can see which base produced the
findings. The `endpoints` object SHALL be specified identically by every surface
defining the machine payload: `plugins/s/skills/review/references/json-output.md`
and `plugins/s/harness/references/review.md`.

#### Scenario: The endpoints are emitted as commit ids
- **WHEN** `semdiff diff main feature` runs
- **THEN** the emitted metadata carries `base_given`, `base_sha`, `head_sha`,
  and `merge_base`, each a commit id rather than a ref name

#### Scenario: Working-tree mode discloses a null head
- **WHEN** `semdiff diff main` runs
- **THEN** `head_sha` is null, and `merge_base` carries the fork point of the
  resolved base and `HEAD`

#### Scenario: Both payload surfaces specify one object
- **WHEN** `references/json-output.md` and `harness/references/review.md` are
  compared
- **THEN** both specify the same `endpoints` object with the same field names

### Requirement: Review-start base fetch
id: review-base-fetch

The `/s:review` skill SHALL carry an inline base-freshness block instructing a
fetch of the base's remote before the first `semdiff` call, in every mode —
working-tree, two-ref, and pull-request alike — rather than only where two refs
are named. The block SHALL state that the fetch updates remote-tracking refs
only and modifies neither the working tree, the index, nor any local branch, so
the skill's no-modification guarantee is unchanged, and that the skill never
pulls, rebases, or checks anything out on the invoker's behalf.

If the fetch fails, then the review SHALL continue and SHALL record a
could-not-verify entry naming that the base went unchecked against its remote —
in the rendered report's could-not-verify list and in `--json`'s
`could_not_verify` array alike — rather than ending the review.

Where the endpoints given to `semdiff lint` name two refs, the review SHALL
record a could-not-verify entry naming that the linters read the checkout rather
than the reviewed head, since `lint` passes changed paths to linter binaries that
read them from disk.

`plugins/s/harness/bodies/review.md`, which cannot read a file under
`skills/review/references/`, SHALL state the same fetch rule in its own body.

#### Scenario: The fetch rule covers the default mode
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** the base-freshness block instructs a fetch before the first `semdiff`
  call in every mode, and states that the fetch writes remote-tracking refs only

#### Scenario: A failed fetch is disclosed, not fatal
- **WHEN** the review-start fetch fails
- **THEN** the review proceeds and its could-not-verify list names the base as
  unchecked against its remote

#### Scenario: Two-ref lint discloses that it read the checkout
- **WHEN** a review runs `semdiff lint <base> <head>` with two refs
- **THEN** its could-not-verify list names that the linters read the checkout
  rather than the reviewed head

#### Scenario: The harness body carries the rule
- **WHEN** `plugins/s/harness/bodies/review.md` is inspected
- **THEN** it states the same fetch-before-every-mode rule in its own body

### Requirement: Doctor base-freshness probe
id: doctor-base-probe

`semdiff doctor` SHALL additionally report a base-freshness line comparing the
repository's default base branch — `main`, else `master` — against its
remote-tracking counterpart, naming the behind and ahead counts when the two
differ and naming the remedy. Without `--fix` the probe SHALL compare
already-fetched refs and SHALL reach the network not at all; where `--fix` is
given, the probe SHALL fetch that remote before comparing.

The probe SHALL be report-only: a diverged or unresolvable base SHALL NOT change
`doctor`'s exit code, which stays non-zero only when a required tool is missing.

#### Scenario: A diverged base is reported without failing the doctor
- **GIVEN** local `main` is behind `origin/main` and every required tool is
  present
- **WHEN** `semdiff doctor` runs
- **THEN** the base line names the behind count and the remedy, no fetch occurs,
  and the exit code is zero

#### Scenario: A repository with no counterpart reports cleanly
- **WHEN** `semdiff doctor` runs in a repository whose default branch has no
  remote-tracking counterpart
- **THEN** the base line says there is nothing to compare and the exit code is
  unchanged

### Requirement: Pull-request base guard
id: post-base-guard

Before its first GitHub write, `review_gate.py post` SHALL resolve the pull
request's `baseRefOid` and `headRefOid` through the `gh` seam, compute their
merge base through an injectable `git` runner, and compare it with the review
payload's `endpoints.merge_base`. If the two differ, or if the payload carries no
`endpoints.merge_base`, then `post` SHALL abort before upserting the summary
comment, posting any inline comment, or setting the `semantic-review` status,
SHALL name both merge bases — or the missing field — and SHALL exit non-zero.

Where the review's target is a named pull request, the `/s:review` skill SHALL
resolve that pull request's base through GitHub rather than through a local
branch name, fetching the pull request's head ref and its base branch so both
commits are present, reviewing as the two resolved commit ids, and stating the
base commit it used.

#### Scenario: A mismatched base aborts the post
- **GIVEN** a review payload whose `endpoints.merge_base` differs from the merge
  base of the pull request's own base and head
- **WHEN** `review_gate.py post` runs
- **THEN** no summary comment, inline comment, or commit status is written, the
  failure names both merge bases, and the exit code is non-zero

#### Scenario: A payload with no endpoints aborts the post
- **GIVEN** a review payload carrying no `endpoints.merge_base`
- **WHEN** `review_gate.py post` runs
- **THEN** no GitHub write occurs and the failure names the missing field

#### Scenario: A matching base posts as before
- **GIVEN** a review payload whose `endpoints.merge_base` equals the pull
  request's own merge base
- **WHEN** `review_gate.py post` runs
- **THEN** the summary comment, the inline comments, and the `semantic-review`
  status are written exactly as they were before the guard existed

#### Scenario: The skill resolves the pull request's base through GitHub
- **WHEN** `references/posting.md` is inspected
- **THEN** it resolves the base through the pull request's own base commit id
  rather than its base ref name, and names the fetch that makes both commits
  present

### Requirement: Fast-pass eligibility and poster arming
id: fast-pass-eligibility

Where a change is in scope, the `/s:review --json` object SHALL carry a
`change` member holding the resolved `slug`, the `location` (`planned` or
`completed`), and the `dir` reported by `semdiff change`, and SHALL omit that
member entirely where no change is in scope — the same presence rule
`spec_coverage` follows. Both documented payload surfaces —
`plugins/s/skills/review/references/json-output.md` and
`plugins/s/harness/references/review.md` — SHALL state that member, and a test
SHALL assert the two surfaces agree so one cannot drift behind the other.

`review_gate.py` SHALL expose a pure eligibility predicate deciding whether a
review object fast-passes. A review is eligible only where **all** of these
hold: the repository variable `SHIPD_FAST_PASS` reads exactly `true`; the
review's `change.location` is `completed`; the review's `verdict` is `pass`;
and `spec_coverage` is non-empty with every entry's `state` equal to `met`. The
predicate SHALL read `verdict` and never the disposition-mapped status state,
because `status_state` returns `success` unconditionally under the `none`
disposition scope and ignores medium findings under `high-only`, so a status
posted under either scope says nothing about whether findings remain open.

While a review is eligible, `review_gate.py post` SHALL arm auto-merge on the
pull request with `gh pr merge --auto --squash --delete-branch` through its
existing injectable `gh` runner, after the commit status is set, and SHALL
record in the summary comment that the fast-pass was armed. If a review is not
eligible, then `post` SHALL arm nothing and SHALL record which condition was
unmet, so a pull request that waits for a human says why. The variable SHALL be
read as `gh variable get SHIPD_FAST_PASS` through the same runner, and a
non-zero exit SHALL be treated as the fast-pass being off. If the arming call
fails, then `post` SHALL report the failure and SHALL still exit on the status
it already posted — a refused merge arming never costs the verdict.

#### Scenario: A verified completed change arms the merge
- **GIVEN** `SHIPD_FAST_PASS` reads `true`
- **WHEN** `post` consumes a review whose `change.location` is `completed`,
  whose verdict is `pass`, and whose every `spec_coverage` state is `met`
- **THEN** `gh pr merge --auto --squash --delete-branch` is run on that pull
  request and the summary comment records the fast-pass

#### Scenario: A can't-tell scenario arms nothing
- **WHEN** `post` consumes an otherwise eligible review carrying one
  `spec_coverage` entry whose state is `cant-tell`
- **THEN** no merge arming is run and the summary comment names the unmet
  condition

#### Scenario: The none disposition cannot fast-pass a failing verdict
- **GIVEN** `SHIPD_FAST_PASS` reads `true` and the acting disposition is `none`
- **WHEN** `post` consumes a review whose verdict is `changes-requested`
- **THEN** the commit status is `success` under that scope and no merge arming
  is run

#### Scenario: A planned-only change arms nothing
- **WHEN** `post` consumes an otherwise eligible review whose
  `change.location` is `planned`
- **THEN** no merge arming is run

#### Scenario: An absent variable is off
- **WHEN** `gh variable get SHIPD_FAST_PASS` exits non-zero
- **THEN** the predicate reports the review ineligible and no merge arming is
  run

#### Scenario: A review with no change in scope omits the member
- **WHEN** a `--json` review runs with no change in scope
- **THEN** the object carries no `change` member and no merge arming is run

#### Scenario: Both payload surfaces carry the change member
- **WHEN** `plugins/s/skills/review/references/json-output.md` and
  `plugins/s/harness/references/review.md` are compared
- **THEN** both document the `change` member with the same keys

#### Scenario: A refused arming keeps the verdict
- **WHEN** the merge arming call exits non-zero after the status was posted
- **THEN** `post` reports the arming failure and the posted status stands
