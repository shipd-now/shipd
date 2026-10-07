## MODIFIED Requirements

### Requirement: Semantic review skill
id: review-skill
base: 765bf986111e

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
severity. Those kinds SHALL NOT set the severity: the skill SHALL rate every
finding by what the defect does, so data loss, data corruption, a security
exposure, or a broken guarantee is `medium` or `high` even when it arrives as
one of the minor kinds — a swallowed error that loses a file is not `low`.
Every surface that states the low rubric SHALL state that floor beside it.
The skill SHALL run a breadth sweep, after judging new code and
applying the risk lenses, that revisits each changed file once more, end to
end, for a remaining low-severity defect of those kinds that the targeted
structural and signature-chasing passes above would not otherwise surface.

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
location SHALL be added only where that site independently shows the drift on
its own terms.

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

#### Scenario: The breadth sweep names its target categories
- **WHEN** `plugins/s/skills/review/SKILL.md`'s breadth-sweep step is inspected
- **THEN** it points at the severity rubric's low-severity categories as what to look for, not only at the structural passes it runs after

#### Scenario: A description claim the diff contradicts is a finding
- **WHEN** a pull request's description claims behavior the diff does not
  implement, falls short of, or exceeds
- **THEN** the review reports it as a `description-drift` finding, severity
  by the normal rubric

#### Scenario: Description-drift is scoped to reviews that saw a description
- **WHEN** no pull request title or description was available to the review
- **THEN** no `description-drift` finding is reported

#### Scenario: Impact overrides the kind that surfaced a defect
- **WHEN** a defect arrives as one of the low rubric's minor kinds — a
  swallowed error — but loses a file when the error fires
- **THEN** the review rates it `medium` or `high`, not `low`, so it blocks
  the merge

#### Scenario: Both rubric surfaces state the impact floor
- **WHEN** `plugins/s/skills/review/SKILL.md` and
  `plugins/s/harness/bodies/review.md` are inspected
- **THEN** each states that the low list names kinds of defect rather than
  severities, and that impact floors a finding at `medium` or `high`

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
- **THEN** the finding carries its primary anchor alone, with a further
  location only where that site independently shows the drift

#### Scenario: Test-coverage findings roll up rather than multiplying
- **WHEN** a review writes four uncovered findings across two cohorts
- **THEN** it raises two `test-coverage` findings, one per cohort naming the
  defects it would guard, not four

#### Scenario: A fully covered cohort raises no test-coverage finding
- **WHEN** every finding in a cohort would already fail an existing test
- **THEN** that cohort raises no `test-coverage` finding
