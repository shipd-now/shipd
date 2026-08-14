## MODIFIED Requirements

### Requirement: Speaker naming and decider arbitration
id: video-skill-arbitration
base: fe870bcaa73c

The skill SHALL populate the brief's `## Speakers` section by mining the
transcript for self-identification and direct address. Where **two or more**
labels remain unnamed after mining, the skill SHALL run one naming round: cut
per-speaker clips with `video_ingest.py samples`, play each with `afplay`, state
how many seconds of speech that label holds, offer any names already in
`build.video_speakers` as candidates, and ask for a name per label — then apply
the answers with `merge-speakers` and persist new names with `roster --add`.
Where fewer than two labels remain unnamed, the skill SHALL ask nothing and use
the diarization label as the name. If playback fails or `afplay` is
unavailable, then the round SHALL continue using a transcript excerpt from that
label's longest turn rather than blocking. Where two speakers state conflicting
intents about the same target and a decider is configured, the decider's
**latest** statement SHALL be the recorded outcome and every superseded
statement SHALL be retained with its speaker and timestamp. If no decider is
configured, then a conflict SHALL be recorded under `## Open questions` rather
than resolved silently.

#### Scenario: A spoken name replaces the label
- **WHEN** the transcript addresses a speaker by name
- **THEN** that name appears in `## Speakers` mapped to the diarization label

#### Scenario: Two unnamed labels trigger one naming round
- **WHEN** mining leaves two labels unnamed
- **THEN** the skill cuts and plays a clip per label, reports each label's
  speech duration, and asks for a name for each in a single round

#### Scenario: One unnamed label asks nothing
- **WHEN** mining leaves only one label unnamed
- **THEN** no naming round runs and that label is used as its own name

#### Scenario: The roster is offered but never auto-applied
- **WHEN** `build.video_speakers` holds names and a naming round runs
- **THEN** those names are offered as candidates and none is assigned to a label
  without the user choosing it

#### Scenario: Failed playback does not block the round
- **WHEN** `afplay` is unavailable or a clip fails to play
- **THEN** the round continues using a transcript excerpt for that label

#### Scenario: The decider's latest word wins and the loser is kept
- **WHEN** a decider contradicts an earlier statement about the same target
- **THEN** the decider's later statement is the recorded intent and the
  superseded statement is retained with its speaker and timestamp

#### Scenario: A conflict with no decider is left unresolved
- **WHEN** speakers conflict and no decider is configured
- **THEN** the conflict appears under `## Open questions` and neither position
  is recorded as the outcome
