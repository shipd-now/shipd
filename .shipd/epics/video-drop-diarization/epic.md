# video-drop-diarization
Status: complete
Theme: developer-experience

## Introduction

The `video-ingest` epic assumed a recording's value included **who said what**:
it diarizes the audio into speakers, names them through an interactive round,
persists a name roster, and arbitrates conflicting intents by a configured
decider. Measured against real audio, none of that works, and nothing consumes
it even when it does.

On a 19-minute two-person interview, three separate diarizers were scored
against a probe set derived from transcript content rather than from any
diarizer's own output. **None separated the two speakers.** sherpa emitted 161
turns split 684s/389s but placed 87% of its segment boundaries mid-sentence and
folded the interviewer into the interviewee's cluster on 3 of 5 probes; Reverb
v1 collapsed to 1056s/69s across 36 turns; Reverb v2 — a model 56× larger than
the one shipped — collapsed hardest of all, 1126s/23s across 23 turns. The
failure is not a tuning gap: better segmentation made attribution worse, and
the two Reverb models are non-production licensed while pyannote's pipeline is
gated behind a Hugging Face token and is built on the very segmentation model
sherpa already runs.

Meanwhile the output is unread. `## Speakers` is enforced by `spec_lint.py` and
described in the ingest skill, and no downstream consumer reads it — `/s:plan`
acts on the `### <intent title>` headings. The one brief this pipeline has
produced attributed its speakers from transcript *content*, overriding the
diarizer entirely, and is sound.

This epic removes diarization from the pipeline. Transcription, frame
extraction, word-level timestamps, and the grounded-citation grammar — every
part that demonstrably works — stay exactly as they are. What a spec actually
needs from a recording is what was asked for and what was settled, and the
transcript carries both: intents live in the words, and "what was agreed"
resolves by recency over timestamps that have been verified exact against
independently transcribed audio.

Success criteria: `ingest` produces a bundle with no diarization stage and no
speaker fields; the brief grammar carries no speaker surface; every test and
eval fixture covering the removed behaviour is gone or updated; and an ingest
run needs no diarization model download and no credentialed model.

### Non-goals

- No change to ASR, frame selection, deixis anchoring, or the citation grammar
  — the working half of the pipeline is untouched.
- No replacement multi-party mechanism by another route (voice fingerprinting,
  manual speaker maps, or a video-based cue).
- No retrofit of already-installed briefs; the grammar's tolerance of
  unrecognized level-2 sections keeps them lint-clean unchanged.
- No revival of the gated pyannote backend or the non-production-licensed
  Reverb models under any licence arrangement.

## Decisions

- **Remove rather than repair.** Every remaining lever was tested or excluded:
  segmentation swap (tried, worse), embedding swap (the failure is real but the
  output is unread either way), and the gated pyannote pipeline (shares sherpa's
  segmentation, so it cannot fix boundaries). Repairing a component nothing
  reads is not worth the models, CLI surface, and test weight it carries.
- **Conflict resolution moves from decider-by-speaker to recency-by-timestamp.**
  The existing arbitration rule already turned on the decider's *latest*
  statement; recency is the load-bearing half and comes from word timestamps,
  which were verified exact against an independently transcribed clip.
  Unresolved contradictions go to `## Open questions` as they do today.
- **The brief loses its speaker surface entirely, not optionally.** No `##
  Speakers` section and no speaker field in `## Sources`; a source entry is its
  `[HH:MM:SS]` anchor and what was said. An optional section nothing reads would
  be carried cost with no consumer.
- **The removal is backward-compatible for installed briefs.** The grammar
  permits unrecognized level-2 sections, and dropping the speaker requirement
  from source entries makes a trailing name ordinary prose — so briefs already
  in the tree stay lint-clean without edits.
- **`video-brief-project` is absorbed, not shipped separately.** It edits
  `video-brief-format` and `video-brief-validation`, the same two requirements
  the grammar member rewrites; folding it in avoids a stale-base collision and
  makes one coherent grammar revision instead of two conflicting ones.
- **Tests travel with the code they cover.** The constitution requires every
  engine change to carry tests, so each member deletes its own test modules
  rather than deferring cleanup to a third member.
- **Orphaned config keys are deleted here and tolerated elsewhere.** The repo's
  own `.shipd-config.json` carries a live `build.video_speakers` roster written by
  the `roster` verb; the engine member deletes that value so the tree holds no
  key nothing reads. A stale `video_speakers`, `video_speakers_count`, or
  `video_diarizer` left in someone else's config needs no migration shim and no
  deprecation warning: config resolution is a layered `.get()` lookup
  (`video_ingest.py:96-111`) and nothing validates `build.*` key names, so an
  orphaned key becomes inert rather than an error. Rejected: a warn-on-stale-key
  pass — it would add a config-schema notion this repo has never had, to
  announce a key that already does nothing.
- **The `--speakers` removal is a real break and is named as such.** Unlike a
  stale config key, a wrapper script passing `--speakers` fails outright:
  argparse exits non-zero with `unrecognized arguments`. The removed
  requirements' `Migration:` notes state this plainly rather than implying the
  option is quietly ignored.

## Design

The pipeline has a clean seam between the **engine** that produces a bundle and
the **grammar plus skills** that turn a bundle into a brief. Diarization crosses
both, and the two sides fail independently, so the decomposition follows that
seam.

Engine side, `video_ingest.py` (1409 lines) and its backends: the diarizer
adapter pair, the `--diarizer` and `--speakers` options, word-to-turn
attribution, the spurious-turn filter, the diarization report, and the three
speaker-support verbs (`samples`, `merge-speakers`, `roster`) all disappear,
along with the sherpa model cache entry in `doctor`. The bundle contract and
transcript schema lose their speaker fields. What remains is demux → ASR →
frames → bundle.

Grammar and skill side: `video-brief-format` and `video-brief-validation` drop
the speaker rules, `/s:video-ingest` loses its naming round and decider
arbitration, and the `plan-video-brief` eval fixture is updated to a brief with
no speaker surface. This member also carries the absorbed `Project:` header
field and `/s:plan`'s target-mismatch guard, since it is already rewriting both
brief-grammar requirements.

Ordering is not strictly enforced by the artifacts, but the engine member is the
natural first: once bundles stop carrying speakers, the grammar member's removal
of the speaker surface has nothing left pointing at it.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| video-drop-diarization-engine | Delete both diarizer backends; drop `--diarizer`/`--speakers`, word-to-turn attribution, the spurious-turn filter, the diarization report, and the `samples`/`merge-speakers`/`roster` verbs; drop the sherpa cache from `doctor`; strip speaker fields from the bundle contract and transcript schema; delete the orphaned `build.video_speakers` value from the repo's `.shipd-config.json`; delete the five covering test modules and prune three more | high | medium | low | medium |
| video-brief-grammar-revision | Remove `## Speakers` and the source speaker field from `video-brief-format` and `video-brief-validation`; strip the naming round and decider arbitration from `/s:video-ingest`; add the absorbed `Project:` header field and `/s:plan`'s target-mismatch guard with its `--cross-project` override; update the `plan-video-brief` eval fixture | medium | high | medium | medium |
