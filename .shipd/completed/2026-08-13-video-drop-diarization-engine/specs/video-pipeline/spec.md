## MODIFIED Requirements

### Requirement: Dependency preflight
id: video-doctor-preflight
base: 956f14d61adf

`video_ingest.py` SHALL provide a `doctor [--fix]` verb reporting each
prerequisite against a tier — `ffmpeg` and `uv` required, the ASR model caches
recommended — printing a per-tool state and a concrete install hint, and exiting
non-zero when a required tool is missing. No reported prerequisite SHALL be a
diarization model or require a credentialed or gated model. If `--fix` is given,
then the verb SHALL install the required tools via Homebrew and pre-warm the ASR
model caches; network access SHALL occur only under `--fix`. If a required tool
is missing, then `ingest` SHALL refuse before extracting any audio.

#### Scenario: Missing required tool fails the check
- **WHEN** `doctor` runs with `ffmpeg` absent
- **THEN** it prints `ffmpeg` as missing with an install hint and exits non-zero

#### Scenario: Cold model cache is reported, not fatal
- **WHEN** `doctor` runs with every required tool present but no ASR model
  cached
- **THEN** it reports the cache as recommended-and-absent, names the download
  size, and exits zero

#### Scenario: Ingest refuses a missing prerequisite
- **WHEN** `ingest` runs while a required tool is missing
- **THEN** it reports the missing tool and exits non-zero without writing a
  bundle directory

#### Scenario: No prerequisite is a diarization or credentialed model
- **WHEN** `doctor` runs with every cache cold and no `HF_TOKEN` set
- **THEN** no reported entry names a diarization model, a token, or gated
  access, and the verb exits zero

### Requirement: Bundle contract
id: video-bundle-contract
base: fa56cba6d312

`video_ingest.py` SHALL write each ingest to `<video-root>/<slug>/` holding
`manifest.json`, `audio.wav`, `transcript.json`, `frames.json`, and a `frames/`
directory holding the extracted keyframes, where `<video-root>` resolves from
the layered configuration's `build.video_dir` key, home-expanded, defaulting to
`~/.shipd/video` — a location outside any repository. A `path <slug>` verb SHALL
print that absolute directory. `manifest.json` SHALL record the source path,
duration, size, the selected ASR backend, and its reported model, and SHALL NOT
record any diarization backend, diarization model, or speaker count. If the
bundle directory already exists, then `ingest` SHALL refuse unless `--force` is
given.

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

#### Scenario: The manifest records no diarization
- **WHEN** `ingest` completes
- **THEN** `manifest.json` names the ASR backend and its model and carries no
  diarizer, diarization, or speaker-count field

### Requirement: Pluggable transcription backends
id: video-backend-adapters
base: c0a575cd7e87

`video_ingest.py` SHALL invoke transcription as a separate `uv run` script
carrying PEP 723 inline dependency metadata, receiving `--audio <wav>` and
printing one JSON object to stdout — a `words` array of `{start, end, text}`
plus its `model`. Where a vocabulary is configured, the orchestrator SHALL
additionally pass `--vocab <terms>` to the ASR backend, and every ASR backend
SHALL accept that option — a backend with no biasing mechanism ignoring it
rather than failing. The ASR backend SHALL be selectable as `parakeet` (default)
or `whisper`, via `--asr` or the configuration's `build.video_asr` key, resolved
through a backend table so a further backend can be added as a table entry. If
the backend exits non-zero or prints unparseable stdout, then `ingest` SHALL
fail with the backend's stderr attached and SHALL NOT leave a partial bundle.

#### Scenario: The default backend is selected without flags
- **WHEN** `ingest` runs with no backend flag and no configuration override
- **THEN** the parakeet ASR backend is invoked and `manifest.json` records it

#### Scenario: Flag overrides the configured backend
- **WHEN** `ingest --asr whisper` runs while the configuration selects
  `parakeet`
- **THEN** the whisper backend is invoked

#### Scenario: A diarizer option is rejected
- **WHEN** `ingest --diarizer sherpa` or `ingest --speakers 2` runs
- **THEN** the invocation is rejected as an unrecognized argument and no bundle
  directory is written

#### Scenario: Backend failure leaves no partial bundle
- **WHEN** the backend exits non-zero
- **THEN** the ingest fails reporting the backend's stderr, and the bundle
  directory does not exist afterward

