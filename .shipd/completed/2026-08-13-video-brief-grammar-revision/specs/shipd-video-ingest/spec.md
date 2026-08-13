## ADDED Requirements

### Requirement: Conflicting intents resolve by recency
id: video-skill-conflict-recency

Where a recording states conflicting intents about the same target, the skill
SHALL record the **latest** statement as the outcome and SHALL retain every
superseded statement with its timestamp rather than dropping it. Where the
conflict cannot be resolved by recency — the statements are contemporaneous, or
the later one does not clearly supersede the earlier — the skill SHALL record it
under `## Open questions`, stating both positions with their timestamps and
leaving neither as the outcome. The skill SHALL NOT attribute a conflict's
resolution to a speaker.

#### Scenario: The later statement wins and the earlier is kept
- **WHEN** a recording states one intent about a target and later contradicts it
- **THEN** the later statement is the recorded intent and the superseded one is
  retained with its timestamp

#### Scenario: An unresolvable conflict is left open
- **WHEN** two conflicting statements about a target cannot be ordered by
  recency
- **THEN** both appear under `## Open questions` with their timestamps and
  neither is recorded as the outcome

## MODIFIED Requirements

### Requirement: Engine-mediated brief emission
id: video-skill-brief-emission
base: 013139dc51c6

The skill SHALL author the brief in a staging area and install it via
`spec_emit.py video <slug> --from <file>`, and SHALL NOT construct a path under
the content directory's `video/` folder in either direction. Every source entry
SHALL be formatted with a zero-padded `HH:MM:SS` timestamp followed by what was
said, and SHALL NOT name a speaker. Every intent SHALL carry at least one
citation marker resolving to a listed source. Where the project the recording's
feedback concerns is known — named at invocation, or resolvable because the
invoking repository is a declared project in the workspace registry — the skill
SHALL author a `Project:` header line carrying that project's declared slug;
where it is not known the skill SHALL omit the line rather than guess. On lint
findings from the emit engine, the skill SHALL fix the staged brief and re-run
until the install exits zero.

#### Scenario: The brief reaches the tree through the engine
- **WHEN** the skill finishes composing a brief
- **THEN** it is installed with `spec_emit.py video` from a staging path, never
  written directly into the content directory

#### Scenario: Source entries carry a timestamp and no speaker
- **WHEN** the skill composes a source entry
- **THEN** it opens with a zero-padded `HH:MM:SS` timestamp followed by what was
  said, naming no speaker

#### Scenario: A known project is recorded on the brief
- **WHEN** the skill composes a brief while the invoking repository resolves to
  a declared project slug
- **THEN** the installed brief carries a `Project:` header line holding that
  slug

#### Scenario: An unknown project is omitted rather than guessed
- **WHEN** no project is named at invocation and the invoking repository
  resolves to no declared project
- **THEN** the installed brief carries no `Project:` header line and still
  installs clean

#### Scenario: Sub-hour timestamps are zero-padded
- **WHEN** an utterance occurs five minutes into a recording
- **THEN** its source entry opens with a three-field zero-padded timestamp that
  satisfies the shipped brief grammar

#### Scenario: An invalid brief never lands
- **WHEN** the emit engine reports findings for the staged brief
- **THEN** the skill fixes the staged file and re-runs, and the tree holds no
  brief until an install exits zero

## REMOVED Requirements

### Requirement: Speaker naming and decider arbitration
id: video-skill-arbitration
base: 4268843743cb
Reason: Every mechanism it depends on is gone — the bundle carries no diarization labels, and the `samples`, `merge-speakers`, and `roster` verbs were deleted with the engine's diarization surface — so neither the naming round nor decider-based arbitration can run.
Migration: The brief no longer carries a `## Speakers` section, so nothing needs naming. Conflict resolution moves to `video-skill-conflict-recency`, which orders by timestamp instead of by a configured decider; a `Decider:` header line on an existing brief becomes inert metadata that the grammar ignores.
