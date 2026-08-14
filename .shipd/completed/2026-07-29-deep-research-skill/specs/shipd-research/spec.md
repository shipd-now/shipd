## ADDED Requirements

### Requirement: Staged research pipeline over built-in tools
id: research-skill-pipeline

The `/s:research` skill SHALL turn a question into a cited research report by
orchestrating a staged pipeline in skill instructions — decompose the question
into bounded sub-questions, search each with the session's built-in WebSearch,
select the strongest sources, extract anchored findings with WebFetch, and
compose the report — using only the session's built-in web tools. If the
question is too underspecified to research (no scope, audience, or success
criterion inferable), then the skill SHALL ask one batched typed clarification
round before searching. If the built-in web tools are unavailable in the
session, then the skill SHALL report that and stop rather than compose
findings from model memory.

#### Scenario: Specific question runs without questions
- **WHEN** `/s:research` is invoked with a question specific enough to
  research directly
- **THEN** the skill proceeds through the staged pipeline and produces a
  report without asking the user anything

#### Scenario: Underspecified question gets one batched round
- **WHEN** the question is too underspecified to research
- **THEN** the skill asks a single batched typed clarification round and
  proceeds only after folding in the answers

#### Scenario: Missing web tools stop the run
- **WHEN** WebSearch or WebFetch cannot be reached in the session
- **THEN** the skill reports the missing tools and stops without emitting a
  report

### Requirement: Engine-mediated report emission
id: research-report-emission

The `/s:research` skill SHALL author the report in a staging area and install
it via `spec_emit.py research <slug> --from <file>`, choosing a kebab-case
slug derived from the question, and SHALL NOT construct a path under the
content directory's `research/` folder in either direction. On lint findings
from the emit engine, the skill SHALL fix the staged report and re-run until
the install exits zero.

#### Scenario: Report reaches the tree through the engine
- **WHEN** the skill finishes composing a report
- **THEN** the report is installed with `spec_emit.py research` from a staging
  path, never written directly into the spec tree

#### Scenario: Invalid report never lands
- **WHEN** the emit engine reports findings for the staged report
- **THEN** the skill fixes the staged file and re-runs the install, and the
  tree holds no report until an install exits zero

### Requirement: Cited report composition
id: research-report-content

The `/s:research` skill SHALL compose the report with a summary, themed
findings sections, a gaps-and-caveats section, and a numbered `## Sources`
list, and SHALL cite every load-bearing claim with an inline `[n]` marker that
maps to a listed source. If a claim cannot be anchored to a fetched source,
then the skill SHALL place it in the gaps-and-caveats section instead of
asserting it as a cited finding.

#### Scenario: Composed report carries the shape and citations
- **WHEN** the skill composes a report from extracted findings
- **THEN** the report holds a summary, themed findings, gaps and caveats, and
  numbered sources, with `[n]` markers on the load-bearing claims

#### Scenario: Unanchored claim is downgraded
- **WHEN** a claim survives extraction with no fetched source anchoring it
- **THEN** it appears under gaps and caveats rather than as a cited finding
