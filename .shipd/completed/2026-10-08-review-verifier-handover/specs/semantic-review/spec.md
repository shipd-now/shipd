## MODIFIED Requirements

### Requirement: Semantic review skill
id: review-skill
base: 47bfe3f7133b

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

A finding's primary location SHALL name the line its own fix would change —
never a symptom site in place of it. A further location SHALL name a site at
which the defect is visible: a line wrong in the same way, a line that shows
the mismatch on its own terms, or, where the defect is the conjunction of two
lines neither wrong alone, the line at which it surfaces at run time even
though that line is correct in isolation. This is the general
permission the packaging and description-drift cases rely on, so no other
requirement SHALL grant it separately. Where the same defect recurs at
more than one call site, the skill SHALL report one finding whose locations
name every recurring site, rather than one finding per site.

The skill SHALL run a breadth sweep, after judging new code and applying the
risk lenses, that revisits each changed file once more, end to end, for a
remaining defect the targeted structural and signature-chasing passes above
would not otherwise surface. That sweep SHALL name the kinds of defect it hunts
— a swallowed or silently-dropped error, a resource or file leak on a rare or
cleanup path, dead or duplicated code, a field or variable declared but never
read, an unstable or incorrect identity such as a list/row key derived from
array index instead of a stable id, and a blocking/synchronous call where the
surrounding context is async or event-driven — and SHALL NOT describe them as
minor, because the kind of a defect is a detection aid and not a severity
class.

The severity rubric SHALL NOT list those kinds under `low`. A `low`-severity
finding SHALL be a real defect whose impact is contained — nothing lost,
corrupted, exposed, or promised and unmet. Pure style, naming preference, and
formatting SHALL NOT be reported as a finding at any severity. The skill SHALL
rate every finding by what the defect does rather than by the kind of defect it
is, so data loss, data corruption, a security exposure, or a broken guarantee
is `medium` or `high` however minor its kind looks. Because those four are
categories rather than situations, every surface stating the rating rule SHALL
also name concrete instances a reviewer can recognise: a success response that
hides a failure, a cleanup path that drops the record and leaves the data or
the reverse, and an error path that loses the only copy. Every surface that
states the low rubric SHALL state that rating rule beside it.

Uncertainty about a finding's severity SHALL NOT be grounds for omitting the
finding. Where the skill cannot place a severity, it SHALL report the finding
at its best estimate and say the estimate is uncertain, rather than leaving it
out — a defect it can describe is a defect it SHALL report.

Where a pull request's title and description are available, the skill SHALL
check them against the diff in **both** directions and report a mismatch from
either as its own finding in the `description-drift` category, severity by the
normal rubric and its impact floor, judged on what the mismatch implies for
correctness or completeness — never a finding for a description that is merely
terse or informal. The first direction takes each concrete claim and asks
whether the diff supports, contradicts, or falls short of it. The second takes
the diff's substantial content — a new feature path, dependency, migration, or
public surface, or a behavioral change to an existing one — and asks what the
description never mentions; it SHALL be a distinct pass, because unmentioned
scope carries no claim for the first direction to iterate over. Every surface
stating this check SHALL name both directions, so a reviewer that opens no
reference file runs neither pass believing the other sufficed.

A `description-drift` finding whose drift is a property of the description
rather than of any one line SHALL carry its primary anchor alone. A further
location follows the general further-location permission stated above; this
requirement grants no separate rule for it.

Where a check applies to every diff that carries the thing it inspects and
its detail lives in a conditionally-loaded reference file, the check's name
SHALL be stated inline in `SKILL.md` — so that skipping the reference's read
degrades only the depth of guidance available, never the existence of the
check itself. This SHALL hold for the five new-code checks (a wrong quantity
measured, an escape hatch lapsing the guarantee, non-termination on hostile
input, a boundary disagreement, and a doc comment versus the actual code),
for the five downstream-impact checks (untouched callers, every match a
candidate, `--lang` missing extensionless scripts, changed constants as
contract changes, and uneven sibling sites), for the two call-site-value
checks (an unreachable guard and a comment the real call sites contradict),
and for the risk lenses, which already carry it.

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