#### Scenario: Every ASR backend accepts the vocabulary option
- **WHEN** an ASR backend is invoked with `--vocab` while having no biasing
  mechanism
- **THEN** it ignores the option and transcribes normally rather than exiting
  non-zero

### Requirement: Transcript schema
id: video-transcript-schema
base: 72cdff421de3

`transcript.json` SHALL carry a schema `version` and a `words` array whose
entries hold `start`, `end`, and `text`, ordered by `start`. It SHALL NOT carry
a `segments` array, nor any speaker field on the transcript or on a word.

#### Scenario: Words are ordered and speaker-free
- **WHEN** a transcript is written
- **THEN** its `words` entries carry only `start`, `end`, and `text`, ordered by
  start time

#### Scenario: No segments array is written
- **WHEN** a transcript is written
- **THEN** the document holds `version` and `words` and no `segments` key

## REMOVED Requirements

### Requirement: Word-level speaker attribution
id: video-speaker-attribution
base: 24cd2879971b
Reason: Attribution maps ASR words onto diarization turns; with no diarizer there are no turns to map onto, and its output was never read by any consumer.
Migration: Word entries lose their `speaker` key. Anything reading it should anchor on `start`/`end`/`text`, which the skill already mandates ("anchor on words, never on segments").

### Requirement: Spurious diarization turns are filtered
id: video-spurious-turn-filter
base: 237682e78f79
Reason: The filter exists to suppress diarization artefacts; with diarization removed there are no turns to filter.
Migration: None — the filter was internal to turn processing and had no external surface.

### Requirement: Per-speaker audio samples
id: video-speaker-samples
base: 384ab1f19aa2
Reason: The `samples` verb cuts one clip per diarization label to support the speaker-naming round, both of which this change removes.
Migration: The `samples` verb is gone and `<bundle>/samples/` is no longer part of the bundle layout; invoking it fails as an unrecognized command. Existing sample directories are inert and may be deleted by hand.

### Requirement: Speaker label merging
id: video-speaker-merge
base: 84808980dc67
Reason: `merge-speakers` rewrites a transcript's diarization labels to names; with no labels written there is nothing to merge.
Migration: The `merge-speakers` verb is gone and fails as an unrecognized command. Bundles already carrying merged names keep them as inert data.

### Requirement: Speaker roster persistence
id: video-speaker-roster
base: 61cdb295f492
Reason: The roster persists speaker names to offer as candidates in the naming round, which this change removes along with the `roster` verb that writes it.
Migration: The persisted roster is abandoned and the `roster` verb that wrote it is gone, failing as an unrecognized command. No tracked configuration in this repository carries a `build.video_speakers` key, and a copy surviving in a local or workspace configuration is inert — config reads are `.get()` lookups and no key names are validated — so no edit is required anywhere.

### Requirement: Configured speaker count constrains clustering
id: video-speaker-count
base: 4b970bd36e2b
Reason: The count constrains diarization clustering, which no longer runs.
Migration: `--speakers` is removed from the CLI, so a script passing it fails outright — argparse exits non-zero with `unrecognized arguments` rather than ignoring the option. A `build.video_speakers_count` key left in a configuration is inert and needs no edit.

### Requirement: Pyannote diarization backend
id: video-diarizer-pyannote
base: d6c1b9b2072f
Reason: One of the two diarization backends this change removes; it additionally required accepted model terms and an exported `HF_TOKEN` to load at all.
Migration: `--diarizer` is removed from the CLI and fails as an unrecognized argument. A `build.video_diarizer` key left in a configuration is inert.

### Requirement: Diarization outcome is reported
id: video-diarization-report
base: 33cc1fdeeed8
Reason: The report summarises the diarizer's label count and per-label speech time; with no diarizer there is no outcome to report.
Migration: None — the report was printed to stderr during ingest and persisted nothing a consumer reads.

### Requirement: Pyannote backend tracks its pinned API
id: video-pyannote-api-contract
base: 8f93c4c2253b
Reason: It constrains the API call and dependency pin of `diarize_pyannote.py`, which this change deletes, so the requirement has no subject left.
Migration: None — no remaining backend declares a `pyannote.audio` dependency.
