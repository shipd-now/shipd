## ADDED Requirements

### Requirement: Dependency preflight
id: video-doctor-preflight

`video_ingest.py` SHALL provide a `doctor [--fix]` verb reporting each
prerequisite against a tier — `ffmpeg` and `uv` required, the backend model
caches recommended — printing a per-tool state and a concrete install hint, and
exiting non-zero when a required tool is missing. If `--fix` is given, then the
verb SHALL install the required tools via Homebrew and pre-warm the backend
model caches; network access SHALL occur only under `--fix`. If a required tool
is missing, then `ingest` SHALL refuse before extracting any audio.

#### Scenario: Missing required tool fails the check
- **WHEN** `doctor` runs with `ffmpeg` absent
- **THEN** it prints `ffmpeg` as missing with an install hint and exits non-zero

#### Scenario: Cold model cache is reported, not fatal
- **WHEN** `doctor` runs with every required tool present but no backend model
  cached
- **THEN** it reports the cache as recommended-and-absent, names the download
  size, and exits zero

#### Scenario: Ingest refuses a missing prerequisite
- **WHEN** `ingest` runs while a required tool is missing
- **THEN** it reports the missing tool and exits non-zero without writing a
  bundle directory

### Requirement: Bundle contract
id: video-bundle-contract

`video_ingest.py` SHALL write each ingest to `<video-root>/<slug>/` holding
`manifest.json`, `audio.wav`, `transcript.json`, and an empty `frames/`
directory, where `<video-root>` resolves from the layered configuration's
`build.video_dir` key, home-expanded, defaulting to `~/.shipd/video` — a location
outside any repository. A `path <slug>` verb SHALL print that absolute
directory. `manifest.json` SHALL record the source path, duration, size, the
selected ASR and diarization backends, and their reported models. If the bundle
directory already exists, then `ingest` SHALL refuse unless `--force` is given.

#### Scenario: Bundle lands outside the repository
- **WHEN** `ingest` completes on a recording
- **THEN** `<video-root>/<slug>/` holds `manifest.json`, `audio.wav`,
  `transcript.json`, and `frames/`, and no file is written inside the repository

#### Scenario: Configured root overrides the default
- **WHEN** the resolved configuration sets `build.video_dir`
- **THEN** `path <slug>` resolves under that root rather than `~/.shipd/video`

#### Scenario: Existing bundle is refused
- **GIVEN** `<video-root>/<slug>/` already exists
- **WHEN** `ingest` runs without `--force`
- **THEN** it exits non-zero and the existing bundle is untouched

### Requirement: Audio extraction and slug derivation
id: video-audio-extraction

`video_ingest.py` SHALL extract the recording's audio to 16 kHz mono PCM WAV via
`ffmpeg`, passing every path as a subprocess argument-list element and never
interpolating one into a shell string. The bundle slug SHALL default to the
source filename with Unicode whitespace and every non-alphanumeric run folded to
a single `-`, lowercased and stripped of leading and trailing separators, and
SHALL be overridable with `--slug`. If the recording carries no audio stream,
then `ingest` SHALL report that and exit non-zero.

#### Scenario: macOS recording filename yields a clean slug
- **WHEN** `ingest` runs on a file named with a U+202F narrow no-break space
  before `am`, as macOS writes timestamped recordings
- **THEN** the derived slug contains only lowercase alphanumerics and single
  `-` separators, and the ffmpeg invocation receives the original path intact

#### Scenario: Audio is normalized for the backends
- **WHEN** audio extraction runs
- **THEN** `audio.wav` is 16 kHz mono PCM regardless of the source's rate or
  channel count

#### Scenario: Silent video is rejected
- **WHEN** `ingest` runs on a file with no audio stream
- **THEN** it reports the missing audio stream and exits non-zero

### Requirement: Pluggable transcription and diarization backends
id: video-backend-adapters

