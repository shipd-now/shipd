## MODIFIED Requirements

### Requirement: Standalone invocation
id: standalone-invocation
base: af1f7ac142d1

The skill SHALL be invocable on its own (`/s:plan <request>`), ending after
artifact emission with a hand-off summary and a pointer to build — without
starting any implementation. The hand-off summary SHALL lead with the
change's Motivation (why it is being built), followed by a brief summary of
the Implementation approach, and SHALL NOT enumerate the artifact files
written. The summary SHALL still name the change and where it lives so the
user can act on it. When the summary points at build, the closing sentence
SHALL end with a colon and the `/s:build` command SHALL sit alone on its own
line, separated from that sentence by a blank line — never inline
mid-sentence.

#### Scenario: Plan without build
- **WHEN** a user invokes `am:plan` directly and the flow completes
- **THEN** the skill summarizes what is being built and stops; no
  implementation work begins

#### Scenario: Summary leads with the why
- **WHEN** the plan flow completes and hands off
- **THEN** the summary opens with the plan's Motivation, follows with the
  Implementation approach, and contains no inventory of the files created

#### Scenario: Build pointer sits on its own line
- **WHEN** the hand-off summary ends with its pointer to build
- **THEN** the sentence before the pointer ends with a colon and `/s:build`
  appears alone on the next non-blank line, not embedded in a sentence
