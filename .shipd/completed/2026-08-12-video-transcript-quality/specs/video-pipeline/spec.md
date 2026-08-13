## MODIFIED Requirements

### Requirement: Pluggable transcription and diarization backends
id: video-backend-adapters
base: 00227481453a

`video_ingest.py` SHALL invoke transcription and diarization as separate
`uv run` scripts carrying PEP 723 inline dependency metadata, each receiving
`--audio <wav>` and printing one JSON object to stdout — an ASR backend a
`words` array of `{start, end, text}` plus its `model`, a diarization backend a
`turns` array of `{start, end, speaker}` plus its `model`. Where a vocabulary is
configured, the orchestrator SHALL additionally pass `--vocab <terms>` to the
ASR backend, and every ASR backend SHALL accept that option — a backend with no
biasing mechanism ignoring it rather than failing. The ASR backend SHALL be
selectable as `parakeet` (default) or `whisper` and the diarization backend as
`sherpa` (default), via `--asr` / `--diarizer` or the configuration's
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

#### Scenario: Every ASR backend accepts the vocabulary option
- **WHEN** an ASR backend is invoked with `--vocab` while having no biasing
  mechanism
- **THEN** it ignores the option and transcribes normally rather than exiting
  non-zero

## ADDED Requirements

### Requirement: Configured vocabulary biases transcription
id: video-vocabulary-biasing

Where the resolved configuration's `build.video_vocabulary` key holds a
non-empty list of terms, `video_ingest.py` SHALL pass them to the ASR backend as
a single comma-separated `--vocab` value, and the whisper backend SHALL apply
them as Whisper's `initial_prompt` so the decoder is biased toward them. If the
key is absent or empty, then no `--vocab` argument SHALL be passed and
transcription behaviour SHALL be unchanged. The parakeet backend SHALL document
that it accepts and ignores `--vocab`, because `parakeet_mlx` exposes no
biasing parameter.

#### Scenario: Configured terms reach the whisper backend
- **WHEN** `build.video_vocabulary` lists domain terms and `ingest --asr
  whisper` runs
- **THEN** the whisper backend is invoked with a `--vocab` argument carrying
  those terms, and applies them as its `initial_prompt`

#### Scenario: Absent vocabulary changes nothing
- **WHEN** no `build.video_vocabulary` key is configured
- **THEN** the ASR backend is invoked with no `--vocab` argument

#### Scenario: Parakeet tolerates a configured vocabulary
- **WHEN** `build.video_vocabulary` is configured and the default parakeet
  backend runs
- **THEN** the ingest succeeds and the transcript is produced, the option having
  been ignored

### Requirement: Spurious diarization turns are filtered
id: video-spurious-turn-filter

`video_ingest.py` SHALL expose a pure function that filters a diarization turn
list before speaker attribution, dropping a turn only where **all** of the
following hold: its duration is below the module's spurious-turn threshold, a
turn exists both before and after it, and those two neighbouring turns carry the
same speaker, which differs from the short turn's speaker. A dropped turn's time
span SHALL be absorbed by that surrounding speaker so no span is left
unattributed. Where any condition fails, the turn SHALL be kept unchanged. The
function SHALL perform no I/O.

#### Scenario: Interruption inside one speaker is absorbed
- **WHEN** a 1.2-second turn for one speaker sits between two turns that both
  belong to a single different speaker
- **THEN** it is dropped and its span is absorbed by the surrounding speaker, so
  words in that span are attributed to the surrounding speaker

#### Scenario: Short turn at a real speaker boundary survives
- **WHEN** a short turn sits between two turns belonging to two *different*
  speakers
- **THEN** it is kept, because the surrounding turns do not agree

#### Scenario: Short turn at the recording edge survives
- **WHEN** a short turn is the first or last turn, so it has no neighbour on one
  side
- **THEN** it is kept

#### Scenario: Long turns are never dropped
- **WHEN** a turn at or above the threshold sits between two same-speaker turns
- **THEN** it is kept unchanged