`video_ingest.py` SHALL invoke transcription and diarization as separate
`uv run` scripts carrying PEP 723 inline dependency metadata, each receiving
`--audio <wav>` and printing one JSON object to stdout — an ASR backend a
`words` array of `{start, end, text}` plus its `model`, a diarization backend a
`turns` array of `{start, end, speaker}` plus its `model`. The ASR backend SHALL
be selectable as `parakeet` (default) or `whisper` and the diarization backend
as `sherpa` (default), via `--asr` / `--diarizer` or the configuration's
`build.video_asr` / `build.video_diarizer` keys. If a backend exits non-zero or
prints unparseable stdout, then `ingest` SHALL fail with the backend's stderr
attached and SHALL NOT leave a partial bundle.

#### Scenario: Default backends are selected without flags
- **WHEN** `ingest` runs with no backend flags and no configuration override
- **THEN** the parakeet ASR backend and the sherpa diarization backend are
  invoked, and `manifest.json` records both

#### Scenario: Flag overrides the configured backend
- **WHEN** `ingest --asr whisper` runs while the configuration selects
  `parakeet`
- **THEN** the whisper backend is invoked

#### Scenario: Backend failure leaves no partial bundle
- **WHEN** a backend exits non-zero
- **THEN** the ingest fails reporting the backend's stderr, and the bundle
  directory does not exist afterward

### Requirement: Word-level speaker attribution
id: video-speaker-attribution

`video_ingest.py` SHALL expose speaker attribution as a pure function over the
ASR words and diarization turns, assigning each word the speaker of the turn it
most overlaps in time. Where a word overlaps no turn, it SHALL take the speaker
of the nearest turn within 250 ms and otherwise `null`. Where a word overlaps
two turns equally, it SHALL take the earlier turn, so the result is
deterministic. The function SHALL perform no I/O.

#### Scenario: Word takes its maximum-overlap speaker
- **WHEN** a word spans two turns and overlaps the second more
- **THEN** it is attributed to the second turn's speaker

#### Scenario: Orphan word falls back then yields null
- **WHEN** a word overlaps no turn but starts within 250 ms of one
- **THEN** it takes that turn's speaker, while a word further from every turn is
  attributed `null`

#### Scenario: Equal overlap resolves deterministically
- **WHEN** a word overlaps two turns by an identical duration
- **THEN** it is attributed to the earlier turn on every run

### Requirement: Transcript schema
id: video-transcript-schema

`transcript.json` SHALL carry a schema `version`, and a `segments` array whose
entries hold `start`, `end`, `speaker`, `text`, and a `words` array of
`{start, end, text, speaker}`. Segments SHALL be split at speaker changes so no
segment spans two speakers, and SHALL be ordered by `start`.

#### Scenario: Speaker change splits a segment
- **WHEN** consecutive words carry different attributed speakers
- **THEN** they land in separate segments, each single-speakered and ordered by
  start time

#### Scenario: Words retain their own attribution
- **WHEN** a transcript is written
- **THEN** every word entry carries its own `start`, `end`, `text`, and
  `speaker`

### Requirement: Dependency-free test surface
id: video-pipeline-testability

Every subprocess the pipeline runs SHALL go through an injectable runner with
signature `run(args, input=None) -> (rc, stdout, stderr)`, so the test suite
exercises the orchestrator with no `ffmpeg`, `uv`, or `mlx` installed. The suite
SHALL live at `plugins/s/skills/video-ingest/tests/` and SHALL be discovered by
its own `ci` step.

#### Scenario: Suite passes on a machine without the toolchain
- **WHEN** the video-ingest suite runs with no `ffmpeg`, `uv`, or `mlx` present
- **THEN** every test passes, driving fake runners rather than real tools

#### Scenario: CI discovers the suite
- **WHEN** the `ci` workflow runs
- **THEN** it discovers and runs `plugins/s/skills/video-ingest/tests/`
