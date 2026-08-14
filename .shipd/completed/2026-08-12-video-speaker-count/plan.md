# video-speaker-count
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Let a caller tell the diarizer how many people are in the recording, and widen
the word-attribution fallback to match observed boundary error.

### Motivation

The diarization backend hardcodes automatic clustering
(`diarize_sherpa.py:91`, `num_clusters=-1`), so a recording whose speaker count
is known cannot constrain it — and the reference recording, which has one
speaker, is split into three labels by the diarizer, which the spurious-turn
filter then reduces to two.

### Details

- Add `--speakers N` to `ingest`, resolved from `build.video_speakers_count`
  when the flag is absent, defaulting to automatic.
- Pass it to the diarization backend as `--speakers N`, which maps it to
  `FastClusteringConfig(num_clusters=N)`.
- Widen `ATTRIBUTION_FALLBACK_WINDOW` from 0.25 s to 0.35 s.

Affected capabilities: `video-pipeline` (modified). Impact:
`plugins/s/skills/video-ingest/scripts/video_ingest.py`,
`plugins/s/skills/video-ingest/scripts/backends/diarize_sherpa.py`, the suite
under `plugins/s/skills/video-ingest/tests/`, and the plugin version in
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to the default: absent a flag and a config key, clustering stays
  automatic, so every existing caller behaves exactly as today.
- No removal of the spurious-turn filter or the naming round — both remain as
  backstops for the unconstrained case.
- No `min`/`max` range, only an exact count; the backend exposes
  `num_clusters`, not a bounded search.
- No change to ASR, frames, the bundle contract, or the brief.
- No re-tuning of `CLUSTER_THRESHOLD`, which governs automatic mode only.

## Implementation

**The constraint is the principled fix; the existing cleanup is the backstop.**
Published guidance on this pipeline shape is explicit that constraining the
speaker count "dramatically improves clustering accuracy by preventing the
algorithm from over-fragmenting the speaker identities". This repository has the
symptom in hand: one physical speaker, three diarization labels, cleaned up
afterwards by `filter_spurious_turns` and, since the previous member, by an
interactive merge. Both stay — they are still needed when the count is genuinely
unknown — but a caller who knows the answer should not have to rely on them.

**Default-automatic is non-negotiable.** Absent `--speakers` and absent
`build.video_speakers_count`, no `--speakers` argument is passed and the backend
keeps `num_clusters=-1`. Every existing bundle, test, and caller is therefore
unaffected. Rejected: defaulting to 1, which would silently collapse genuine
multi-speaker recordings — the worst possible failure for an epic whose point is
attributing intents to people.

**The option rides the established contract seam.** `backend_argv` already
appends `--vocab` conditionally, and `video-backend-adapters` already requires
every backend to accept options it does not use. `--speakers` follows that
pattern exactly, so the ASR backends tolerate and ignore it and no contract
rewrite is needed.

**A count below 1 is rejected at the CLI, not passed through.** `num_clusters=0`
or a negative value would be interpreted by the backend as "automatic" and
silently do the opposite of what the caller asked. The flag therefore validates
`N >= 1` and exits non-zero otherwise.

**The fallback window moves on evidence, not taste.** `0.25` was chosen by
intuition when word attribution was written. Boundary imprecision — not missed
turns — is the dominant contributor to diarization error, with average missed
segment durations reported around 350 ms, so a word sitting in a 300 ms boundary
gap is currently attributed `null` when the adjacent turn is almost certainly
right. Widening to `0.35` brings the window in line with the error it exists to
absorb. The change is deliberately small: the maximum-overlap rule is untouched,
and only words overlapping *no* turn are affected.

Risk: a caller who states the wrong count forces the clusterer to merge distinct
voices or split one, with no signal that it happened. Guarded by keeping the
default automatic, validating `N >= 1`, and recording the requested count in
`manifest.json` so a surprising transcript can be traced back to the constraint
that produced it.
