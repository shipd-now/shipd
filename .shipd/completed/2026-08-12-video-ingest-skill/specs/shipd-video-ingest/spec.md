## ADDED Requirements

### Requirement: Staged bundle-to-brief pipeline
id: video-skill-pipeline

The `/s:video-ingest` skill SHALL turn a screen recording into an intent brief
by running a staged pipeline in skill instructions: confirm the toolchain with
`video_ingest.py doctor`, obtain a bundle by ingesting a supplied video or
reusing a supplied slug, read the bundle's `transcript.json` and `frames.json`,
extract candidate intents, ground them on frames, and compose the brief. If
`doctor` reports a missing required tool, then the skill SHALL report it and
stop rather than proceed. If no actionable intent can be extracted, then the
skill SHALL report that and install nothing, because the grammar requires at
least one intent.

#### Scenario: A video argument is ingested then read
- **WHEN** `/s:video-ingest` is invoked with a path to a recording
- **THEN** the skill produces a bundle for it and composes the brief from that
  bundle's transcript and frames

#### Scenario: An existing bundle is reused
- **WHEN** the skill is invoked with a slug naming a bundle that already exists
- **THEN** it reads that bundle rather than re-ingesting the recording

#### Scenario: A missing prerequisite stops the run
- **WHEN** `doctor` reports a required tool missing
- **THEN** the skill reports the missing tool and stops without composing a
  brief

#### Scenario: A recording with no actionable intent installs nothing
- **WHEN** no actionable intent can be extracted from the transcript
- **THEN** the skill reports that and no brief is installed

### Requirement: Word-anchored frame grounding
id: video-skill-frame-grounding

The skill SHALL anchor each intent on the start time of the transcript **words**
expressing it, never on the enclosing segment, and SHALL cite the entry in
`frames.json` nearest that anchor. The skill SHALL read only the frames its
candidate intents anchor to, rather than every frame in the bundle. Where a
frame's visible content contradicts the transcript's wording, the brief SHALL
state what the frame shows and note the transcript's wording, rather than
repeating a misheard term as fact.

#### Scenario: Anchoring uses words, not segments
- **WHEN** an intent is expressed inside a segment spanning tens of seconds
- **THEN** its anchor is the start time of the words expressing it, and the
  cited frame is the one nearest that time

#### Scenario: Only anchored frames are read
- **WHEN** a bundle holds many frames and the candidate intents anchor to a few
- **THEN** the skill reads only those frames

#### Scenario: The frame corrects a misheard term
- **WHEN** the transcript's wording for an on-screen element disagrees with what
  the cited frame shows
- **THEN** the brief states the frame's version and notes the transcript's
  wording rather than asserting the misheard term

### Requirement: Speaker naming and decider arbitration
id: video-skill-arbitration

The skill SHALL populate the brief's `## Speakers` section by mining the
transcript for self-identification and direct address, falling back to the
diarization label as the name where no name is spoken. Where two speakers state
conflicting intents about the same target and a decider is configured, the
decider's **latest** statement SHALL be the recorded outcome and every
superseded statement SHALL be retained with its speaker and timestamp. If no
decider is configured, then a conflict SHALL be recorded under
`## Open questions` rather than resolved silently.

#### Scenario: A spoken name replaces the label
- **WHEN** the transcript addresses a speaker by name
- **THEN** that name appears in `## Speakers` mapped to the diarization label

#### Scenario: An unnamed speaker keeps its label
- **WHEN** no name is spoken for a diarized speaker
- **THEN** the label is used as the name, so the section is still populated

#### Scenario: The decider's latest word wins and the loser is kept
- **WHEN** a decider contradicts an earlier statement about the same target
- **THEN** the decider's later statement is the recorded intent and the
  superseded statement is retained with its speaker and timestamp

#### Scenario: A conflict with no decider becomes an open question
- **WHEN** speakers conflict and no decider is configured
- **THEN** the conflict appears under `## Open questions` and neither position
  is recorded as the outcome

### Requirement: Engine-mediated brief emission
id: video-skill-brief-emission

The skill SHALL author the brief in a staging area and install it via
`spec_emit.py video <slug> --from <file>`, and SHALL NOT construct a path under
the content directory's `video/` folder in either direction. Every source entry
SHALL be formatted with a zero-padded `HH:MM:SS` timestamp followed by the
speaker, and every intent SHALL carry at least one citation marker resolving to
a listed source. On lint findings from the emit engine, the skill SHALL fix the
staged brief and re-run until the install exits zero.

#### Scenario: The brief reaches the tree through the engine
- **WHEN** the skill finishes composing a brief
- **THEN** it is installed with `spec_emit.py video` from a staging path, never
  written directly into the content directory

#### Scenario: Sub-hour timestamps are zero-padded
- **WHEN** an utterance occurs five minutes into a recording
- **THEN** its source entry opens with a three-field zero-padded timestamp that
  satisfies the shipped brief grammar

#### Scenario: An invalid brief never lands
- **WHEN** the emit engine reports findings for the staged brief
- **THEN** the skill fixes the staged file and re-runs, and the tree holds no
  brief until an install exits zero
