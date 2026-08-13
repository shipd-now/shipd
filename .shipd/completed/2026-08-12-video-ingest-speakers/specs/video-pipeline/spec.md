## MODIFIED Requirements

### Requirement: Bundle contract
id: video-bundle-contract
base: d96f45753085

`video_ingest.py` SHALL write each ingest to `<video-root>/<slug>/` holding
`manifest.json`, `audio.wav`, `transcript.json`, `frames.json`, a `frames/`
directory holding the extracted keyframes, and a `samples/` directory holding
per-speaker audio samples once the `samples` verb has run, where `<video-root>`
resolves from the layered configuration's `build.video_dir` key, home-expanded,
defaulting to `~/.shipd/video` — a location outside any repository. A `path <slug>`
verb SHALL print that absolute directory. `manifest.json` SHALL record the
source path, duration, size, the selected ASR and diarization backends, and
their reported models. If the bundle directory already exists, then `ingest`
SHALL refuse unless `--force` is given.

#### Scenario: Bundle lands outside the repository
- **WHEN** `ingest` completes on a recording
- **THEN** `<video-root>/<slug>/` holds `manifest.json`, `audio.wav`,
  `transcript.json`, `frames.json`, and `frames/`, and no file is written inside
  the repository

#### Scenario: Configured root overrides the default
- **WHEN** the resolved configuration sets `build.video_dir`
- **THEN** `path <slug>` resolves under that root rather than `~/.shipd/video`

#### Scenario: Existing bundle is refused
- **GIVEN** `<video-root>/<slug>/` already exists
- **WHEN** `ingest` runs without `--force`
- **THEN** it exits non-zero and the existing bundle is untouched

#### Scenario: Samples land inside the bundle
- **WHEN** the `samples` verb runs against an existing bundle
- **THEN** the clips are written under that bundle's `samples/` directory, still
  outside any repository

## ADDED Requirements

### Requirement: Per-speaker audio samples
id: video-speaker-samples

`video_ingest.py` SHALL provide a `samples <slug>` verb writing one audio clip
per distinct speaker label in the bundle's transcript into the bundle's
`samples/` directory, cutting each clip from `audio.wav` through the injectable
runner. Each clip SHALL be taken from that label's **longest** turn and its
duration SHALL be `min(SAMPLE_SECONDS, that turn's duration)`, so a clip never
extends past the speaker's own audio. Selecting the source window SHALL be a
pure function over the transcript.

#### Scenario: A clip is cut per speaker label
- **WHEN** `samples` runs on a bundle whose transcript holds two labels
- **THEN** two clips are written into `samples/`, one named for each label

#### Scenario: A short speaker yields a short clip
- **WHEN** a label's longest turn is shorter than `SAMPLE_SECONDS`
- **THEN** its clip duration is that turn's duration, not `SAMPLE_SECONDS`

#### Scenario: The clip comes from the speaker's longest turn
- **WHEN** a label holds several turns of differing length
- **THEN** the selected window falls inside that label's longest turn

### Requirement: Speaker label merging
id: video-speaker-merge

`video_ingest.py` SHALL provide a `merge-speakers <slug>` verb that, given a
mapping of speaker labels to names, relabels the transcript's words to the
assigned names, re-assembles segments with the existing assembly so no two
adjacent segments carry the same speaker, and writes `transcript.json` back.
The verb SHALL record the applied mapping in `manifest.json` under a
`speaker_merges` entry, so a rewrite is auditable after the fact. Where the
mapping assigns distinct names to every label, no labels SHALL be merged.

#### Scenario: Two labels under one name become one speaker
- **WHEN** `merge-speakers` applies a mapping giving two labels the same name
- **THEN** the rewritten transcript carries that single name and no two adjacent
  segments share a speaker

#### Scenario: The rewrite is recorded in the manifest
- **WHEN** a merge is applied
- **THEN** `manifest.json` carries a `speaker_merges` entry naming which labels
  were folded into which name

#### Scenario: Distinct names merge nothing
- **WHEN** the mapping assigns a different name to every label
- **THEN** the transcript's speaker count is unchanged

### Requirement: Speaker roster persistence
id: video-speaker-roster

`video_ingest.py` SHALL provide a `roster --add <name>…` verb appending names to
the resolved project configuration's `build.video_speakers` list, preserving
every other key in that file and creating the file only where absent. Names
already present SHALL NOT be duplicated. The roster SHALL hold names only — no
speaker embeddings or other biometric data — and SHALL NOT be applied
automatically to any diarization label.

#### Scenario: A name is added without disturbing other config
- **WHEN** `roster --add Mikk` runs against a config carrying other `build` keys
- **THEN** `build.video_speakers` gains `Mikk` and every other key is unchanged

#### Scenario: Re-adding a known name is a no-op
- **WHEN** a name already in the roster is added again
- **THEN** the list is unchanged and the command still exits zero

#### Scenario: The roster never carries biometric data
- **WHEN** the roster is written
- **THEN** it holds only names, with no embedding or voiceprint field
