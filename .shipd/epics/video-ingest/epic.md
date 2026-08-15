# video-ingest
Status: complete
Theme: developer-experience

## Introduction

The cheapest way for a person to express a change to software they are looking
at is to record their screen and talk over it: point the cursor at the button,
say what is wrong with it, move on. That recording carries more grounded intent
per minute than any written brief — the speaker never has to name the element,
describe where it sits, or reconstruct the state the app was in. Today none of
that reaches `am`. The recording is watched by a human who retypes its content
as a prompt, losing the timestamps, the on-screen evidence, and — in a
multi-speaker recording — any record of who actually decided what.

This epic adds `/s:video-ingest`: a skill that turns a screen recording into a
spec-ready **intent brief**. Step one runs entirely on the local machine —
demux the audio, transcribe it with Apple-Silicon-native MLX models, diarize it
into speakers, and extract the handful of video frames that matter. Step two is
performed by the session itself, which reads that bundle, grounds each spoken
intent against the frame that was on screen when it was said, resolves
contradictions in favour of the designated decider, and writes a brief whose
every claim cites a timestamped, speaker-attributed utterance. `/s:plan` then
consumes that brief when the user supplies a video, routing to `/s:epic`
instead when the extracted intent is too broad for a single change.

The intended outcome is that "here's a two-minute video of what I want" becomes
a first-class entry point to the spec lifecycle, no less traceable than a typed
request. Success criteria: a recording of this repo's own delivery board, with
two speakers disagreeing and one of them deciding, produces a lint-clean brief
in which every intent carries a timestamp, a speaker, and a frame reference,
and the superseded position is recorded rather than dropped.

### Non-goals

- **No cloud transcription or vision APIs.** Every byte of step one stays on the
  machine; a recording of an unreleased product never leaves it.
- **No local vision-language model.** The reasoning session is already a strong
  GUI-reading VLM; a local Qwen2.5-VL adds VRAM pressure and worse output.
- **No second structured-output engine.** `spec_emit.py` plus `spec_lint.py`
  already provide validate-then-install with a fix-and-retry loop.
- **No forced phoneme alignment** (wav2vec2/CTC) in this epic — frame-window
  tolerance makes sub-200 ms word timing unnecessary.
- **No cross-recording speaker recognition by voiceprint.** Speakers are named
  per ingest; the config remembers names, not biometric embeddings.
- **No live or streaming ingest.** Offline files only.
- **No overlapping-speech separation**, and no inferring agreement from
  backchannels — both are known-lossy and are surfaced as such, not guessed.
- **Not a meeting-notes or summarization product.** The only output is
  actionable, spec-shaped intent.
- **No media in the repository.** Audio, frames, and raw transcripts never enter
  a checkout or a PR.
- **No non-macOS ASR backends.** Apple Silicon first; other platforms fail the
  preflight with a clear message rather than degrading silently.

## Decisions

Every member change inherits the following. They are recorded once here so no
member author re-derives or contradicts them.

### D1 — Only the audio/frame stage runs locally; the session is the vision model

The reference architecture this epic is drawn from
(`docs/research/Local Video Meeting Spec Extraction.md`) prescribes four local
phases: transcription/diarization, a local VLM, a local structured-output LLM,
and sequential VRAM orchestration. Two of those do not apply here. The skill
runs inside a session whose model already reads images natively and reasons
about GUIs better than a locally hosted 7B VLM would, and it already writes into
an engine that enforces structure. So the local pipeline stops after producing a
transcript and frames.

**Rejected:** a local Qwen2.5-VL (via `mlx-vlm`) as the frame analyst — it costs
14–16 GB of unified memory, forces a sequential load/unload graph with 30–90 s
cold starts, and produces a strictly weaker reading of the UI than the session
that must consume it anyway.

### D2 — No Pydantic/Instructor/Ollama layer