The skill SHALL additionally carry five judgement passes. It SHALL treat a
changed limit, bound, timeout, retry count, buffer size or threshold as a
contract change and chase its consumers through `semdiff context`, and it
SHALL compare two or more parallel implementations the diff touches against
each other, naming any hardening applied to one and not the other. It SHALL
judge every function, class, guard or helper the diff introduces against its
own stated purpose — whether it measures the quantity its limit governs,
whether an escape hatch lapses its guarantee, whether it terminates cheaply
on hostile input, and whether its boundaries and its doc comment agree. It
SHALL run the breadth sweep described above. It SHALL check the PR description against the diff as described above. It SHALL ask of each
finding it writes, at every severity, whether an existing test would fail if
that defect regressed, and SHALL report the gaps **rolled up per cohort** —
one `test-coverage` finding per cohort carrying uncovered findings, naming
each defect it would guard and where the tests belong, anchored once where
the tests belong. It SHALL NOT raise one such finding per finding: that count
scales with the findings themselves, so it buries the defects the check
exists to surface. A cohort whose findings are all covered SHALL raise none.
The `--json` finding shape SHALL accept the `test-coverage` category.

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
The harness command body for the review SHALL carry the same five
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
  defects, to check the PR description against the diff, and to roll test
  coverage up per cohort

#### Scenario: A finding anchors at its fix site
- **WHEN** a defect's symptom is observable at a caller but the fix changes a
  different line
- **THEN** the finding's location names the line the fix would change, not
  the caller

#### Scenario: A recurring defect is one finding with every site
- **WHEN** the same defect recurs at more than one call site in the diff
- **THEN** the review reports one finding whose locations name every
  recurring site, not one finding per site

#### Scenario: A real defect of a minor kind is reported, not waved through
- **WHEN** the diff carries a swallowed error, a dead or duplicated block, an
  unread field, or an index-derived list key
- **THEN** the review reports it as a finding, rated by its own impact, rather
  than omitting it as style

#### Scenario: Pure style stays out of the findings
- **WHEN** a diff carries only a naming preference, a formatting choice, or
  other pure style difference with no functional effect
- **THEN** the review reports no finding for it, at any severity

#### Scenario: The breadth sweep runs after the targeted passes
- **WHEN** a changed file carries a defect that sits beside a hunk rather
  than inside it — so the structural diff and signature-chasing passes would
  not surface it on their own
- **THEN** the breadth sweep still reports it, after the new-code judgement
  and risk-lens passes have run

#### Scenario: The five new-code check names survive a skipped reference read
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected outside its
  References table
- **THEN** all five new-code check names appear inline, so a reviewer that
  never opens `references/new-code-checks.md` still knows every check exists

#### Scenario: The extracted call-site check names survive the same way
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected outside its
  References table
- **THEN** the five downstream-impact check names and the two
  call-site-value check names appear inline too, so a reviewer that never
  opens `references/call-site-tracing.md` still knows every check exists

#### Scenario: The breadth sweep names the kinds itself
- **WHEN** `plugins/s/skills/review/SKILL.md`'s breadth-sweep step is inspected
- **THEN** it names the kinds of defect to look for in the step itself, and the
  severity rubric's `low` bullet does not list those kinds

#### Scenario: A description claim the diff contradicts is a finding
- **WHEN** a pull request's description claims behavior the diff does not
  implement, falls short of, or exceeds
- **THEN** the review reports it as a `description-drift` finding, severity
  by the normal rubric

#### Scenario: Description-drift is scoped to reviews that saw a description
- **WHEN** no pull request title or description was available to the review
- **THEN** no `description-drift` finding is reported

#### Scenario: Impact overrides the kind that surfaced a defect
- **WHEN** a defect arrives as one of the kinds the breadth sweep names — a
  swallowed error — but loses a file when the error fires
- **THEN** the review rates it `medium` or `high`, not `low`, so it blocks
  the merge

#### Scenario: Both rubric surfaces state the rating rule
- **WHEN** `plugins/s/skills/review/SKILL.md` and
  `plugins/s/harness/bodies/review.md` are inspected
- **THEN** each states that severity follows what the defect does rather than
  the kind of defect it is, and that data loss, corruption, exposure, or a
  broken guarantee is `medium` or `high`

#### Scenario: Unmentioned scope is found by the second direction
- **WHEN** a pull request's description is accurate about what it claims but
  the diff also adds a feature path the description never mentions
- **THEN** the review reports a `description-drift` finding for the
  unmentioned scope, which checking each claim against the diff cannot reach

#### Scenario: Every description surface names both directions
- **WHEN** `plugins/s/skills/review/SKILL.md`,
  `plugins/s/harness/bodies/review.md`, and
  `plugins/s/skills/review/references/pr-description.md` are inspected
- **THEN** each names both directions of the check

#### Scenario: A description-level finding does not fan out to code sites
- **WHEN** a drift is a property of the description rather than of any
  particular line
- **THEN** the finding carries its primary anchor alone, with any further
  location governed by the general further-location permission rather than
  a separate description-drift rule

