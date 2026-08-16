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
sites and, in the posted summary comment, the ☕ of the
`**☕ shipd** semantic review` brand line — the three sanctioned sites;
branding is shipd-only, and the skill SHALL NOT modify the repo.

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
context `semantic-review` on the PR's head SHA. The verb SHALL accept
`--disposition <scope>` (`all`, `high-only`, or `none`, default `all`) and
SHALL map the status state by scope: under `all`, `success` iff the verdict
is `pass`; under `high-only`, `success` iff no finding has severity `high`;
under `none`, always `success` — the findings JSON and rendered verdict
stay severity-honest in every scope. When the scope is not `all`, the
summary comment SHALL carry a `Disposition: <scope>` line and the status
description SHALL name the scope. The verb SHALL also accept
`--model <tier>` and, when given, SHALL record it verbatim as a
`Model: <tier>` line in the summary comment without resolving symbolic
tiers. The script SHALL be stdlib-only and perform no analysis of its own.

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

#### Scenario: High-only greens over mediums
- **WHEN** `post --disposition high-only` runs with verdict
  `changes-requested` from one medium and one low finding and no high
- **THEN** the status state is `success`, its description names the
  scope, and the summary carries the findings and a
  `Disposition: high-only` line

#### Scenario: High-only stays red on a high
- **WHEN** `post --disposition high-only` runs with a JSON carrying a
  high finding
- **THEN** the status state is `failure`

#### Scenario: None is always green and stays honest
- **WHEN** `post --disposition none --model tier-below` runs with a JSON
  carrying a high finding
- **THEN** the status state is `success` and the summary comment carries
  the finding, a `Disposition: none` line, and a `Model: tier-below` line

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
skill SHALL run the review, emit the machine verdict, and publish it via
the poster, passing through the disposition scope and model tier when the
invoker supplied them (defaults: scope `all`, no tier). The skill SHALL
then disposition findings by scope. Under `all`, the flow SHALL run the
full loop over every posted finding regardless of severity: implement the
suggestion (edit, commit, push) when it is correct, otherwise reply on the
finding's thread with the concrete reason via the gate's reply verb —
never leaving a finding with neither. Under `high-only`, the flow SHALL
implement (or push back with a reasoned reply) only the high-severity
findings, re-reviewing and re-posting after any push, and SHALL then run
the gate's autoreply verb so the remaining threads carry disposition
evidence. Under `none`, the flow SHALL perform no per-finding judgment and
SHALL run the autoreply verb over every gate thread. Every scope SHALL
finish by running the gate's resolve verb and reporting the posted status
state, the summary comment URL, the acting scope when it is not `all`, and
the unresolved count, which SHALL be zero on a completed disposition. The
skill SHALL document that applying the model tier is the spawning driver's
concern, and SHALL NOT resolve the pipeline configuration or post as a
side effect of a plain review request.

#### Scenario: Sensible suggestion is implemented before merge
- **GIVEN** a posted low finding whose fix is correct under scope `all`
- **WHEN** the disposition loop reaches it
- **THEN** the fix is committed and pushed rather than left as advice

#### Scenario: Disagreement is answered, not ignored
- **WHEN** the session judges a posted finding not worth implementing
  under scope `all`
- **THEN** the finding's thread gains a reasoned reply and is then
  resolved

#### Scenario: Flow ends with zero unresolved
- **WHEN** the posting flow completes in any scope
- **THEN** the report includes `unresolved=0` from the resolve verb

#### Scenario: High-only spends judgment only on highs
- **GIVEN** an invocation passing disposition `high-only` and a posted
  review with one high and two medium findings
- **WHEN** the posting flow runs
- **THEN** the high finding is implemented or answered with a reasoned
  reply, the medium threads are covered by the autoreply verb instead of
  individual judgment, and the flow ends with resolve reporting zero
  unresolved

#### Scenario: None costs no disposition judgment
- **GIVEN** an invocation passing disposition `none`
- **WHEN** the posting flow runs
- **THEN** the review is posted, the autoreply verb covers every gate
  thread, resolve reports zero unresolved, and no finding receives an
  individually authored disposition

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

When `review_gate.py post` renders the marker-tagged summary comment, the system SHALL open the comment's visible body with the brand line `**☕ shipd** semantic review` — after the hidden `<!-- am-semantic-review -->` marker and before the `## Findings:` verdict header — on fresh posts and in-place re-post edits alike, leaving the marker line itself byte-identical.

#### Scenario: Summary opens with the brand line
- **WHEN** the summary body is rendered for any review JSON
- **THEN** the first non-blank line after the hidden marker is `**☕ shipd** semantic review`, and the `## Findings:` verdict header follows it

#### Scenario: Machine surfaces stay unbranded
- **WHEN** `post` sets the commit status for a review
- **THEN** the status context is exactly `semantic-review`, with no brand mark in the context or the hidden marker