The research report's Phase III solves "force a probabilistic model to emit a
validated schema, and re-prompt it with the validation error until it complies".
This repository already has exactly that mechanism, aimed at a better target
than JSON: `spec_emit.py` validates in-process and installs nothing on a
finding, and the skills re-author and re-run until it exits zero.

**Rejected:** adding Ollama + Instructor + Pydantic — a second, weaker structured
output engine, three third-party dependencies, and a JSON intermediate nobody
downstream consumes.

### D3 — MLX-native ASR with two backends behind one adapter

WhisperX is the right *architecture* and the wrong *implementation* for this
hardware: its speed comes from `faster-whisper`/CTranslate2, which has no Metal
backend and therefore runs CPU-only on Apple Silicon. The MLX-native equivalents
carry the same word-level-timestamp contract with actual GPU acceleration. Both
ship, selected by flag and config:

- `parakeet-mlx` — default. Native word-level `AlignedToken` timings, fastest by
  a wide margin.
- `mlx-whisper` (`whisper-large-v3-turbo`) — `word_timestamps=True`; chosen when
  the audio is multilingual, heavily accented, or dense with domain jargon.

**Rejected:** WhisperX unmodified (CPU-bound here); a single hardcoded backend
(the two have genuinely different failure modes and the adapter seam is cheap).

### D4 — Diarization defaults to sherpa-onnx, with pyannote as an opt-in backend

Speaker diarization has no mature MLX-Python implementation; the Apple-Neural-
Engine options are Swift. Of the importable choices, `sherpa-onnx` runs an
ONNX-exported `pyannote-segmentation-3.0` plus 3D-Speaker embeddings on CPU in a
~6.6 MB model, with **no PyTorch dependency and no Hugging Face token or gated-
model acceptance**. That preflight friction is decisive: a first run on a clean
Mac must not stall on a licence click-through. `pyannote.audio` 3.1/community-1
is the more accurate backend for difficult audio and is selectable through the
same adapter seam as D3.

**Rejected:** pyannote as the default (torch + gated-model auth on first run);
Swift/CoreML diarizers (not callable from the Python orchestrator).

### D5 — The orchestrator is stdlib; every heavy dependency is a subprocess

`.shipd/constitution.md` binds the engine to stdlib-only Python 3, and `mlx` is
macOS-only — putting it in `requirements.txt` would break the Ubuntu `ci` job.
So the orchestrator imports nothing outside the standard library and reaches its
dependencies through process boundaries: `ffmpeg`/`ffprobe` as CLIs, and the ASR
and diarization backends as **`uv run` scripts carrying PEP 723 inline
dependency metadata**, which resolve into a cached ephemeral environment. No
dependency enters the repository, CI never installs `mlx`, and every test stubs
the subprocess boundary.

**Rejected:** a `requirements-video.txt` and direct imports (breaks Linux CI and
the stdlib rule); vendoring the models (hundreds of MB in git).

### D6 — Word-to-speaker attribution by maximum temporal overlap; no forced alignment

Each word is assigned the speaker whose diarization turn it most overlaps.
Forced phoneme alignment is deliberately skipped: it exists to reach ±200 ms,
and this pipeline's timing consumer is a *frame window* (t−0.5 s to t+1.5 s),
which tolerates ±500 ms without changing what the session sees. The adapter seam
leaves room to add it if a member later proves otherwise.

### D7 — Frame selection is a context budget, not a sampling rate

Frames are never sampled at a fixed FPS. The selected set is the union of
scene-change keyframes (`ffmpeg select='gt(scene,N)'`, catching UI transitions)
and **deixis-anchored** frames — a window around each demonstrative in the
transcript ("this", "here", "that button", "right there"), because a person
points slightly before and after they speak. The set is then deduplicated,
downscaled to a long edge of ~1568 px, and hard-capped. **Truncation is always
logged explicitly**; a capped frame set that silently reads as complete coverage
is a correctness bug, not a performance trade.

### D8 — Heavy artifacts live outside the repository; only the brief enters it

