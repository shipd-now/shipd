# video-ingest-pipeline
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Turn a screen recording into a speaker-attributed transcript bundle on the
local machine, with a preflight that refuses to run half-configured.

### Motivation

Every remaining member of the `video-ingest` epic reads a bundle that nothing
produces yet — there is no demux, no transcription, no diarization, and no
on-disk contract for them to consume.

### Details

- Add `video_ingest.py` (stdlib) with `doctor [--fix]`, `ingest <video>`, and
  `path <slug>` verbs under `plugins/s/skills/video-ingest/scripts/`.
- Add three PEP 723 backend scripts under `scripts/backends/`: `asr_parakeet.py`
  (default), `asr_whisper.py`, `diarize_sherpa.py`, invoked via `uv run`.
- Freeze the bundle contract: `manifest.json`, `audio.wav`, `transcript.json`
  under a bundle root resolved from `build.video_dir` (default `~/.shipd/video`).
- Attribute words to speakers by maximum temporal overlap.
- Add `plugins/s/skills/video-ingest/tests/` and its own `ci.yml` step.

Affected capabilities: `video-pipeline` (added). Impact: the new
`plugins/s/skills/video-ingest/` tree, `.github/workflows/ci.yml`, and the
plugin version in `plugins/s/.claude-plugin/plugin.json`. No repo
dependencies: the orchestrator is stdlib and backends resolve their own via
`uv`.

### Non-goals

- No frame extraction — the sibling `video-ingest-frames` member owns it, and
  this member only creates the empty `frames/` slot in the bundle.
- No speaker naming, `afplay` sampling, or roster persistence — that is
  `video-ingest-speakers`.
- No intent brief authoring — `video-ingest-skill` reads the bundle and writes
  the brief through the already-shipped `spec_emit.py video` verb.
- No `SKILL.md`; this member ships scripts and tests only, so the directory is
  not yet a loadable skill.
- No forced phoneme alignment (epic D6) and no pyannote backend — pyannote is
  reachable through the adapter seam but is not written here.
- No streaming or live capture; offline files only.

## Implementation

**Process boundaries carry every dependency (epic D5).** `video_ingest.py`
imports only the standard library and reaches everything else by subprocess:
`ffmpeg`/`ffprobe` as CLIs, and each backend as a `uv run` script carrying PEP
723 inline metadata. Nothing enters `requirements.txt`; the Ubuntu `ci` job
never installs `mlx`. Rejected: a `requirements-video.txt` with direct imports —
it breaks Linux CI and the constitution's stdlib rule.

**Runners are injectable, following `review_gate.py`'s `gh`-runner
precedent.** Every subprocess call goes through a runner with signature
`run(args, input=None) -> (rc, stdout, stderr)` that tests substitute. This is
what makes the member testable at all: CI has no ffmpeg, no `uv`, and no Metal,
so the suite drives fakes and never a real transcription.

**Paths are passed as argument lists, never interpolated into a shell
string.** The verification recording is named `Screen Recording … 11.00.10 am
.mov` where the space before `am` is U+202F (narrow no-break space) — macOS
writes it into every timestamped recording filename. Slug derivation therefore
normalizes Unicode whitespace and any non-alphanumeric run to a single `-`,
lowercases, and strips leading/trailing separators.

**The backend contract is one line, so backends stay swappable:** a backend
receives `--audio <wav>` and prints a single JSON object to stdout. ASR
backends print `{"words": [{"start", "end", "text"}], "model": …}`;
diarization backends print `{"turns": [{"start", "end", "speaker"}], "model":
…}`. A non-zero exit or unparseable stdout fails the ingest with the backend's
stderr attached — never a partial bundle.

**Backend selection (epic D3, D4):** `--asr parakeet|whisper` defaults to
`parakeet`, `--diarizer sherpa` defaults to `sherpa`, both overridable via the
resolved config's `build.video_asr` / `build.video_diarizer` keys.

**`join(words, turns)` is a pure function** — no I/O, no subprocess — because it
is the part that determines correctness. Each word takes the speaker of the turn
it most overlaps; a word overlapping nothing takes the nearest turn within
250 ms, else `null`; an exact tie takes the earlier turn, so the result is
deterministic.

**Bundle placement follows `design.py` (epic D8).** The root resolves from the
layered config's `build.video_dir`, home-expanded, defaulting to `~/.shipd/video` —
outside any repository, so recordings and audio never reach a checkout or a PR.
An existing bundle is refused unless `--force`, mirroring the emit engine.

**`doctor` follows `semdiff.py`'s tiered-DEPS precedent**, and network access is
confined to `--fix`, which installs `ffmpeg` and `uv` via Homebrew and pre-warms
the model cache. The model download is ~600 MB (parakeet) and ~1.5 GB
(whisper-large-v3-turbo), so `doctor` reports cache state explicitly rather than
letting a first ingest stall for minutes.

Risk: the three backend scripts call third-party APIs that CI can never
exercise, so "tests green" does not mean "it transcribes." Guarded by a
mandatory manual verification task run against the supplied 48-second recording,
whose observed output is recorded in the task list — a green suite alone does
not close this change. Second risk: that recording appears to carry a single
speaker, so multi-speaker attribution is proven by unit tests over synthetic
turns rather than end to end.
