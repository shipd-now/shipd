# video-drop-diarization-engine
Status: verified
Epic: video-drop-diarization

## Idea

Remove diarization from the ingest engine: both diarizer backends, the speaker
options, word-to-turn attribution, the speaker-support verbs, and every speaker
field in the bundle.

### Motivation

Diarization does not work and nothing reads its output: measured against a
content-derived probe set on a real two-person recording, all three available
diarizers failed to separate the speakers, and `## Speakers` is linted but never
consumed. The engine nonetheless carries two backends, three CLI verbs, a model
cache, an attribution function, a turn filter, and a diarization report to
produce it.

### Details

- Delete `backends/diarize_sherpa.py` and `backends/diarize_pyannote.py`.
- Drop `--diarizer`/`--speakers`, the diarizer rows of the backend table, and
  the `samples`, `merge-speakers`, and `roster` verbs.
- Drop word-to-turn attribution, the spurious-turn filter, and the diarization
  report; flatten `transcript.json` to a schema `version` plus a `words` array.
- Drop the sherpa and pyannote cache entries from `doctor`, so no ingest
  prerequisite is a diarization model or a credentialed one.
- Confirm no tracked configuration carries an orphaned `build.video_*` key, and
  correct the transcript-shape sentence in the ingest skill.

Affected capabilities: `video-pipeline` (modified). Impact:
`plugins/s/skills/video-ingest/scripts/video_ingest.py`, both diarizer backends
(deleted), five test modules (deleted) plus three pruned,
`plugins/s/skills/video-ingest/SKILL.md`, `.shipd-config.json`, and the plugin
version in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to ASR, audio extraction, frame selection, or the vocabulary
  biasing that feeds them — the working half of the pipeline is untouched.
- No change to the brief grammar, its linter, or the skill's speaker-naming and
  arbitration sections: those are `video-brief-grammar-revision`'s scope. The
  one skill edit here is the sentence describing the transcript's shape.
- No deprecation shim or warning for stale `build.video_*` keys in other
  configs.

## Implementation

- **`transcript.json` flattens to `version` + `words`.** The `segments` array
  exists only to group same-speaker runs — `assemble_segments`
  (`video_ingest.py:504`) splits at speaker changes and nothing else — and the
  skill already instructs readers to "anchor on words, never on segments"
  (`SKILL.md:83`). With speakers gone the container carries no information.
  Rejected: keeping segments split on a silence gap, which would invent a
  threshold constant nothing needs; and keeping a single all-spanning segment,
  which preserves the shape while emptying it of meaning.
- **This member corrects the skill's transcript-shape sentence**
  (`SKILL.md:64`), even though the grammar member owns the rest of that file.
  The member that changes a schema fixes the sentence describing it, so the
  skill never documents a shape that does not exist between the two merges.
- **No tracked configuration carries a diarization key, so none is deleted.**
  The epic's decision anticipated removing a live `build.video_speakers` roster,
  but the committed `.shipd-config.json` holds only `valid_themes` — the roster
  exists solely as an uncommitted local edit in one checkout, outside this
  change's scope. The task therefore verifies the absence rather than performing
  a deletion that would find nothing.
- **Stale config keys are left inert, deliberately.** No migration shim or
  warning is added for `build.video_speakers`, `video_speakers_count`, or
  `video_diarizer` surviving in someone's local or workspace config: reads are
  layered `.get()` lookups (`video_ingest.py:96-111`) and nothing validates
  `build.*` key names, so an orphaned key simply stops being read. Rejected: a
  warn-on-stale-key pass, which would introduce a config-schema notion this repo
  has never had.
- **`--speakers` disappearing is a genuine break, not a silent ignore.**
  argparse exits non-zero with `unrecognized arguments`, so a wrapper script
  passing it fails outright. The removed requirements' `Migration:` notes say so
  rather than implying tolerance.
- **The bundle keeps its `frames/` directory and loses `samples/`.** The
  `samples` verb is the only writer of `samples/`, so the layout requirement
  drops it with the verb.

Risk: the delta carries 13 requirement operations and will exceed the linter's
per-document size guidance, which the epic accepted when choosing two members
over three. The compensating control is that every operation is a removal or a
narrowing of an existing requirement — no new behaviour is introduced that a
reader must reason about.