The bundle — extracted audio, frames, raw transcript JSON — is written to a
global scratch root (default `~/.shipd/video/<slug>`, overridable via the resolved
config), following the precedent `design.py` set for design scratch
directories: a location deliberately outside the consuming repository so nothing
large or private lands in a checkout or a PR. Only `brief.md` is installed into
the content directory.

### D9 — The intent brief is a first-class artifact with its own emit verb

This repository's pattern is one artifact kind per emit verb plus one lint mode
(`change`, `initiative`, `epic`, `research`, `wiki`). The brief follows it:
`spec_emit.py video <slug> --from <file>` installs to
`<content-dir>/video/<slug>/brief.md`, validated by a matching `spec_lint.py`
mode. Its grammar borrows research's citation discipline — every load-bearing
intent carries an inline `[n]` marker resolving to a numbered source, where a
source is a **timestamped, speaker-attributed utterance plus its frame
reference**. An unciteable claim goes in gaps-and-caveats, never in the intents.

**Rejected:** installing briefs through `spec_emit.py research` — the citation
grammar fits, but a recording-derived brief is not research, and overloading
`research/` would make both artifact kinds ambiguous to readers and to
`/s:epic`'s link validation.

### D10 — Speakers are named by the user, assisted but never guessed silently

Diarization emits `SPEAKER_00`-style labels. Resolution is layered: first mine
the transcript for self-identification and address ("Sarah, what do you think?"
immediately before a turn); then, for every speaker still unnamed, extract a
representative **5-second sample**, play it locally (`afplay`), and ask the user
to name that voice. Confirmed names persist to the resolved config as a roster
that is offered first on later ingests. The roster stores **names only** — no
speaker embeddings, no biometric data on disk.

### D11 — The decider's latest word wins, and losers are recorded

One speaker may be designated the decider. Where two speakers state conflicting
intents about the same target, the decider's **latest** utterance is the
outcome, and every superseded statement is retained in the brief as a rejected
alternative with its speaker and timestamp — so a downstream plan can say why an
option lost. **Where no decider is designated, a conflict becomes an explicit
open question in the brief**; the pipeline never silently picks a winner.

### D12 — Known-lossy audio is reported, not papered over

Every backend in this class drops sub-second backchannels ("yeah", "right") at
the VAD stage and attributes overlapping speech to one voice. Consequently
**agreement is never inferred from a backchannel**, and regions flagged as
overlapping are marked low-confidence in the brief rather than transcribed
confidently.

### D13 — Preflight is mandatory and fails loudly

Because the toolchain is user-installed, macOS-only, and multi-component, a
`doctor` verb reports the status of every prerequisite with the exact command to
fix each one, and the pipeline refuses to run half-configured rather than
failing three minutes into a transcription.

### D14 — Video is an entry point to the existing flow, not a parallel one

`/s:video-ingest` is standalone (it produces a brief on its own) and is also a
pre-step to `/s:plan` when the request names a video. The brief feeds
investigation; it never displaces the codebase-first rule — the video says
*what* the user wants, the repository still says *how*. The choice between
planning one change and decomposing an epic reuses the **existing** epic
criteria; this epic introduces no competing scope heuristic.

## Design

The feature is a two-stage pipeline with a durable artifact between the stages,
plus two integration points into the existing skills.

