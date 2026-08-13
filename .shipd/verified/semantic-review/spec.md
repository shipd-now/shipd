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
count; whitespace-only content edits SHALL be filtered out.

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

The system SHALL provide `semdiff change <name>` aggregating a planned am
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
only under `--fix`.

#### Scenario: Doctor reports without installing
- **WHEN** `semdiff doctor` runs without `--fix` on a machine missing difft
- **THEN** difft is reported as recommended-missing with an install hint,
  no network access occurs, and the exit code is zero when git is present

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
sites; branding is shipd-only, and the skill SHALL NOT modify the repo.

#### Scenario: Blocking verdict matches severities
- **WHEN** a review yields one medium and one low finding
- **THEN** the header reads `## Findings: ❌ Fix required` and the summary
  table rates them 🟠 and 🟡

#### Scenario: Machine mode for the gate
- **WHEN** the skill is invoked with `--json`
- **THEN** it emits only a JSON object — verdict `changes-requested` iff
  any finding is high or medium, else `pass`, with findings, optional
  spec_coverage, and could_not_verify arrays — and no emoji or prose

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

The system SHALL provide `review_gate.py post <pr> --from <json|->` which,
given a `/s:review --json` object, publishes it to the named pull request
via `gh`: it SHALL upsert a single summary comment identified by the hidden
marker `<!-- am-semantic-review -->` (editing the existing marker comment in
place on re-runs), SHALL post inline comments only for findings whose
`location` anchors to a RIGHT-side commentable line of the PR diff (folding
unanchorable findings into the summary, and retrying once with no inline
comments if the review POST is rejected), and SHALL set a commit status with
context `semantic-review` on the PR's head SHA — state `success` iff the
verdict is `pass`, else `failure`, with the summary comment as target URL.
The script SHALL be stdlib-only and perform no analysis of its own.

#### Scenario: Pass verdict posts green
- **WHEN** `post` runs with a JSON whose verdict is `pass` and no prior
  marker comment exists
- **THEN** a summary comment carrying the marker is created and the
  `semantic-review` status on the head SHA is `success`

#### Scenario: Re-post updates instead of stacking
- **WHEN** `post` runs twice against the same PR
- **THEN** the second run edits the existing marker comment and exactly one
  marker comment exists afterward

#### Scenario: Red verdict anchors findings inline
- **WHEN** `post` runs with verdict `changes-requested`, one finding whose
  `path:LINE` is in the PR diff and one whose is not
- **THEN** the in-diff finding becomes an inline comment, the other appears
  in the summary, and the status state is `failure`

### Requirement: Required-check protection verb
id: required-check-protect

`review_gate.py protect` SHALL read the default branch's protection,
union `semantic-review` into the required status check contexts, set
`required_conversation_resolution` to true, and write back preserving
`strict` and every other protection field; `protect --remove` SHALL
remove the context and clear the conversation-resolution requirement the
same way. Both directions SHALL be idempotent — already in the desired
state means no write and exit zero — and the verb SHALL print the
resulting contexts and conversation-resolution state.

#### Scenario: Protect adds the check and the resolution requirement
- **GIVEN** required contexts `["ci"]` and conversation resolution off
- **WHEN** `protect` runs
- **THEN** contexts become `ci` and `semantic-review`, conversation
  resolution is required, and `strict` is preserved

#### Scenario: Remove restores the prior gate
- **WHEN** `protect --remove` runs on a protected branch
- **THEN** `semantic-review` leaves the contexts and conversation
  resolution is no longer required

### Requirement: Skill post-to-PR flow
id: skill-post-flow

Where the user explicitly asks for a review to be posted, the `/s:review`
skill SHALL run the review, emit the machine verdict, publish it via the
poster, and then run the disposition loop over every posted finding
regardless of severity: implement the suggestion (edit, commit, push) when
it is correct, otherwise reply on the finding's thread with the concrete
reason via the gate's reply verb — never leaving a finding with neither.
The flow SHALL finish by running the gate's resolve verb and reporting the
posted status state, the summary comment URL, and the unresolved count,
which SHALL be zero on a completed disposition. The skill SHALL NOT post
as a side effect of a plain review request.

#### Scenario: Sensible suggestion is implemented before merge
- **GIVEN** a posted low finding whose fix is correct
- **WHEN** the disposition loop reaches it
- **THEN** the fix is committed and pushed rather than left as advice

#### Scenario: Disagreement is answered, not ignored
- **WHEN** the session judges a posted finding not worth implementing
- **THEN** the finding's thread gains a reasoned reply and is then
  resolved

#### Scenario: Flow ends with zero unresolved
- **WHEN** the posting flow completes
- **THEN** the report includes `unresolved=0` from the resolve verb

### Requirement: Poster test coverage in ci
id: gate-test-coverage

The `review_gate.py` script SHALL be covered by a unittest suite under
`plugins/s/skills/review/tests/` that injects a fake `gh` command seam,
performs no network access, and covers marker upsert versus create, inline
anchor computation from patch text, status state mapping, the no-inline
fallback, and protect add/remove idempotency; the suite SHALL be discovered
by the existing `ci` review-tests step.

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
