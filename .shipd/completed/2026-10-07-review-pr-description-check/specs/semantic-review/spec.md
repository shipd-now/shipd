## MODIFIED Requirements

### Requirement: Semantic review skill
id: review-skill
base: ef0ca408187c

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

Where a pull request's title and description are available, the skill SHALL check each concrete claim against the diff and report a mismatch as its own finding in the `description-drift` category, severity by the normal rubric, judged on what the mismatch implies for correctness or completeness — never a finding for a description that is merely terse or informal.

The five checks the skill applies to judge new code (a wrong quantity
measured, an escape hatch lapsing the guarantee, non-termination on hostile
input, a boundary disagreement, and a doc comment versus the actual code)
SHALL have their names stated inline in `SKILL.md`, outside any
conditionally-loaded reference file — the same always-applies guarantee the
risk lenses already carry — so that skipping the reference's read degrades
only the depth of guidance available, never the existence of the check
itself.

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
SHALL run the breadth sweep described above. It SHALL check the PR description against the diff as described above. It SHALL run a test-coverage
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
  defects, to check the PR description against the diff, and to check test
  coverage per finding

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
