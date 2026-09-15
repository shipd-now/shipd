## MODIFIED Requirements

### Requirement: Skill post-to-PR flow
id: skill-post-flow
base: 10649e1d6eec

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

### Requirement: Skill reference loading
id: review-skill-references
base: eac6d6541d07

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
difftastic probe and its degradation ladder, and the guardrails. `SKILL.md`
SHALL stay under 300 lines.

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
- **THEN** the workflow steps, the high/medium/low severity rubric, and the
  `command -v difft` probe are present in the file itself, behind no reference

#### Scenario: The skill body fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is under 300 lines

#### Scenario: A reference states its own trigger
- **WHEN** a file under `plugins/s/skills/review/references/` is read on its own
- **THEN** its opening lines give a level-1 title and the condition under which
  the skill loads it

#### Scenario: The other rubric surfaces are untouched
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` and
  `plugins/s/harness/bodies/review.md` are inspected
- **THEN** neither references a file under `plugins/s/skills/review/references/`,
  since neither runs where `${CLAUDE_PLUGIN_ROOT}` resolves

### Requirement: Semantic review skill
id: review-skill
base: 0bda56bdd892

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
list of what could not be verified.

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
regressed, and SHALL raise any gap as its own finding in the `test-coverage`
category, which the `--json` finding shape SHALL accept.

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
The harness command body for the review SHALL carry the same three
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
  terms, and to check test coverage per finding

### Requirement: PR posting of a review verdict
id: gate-poster
base: 6e2c85b069cd

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

An anchored inline comment's leading severity marker SHALL carry the severity's
🔴/🟠/🟡 dot directly before the severity word, and each bullet of the summary
comment's folded-findings section SHALL carry that same dot before its severity.
The marker's literal format SHALL live in exactly one place, shared by the body
renderer and by `parse_severity`, so the pair cannot drift. `parse_severity`
SHALL read a severity whether or not the marker carries the dot, so a finding
comment posted before this change is still classified rather than reported as
unparseable.

Where a finding declares its fix confident and supplies a replacement covering
one or more contiguous whole lines that anchor to a RIGHT-side commentable
line, its inline comment SHALL carry that replacement as a committable
`suggestion` block so the fix can be applied without retyping. A finding whose
replacement is absent, covers part of a line, spans a discontiguous range, or
does not anchor SHALL render as prose instead. Emitting a suggestion SHALL NOT
change the comment's leading severity marker, and the `--json` mode SHALL stay
free of emoji and prose.

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
