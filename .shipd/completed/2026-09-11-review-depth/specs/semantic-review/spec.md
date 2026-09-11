## MODIFIED Requirements

### Requirement: Structural diff subcommand
id: structural-diff
base: 1067375eed8a

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

### Requirement: Semantic review skill
id: review-skill
base: 2e6efc7350d6

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
