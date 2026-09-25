## MODIFIED Requirements

### Requirement: Standalone invocation
id: standalone-invocation
base: f3cf4235738d

The skill SHALL be invocable on its own (`/s:plan <request>`), ending after
artifact emission with a hand-off summary and a pointer to build — without
starting any implementation. The hand-off summary SHALL lead with the
change's Motivation (why it is being built), followed by a brief summary of
the Implementation approach, and SHALL NOT enumerate the artifact files
written. The summary SHALL still name the change and where it lives so the
user can act on it. The hand-off SHALL then close with a level-2 `## Summary`
heading followed by exactly one plain-language sentence stating what the
change does and why, naming no file, and the same heading and sentence SHALL
close the enrichment hand-off. When the summary points at build, the closing
sentence SHALL end with a colon and the `/s:build` command SHALL sit alone on
its own line, separated from that sentence by a blank line — never inline
mid-sentence, and both SHALL follow the one-sentence summary.

#### Scenario: Plan without build
- **WHEN** a user invokes `shipd:plan` directly and the flow completes
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

#### Scenario: A Summary heading closes the hand-off
- **WHEN** the plan flow hands off, from a fresh plan or from enrichment
- **THEN** a `## Summary` heading appears after the motivation-led body,
  followed by one sentence stating what the change does and why, and the
  build pointer comes after that sentence

#### Scenario: The summary sentence names no file
- **WHEN** the hand-off's one-sentence summary is printed
- **THEN** it reads in plain words, such as "We're making X, so Y", and
  carries no path or artifact name
