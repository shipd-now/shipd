# semantic-review

## MODIFIED Requirements

### Requirement: Semantic review skill
id: review-skill
base: 1abc4c79cb86

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

## ADDED Requirements

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