#### Scenario: Test-coverage findings roll up rather than multiplying
- **WHEN** a review writes four uncovered findings across two cohorts
- **THEN** it raises two `test-coverage` findings, one per cohort naming the
  defects it would guard, not four

#### Scenario: A fully covered cohort raises no test-coverage finding
- **WHEN** every finding in a cohort would already fail an existing test
- **THEN** that cohort raises no `test-coverage` finding

#### Scenario: A run-time failure site qualifies as a further location
- **WHEN** a defect is the conjunction of two lines, neither wrong alone — a
  manifest omitting a file and the import that names it
- **THEN** the finding anchors at the fix site and names the importing line as
  a further location, because that is where the defect surfaces at run time

The skill SHALL run `semdiff related` after the structural diff and before its
judgement passes, and SHALL read the files that subcommand names where a check
needs context beyond the diff. The step SHALL name which checks the context
serves — the downstream-impact and call-site checks, and the lenses that
compare a change against unchanged code — so a reviewer given files is also
given the reason to read them. Reading a file the subcommand did not name
SHALL remain outside the skill's context economy: the engine's set is what
widens, never the reviewer's discretion.

#### Scenario: Related files are read when a check needs them
- **WHEN** a changed function's callers sit in files the diff does not touch
- **THEN** the review reads those files from `semdiff related`'s output rather
  than reasoning about the callers from the diff alone

#### Scenario: A file the engine did not name stays unread
- **WHEN** a reviewer judges some other file might be interesting
- **THEN** it is not read, because only the engine's named set widens the
  skill's context economy

Between judging the diff and reporting, the skill SHALL verify every candidate
finding through a **fresh-context verifier** spawned with the `Agent` tool. The
spawn SHALL name a `subagent_type` that resolves without plugin-provided agent
definitions, so a restricted headless session cannot mistake an unresolvable
type for a denied spawn. The verifier SHALL answer with one line per candidate,
in the order received, carrying the candidate's index and either `confirmed`
with a severity or `killed` with a one-line reason — and no justification
beyond that, since prompts demanding explanations raise misjudgment in code
verification. Candidates SHALL travel in the spawn message; the diff SHALL be
re-derived by the verifier from endpoints the message names, so it reads the
change itself rather than the hunt's summary of it. The
verifier SHALL receive the candidates, the diff, and the ability to read files,
and SHALL NOT receive the reasoning that produced the candidates. For each
candidate it SHALL return `confirmed` with a severity, or `killed` with a
reason. Severity SHALL be the verifier's: an earlier pass may propose one and
the verifier overrides it.

A killed candidate SHALL appear in the machine-readable payload in its own
top-level `killed` array carrying its location, claim, reason, and the
zero-based position it held in the candidate list the verifier received, and
SHALL NOT appear among `findings` under any status. The payload SHALL carry a
`verifier` field naming a `state` of `ran` or `skipped`, the total
`candidates` count the verifier was given, and a `reason` when skipped. Every
surface that specifies the machine payload SHALL carry both fields, so a review
told to emit them is never given a payload shape that omits them. The
position and the total together let a reader test whether kills cluster by
order rather than by merit, which surviving findings and kills reported
separately cannot show.

Where the spawn is unavailable — a restricted tool list denies it, or it
fails — the skill SHALL continue, record `skipped` with the reason, keep each
finding's proposed severity, and name the unverified review among what it could
not verify. It SHALL NOT report a review as verified when no verifier ran.

#### Scenario: A candidate the verifier kills leaves the findings
- **WHEN** the verifier returns `killed` for a candidate
- **THEN** that candidate appears in `killed` with its reason and appears
  nowhere in `findings`

#### Scenario: The verifier sets the severity
- **WHEN** a pass proposes `low` and the verifier judges the defect loses data
- **THEN** the reported severity is the verifier's, not the proposal

#### Scenario: A denied spawn is recorded, never hidden
- **WHEN** the `Agent` tool is unavailable to the review
- **THEN** `verifier.state` reads `skipped` with a reason, the findings keep
  their proposed severities, and the report names the review as unverified

#### Scenario: The verifier never sees the hunt's reasoning
- **WHEN** the verifier is spawned
- **THEN** its input carries the candidates, the diff and file access, and not
  the reasoning that produced them

#### Scenario: The spawn names a type that resolves headless
- **WHEN** the verify stage is inspected on any surface that states it
- **THEN** it names a concrete `subagent_type` that needs no plugin-provided
  agent definition

#### Scenario: Two sessions parse the same verdicts the same way
- **WHEN** two reviews of the same diff each spawn a verifier
- **THEN** both read verdicts in the one-line-per-candidate shape the skill
  specifies, rather than a convention each invented
