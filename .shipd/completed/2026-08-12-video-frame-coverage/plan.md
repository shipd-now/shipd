# video-frame-coverage
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Spread the frame budget across the whole recording instead of spending it all
on whatever happens first.

### Motivation

`video-frame-budget` fills the cap with deixis candidates in time order, so a
581-second walkthrough produced 24 frames spanning only its first 48 seconds —
no visual evidence at all for the remaining 92%, and every scene peak dropped.

### Details

- Replace time-ordered greedy filling with distribution: divide the recording
  into as many equal buckets as the frame cap and take at most one candidate
  from each occupied bucket.
- Within a bucket, keep preferring a deixis candidate over a scene candidate.
- Backfill any slots left by empty buckets with the best remaining candidates.
- Keep dedup, the `build.video_max_frames` key, and per-drop stderr reporting
  exactly as they are.

Affected capabilities: `video-pipeline` (modified). Impact:
`plugins/s/skills/video-ingest/scripts/video_ingest.py`,
`plugins/s/skills/video-ingest/tests/test_video_frames.py`, and the plugin
version in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to how candidates are generated — `video-deixis-anchors` and
  `video-scene-peaks` are untouched.
- No change to the dedup gap, the cap's default, or the drop-reporting rule.
- No change to extraction, scaling, or `frames.json`.
- No reservation of a fixed share for scene candidates in this change — see the
  Implementation note, which records that distribution alone was measured NOT to
  rescue scene frames, leaving that to a follow-up.
- No adjustment to `SPURIOUS_TURN_MAX_SECONDS`, which is a diarization concern
  and is better answered by `--speakers`.

## Implementation

**The current rule is the defect, so this is a delta and not a bug fix.**
`video-frame-budget` states the cap is applied "by keeping deixis candidates
first in time order"; the implementation does precisely that. Measured on a
581-second UX walkthrough (`~/.shipd/video/skymiles/`): 24 of 24 frames came from
deixis anchors, **zero** from scene peaks, and every frame fell between 2.6 s
and 48.1 s. Scene peaks marking real UI transitions at 387 s, 514 s and 562 s
were dropped by the cap. A brief built on that bundle could cite nothing past
the introduction.

**Distribution, not priority, is the fix.** The recording is divided into
`max_frames` equal-width buckets and at most one candidate is taken from each
occupied bucket, so coverage is proportional to duration rather than to how
early a speaker gestures. Within a bucket the existing preference holds — a
deixis candidate beats a scene candidate, and among same-reason candidates the
higher-scoring scene peak or the earlier deixis anchor wins — so the original
intent that speech-anchored frames are primary is preserved exactly where it
still makes sense: locally.

**Empty buckets backfill rather than waste the budget.** A recording with long
silent stretches leaves buckets with no candidate; those slots are filled from
the remaining unselected candidates by the same within-bucket preference, so a
short or sparse recording still yields as many frames as it did before. On the
48-second reference recording, where 23 candidates never reached the 24-frame
cap, this change is a no-op — every candidate is still kept.

**Deferred, not rejected: reserving a fixed share for scene candidates.** The
first draft of this plan rejected a scene quota on the grounds that
"distribution fixes both symptoms with one rule". **Measurement disproved
that.** After this change the 581-second recording yields frames spanning
2.6 s–557.1 s — the clustering is fixed — but still **zero** scene frames,
because every one of the 24 buckets held a deixis candidate and the
within-bucket rule prefers deixis. Distance from each of the 47 dropped scene
peaks to the nearest kept frame: median 7.9 s, max 18.5 s, only 5 within 2 s.
A UI transition can therefore still go uncaptured. Reserving a share of the
cap for scene candidates, or preferring the scene candidate when a bucket's
deixis winner sits far from it, remains a real improvement and is left to a
follow-up change rather than widened into this one.

**Rejected: raising the cap.** The cap exists to bound what a downstream reader
must look at, and the failure is not that 24 frames is too few — it is that the
24 chosen frames describe 8% of the recording.

**Drop reporting stays load-bearing.** Every candidate the cap discards is still
named on stderr with its timestamp and reason. That log is what made this defect
visible in the first place: seven `dropped frame candidate … (scene)` lines were
the first signal that scene peaks were being starved.

Risk: bucketing could scatter frames away from the moments that matter, keeping
a weak candidate in an empty stretch over a strong one in a dense stretch.
Bounded by backfill — surplus slots return to the best remaining candidates
regardless of bucket — and by the verification below, which requires the
reference 48-second recording's frame set to be unchanged, so the fix cannot
silently degrade the case that already worked.