```
stage 1 — local, on-device, no network            (members: pipeline, frames, speakers)

  video.mov ─▶ ffmpeg demux ─▶ 16 kHz mono wav ─┬─▶ ASR adapter    ─▶ words + timestamps ─┐
                                                │   parakeet-mlx | mlx-whisper            │
                                                └─▶ diarize adapter ─▶ speaker turns ─────┤
                                                    sherpa-onnx | pyannote                │
                                                                   max-overlap join ◀─────┘
                                                                          │
  video.mov ─▶ ffmpeg keyframes ─▶ scene-change ∪ deixis-anchored ─▶ dedup/cap ─┐
                                                                                ▼
                                              ~/.shipd/video/<slug>/  (bundle: wav, frames, transcript.json)
                                                                                │
stage 2 — the session is the analyst                     (member: skill)         ▼
                                        read transcript + frames ─▶ intent extraction
                                        ─▶ speaker naming ─▶ decider arbitration
                                                                                │
                                                                                ▼
                                    spec_emit.py video ─▶ <content-dir>/video/<slug>/brief.md
                                                                                │
stage 3 — routing                              (members: plan-entry, epic-entry) ▼
                              one capability ─▶ /s:plan ─▶ change   |   broad ─▶ /s:epic ─▶ members
```

**The seams the decomposition follows.**

- **Audio and video are independent producers** into the same bundle. The
  transcript is required to *select* deixis-anchored frames, but scene-change
  selection and the whole ffmpeg surface are separable, separately testable
  work — so frames are their own member.
- **Speaker naming is interactive; everything else in stage 1 is batch.** It
  needs sample extraction, local playback, a typed question round, and config
  persistence — a different shape from the rest of the pipeline, and the only
  part that blocks on a human.
- **The artifact contract is engine work under the constitution's stdlib rule**;
  the pipeline is skill-local scripting. They are governed by different rules and
  tested in different suites, so the emit verb and lint mode land first and
  independently.
- **The two integration points are small and additive** — a pre-step in
  `/s:plan`, and brief consumption in `/s:epic` — and each carries a delta
  against an existing verified capability rather than new machinery.
- **Cursor grounding is isolated at the end.** A ~20 px cursor on a 3000 px frame
  is close to invisible to any vision model; recovering it needs frame
  differencing and zoom crops. It is the highest-uncertainty piece, it improves
  an already-working brief rather than enabling it, and it is far easier to build
  once the bundle, frames, and brief formats are settled.

**Test and CI placement.** The engine member's tests join
`plugins/s/skills/build/tests/` (discovered by `ci`). The pipeline members
follow the `review` skill's precedent — `plugins/s/skills/video-ingest/tests/`
with its own `ci.yml` step — and stub every subprocess boundary so the suite
passes on Ubuntu with neither `ffmpeg`, `uv`, nor `mlx` installed.

**Skill instruction changes require an eval run** per `AGENTS.md`; the members
touching a `SKILL.md` (`video-ingest-skill`, `plan-video-entry`,
`epic-video-brief`) each carry one.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| video-brief-artifact | `spec_emit.py video` + `spec_lint.py` video mode installing `<content-dir>/video/<slug>/brief.md` with the timestamped-utterance citation grammar | medium | medium | low | low |
| video-ingest-pipeline | Stdlib `video_ingest.py` orchestrator: ffmpeg demux, ASR and diarization adapters over `uv run` PEP 723 scripts, max-overlap word attribution, bundle layout, `doctor` preflight | high | medium | high | medium |
| video-ingest-frames | Keyframe selection: scene-change plus deixis-anchored windows, dedup, downscale, hard cap with explicit drop logging | medium | low | medium | low |
| video-ingest-speakers | Speaker naming: transcript name mining, 5-second per-speaker samples played via `afplay`, typed naming round, name roster persisted to config | medium | medium | medium | low |
| video-ingest-skill | The `/s:video-ingest` SKILL.md: frame-grounded intent extraction, decider arbitration with superseded alternatives, brief authoring through the emit gate | medium | medium | medium | medium |
| plan-video-entry | `/s:plan` video pre-step and scope routing to `/s:epic`, with the `shipd-plan` delta and an eval case | low | high | low | medium |
| epic-video-brief | `/s:epic` consumes an intent brief as pre-investigation context and links it, mirroring its research handling | low | medium | low | low |
| video-cursor-grounding | Deferred cursor grounding: locate the pointer by frame differencing and emit zoom crops alongside full frames | medium | low | high | medium |
