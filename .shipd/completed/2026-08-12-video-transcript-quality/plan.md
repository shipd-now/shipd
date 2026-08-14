# video-transcript-quality
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Fix the two transcript defects the first real ingest exposed: domain terms are
misheard, and a spurious sub-second diarization turn tears a word out of a
continuous sentence.

### Motivation

Running the shipped pipeline on a real recording produced `auto mic delivery
board` for `shipd` and attributed the single word `header.` to a different
speaker mid-sentence — both of which would propagate into every intent brief
built on this transcript.

### Details

- Add a `build.video_vocabulary` config list of domain terms, passed to ASR
  backends as `--vocab` and applied by the whisper backend as Whisper's
  `initial_prompt`.
- Filter spurious diarization turns before attribution: drop a turn shorter than
  the threshold when the turns on both sides belong to the same *other* speaker,
  reassigning its span to that surrounding speaker.
- Leave `parakeet` as the default ASR backend.

Affected capabilities: `video-pipeline` (modified). Impact:
`plugins/s/skills/video-ingest/scripts/video_ingest.py`,
`scripts/backends/asr_whisper.py`, `scripts/backends/asr_parakeet.py`, the
suite under `plugins/s/skills/video-ingest/tests/`, and the plugin version in
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to the default ASR backend — `parakeet` stays default.
- No frame extraction, speaker naming, or brief authoring; those remain their
  own epic members.
- No pause-based segment splitting — segments still split on speaker change
  only.
- No attempt to fix `sensor aligned` → `centre-aligned`; both backends make that
  error identically and no vocabulary term reliably corrects it.
- No custom acoustic model, fine-tuning, or lexicon file.

## Implementation

**`parakeet` stays the default, on measured evidence.** Both backends were run
warm against the same 48-second recording: parakeet 10.0 s, whisper 37.1 s — a
3.7× cost. Whisper's only advantage on that clip was capitalisation
(`AutoMIC Delivery Board` vs `auto mic delivery board`); neither produced
`shipd`, and both made the identical `sensor aligned` error. Rejected:
switching the default to whisper — the accuracy difference measured did not
justify a 3.7× slowdown on every ingest.

**Vocabulary biasing is whisper-only, because only whisper has the hook.**
`mlx_whisper.transcribe` accepts `initial_prompt` (verified against the
installed signature); `parakeet_mlx`'s `transcribe` exposes only
`path, dtype, decoding_config, chunk_duration, overlap_duration,
chunk_callback` — no prompt, vocabulary, or context parameter. So `--vocab` is
part of the backend contract and every ASR backend must **accept** it, while a
backend without a biasing mechanism ignores it and says so in its docstring. A
future backend with biasing needs no contract change.

**The vocabulary lives in config, not in code.** `build.video_vocabulary` is a
list of strings resolved through the same layered configuration as
`build.video_dir` and `build.video_asr`, so a consuming repo declares its own
jargon. Rejected: hardcoding shipd's terms in the backend — wrong for every
other repo the plugin serves; and deriving terms from repo signals — zero
configuration but unpredictable, untestable, and silently different per branch.

The terms are joined into a single comma-separated `--vocab` value and the
whisper backend renders them into one `initial_prompt` sentence. An absent or
empty list passes no `--vocab` at all, so behaviour is byte-identical to today.

**The spurious-turn filter is deliberately conservative.** A turn is dropped
only when *all three* hold: it is shorter than `SPURIOUS_TURN_MAX_SECONDS`
(2.0), the turn before and the turn after both exist, and both belong to the
same speaker, which is **not** the short turn's speaker. Its time span is then
absorbed by that surrounding speaker. Rejected: a flat duration threshold — it
would discard a genuine brief reply ("yes, exactly") at a real speaker boundary,
which is exactly the multi-speaker signal this epic exists to capture; and a
word-count threshold — it ties a diarization defect to ASR output.

**The filter is a pure function running before `join`.** It takes and returns a
turn list, so `join(words, turns)` is unchanged and its existing scenarios
continue to hold. This placement is what makes the fix reach every consumer:
`transcript.json` is what all downstream epic members read, so correcting the
turns at the source is strictly better than each member compensating.

Risk: a recording where two speakers genuinely alternate in under two seconds
would have the interjection absorbed. The sandwich condition bounds this — the
interjection must be surrounded by one single other speaker — and the threshold
is a module constant, so the assumption is visible and adjustable rather than
buried.

**Epic membership drift is expected here.** This change carries
`Epic: video-ingest` but is not one of the epic's eight stub rows, so the linter
emits its membership-drift warning by design ("the decomposition may
legitimately grow"). The change is genuinely part of that epic's work and the
warning is the intended record of the growth.
