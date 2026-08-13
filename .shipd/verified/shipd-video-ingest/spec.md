# shipd-video-ingest

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

### Requirement: Engine-mediated brief emission
id: video-skill-brief-emission

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
