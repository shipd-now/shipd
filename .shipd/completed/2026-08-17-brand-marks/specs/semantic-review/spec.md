## ADDED Requirements

### Requirement: Summary comment brand mark
id: summary-brand-mark

When `review_gate.py post` renders the marker-tagged summary comment, the system SHALL open the comment's visible body with the brand line `**☕ shipd** semantic review` — after the hidden `<!-- am-semantic-review -->` marker and before the `## Findings:` verdict header — on fresh posts and in-place re-post edits alike, leaving the marker line itself byte-identical.

#### Scenario: Summary opens with the brand line
- **WHEN** the summary body is rendered for any review JSON
- **THEN** the first non-blank line after the hidden marker is `**☕ shipd** semantic review`, and the `## Findings:` verdict header follows it

#### Scenario: Machine surfaces stay unbranded
- **WHEN** `post` sets the commit status for a review
- **THEN** the status context is exactly `semantic-review`, with no brand mark in the context or the hidden marker

## MODIFIED Requirements

### Requirement: Semantic review skill
id: review-skill
base: e8e6ebae2d49

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
