## MODIFIED Requirements

### Requirement: Candidate merge, dedup and capping
id: video-frame-budget
base: e019d965a3a5

`video_ingest.py` SHALL merge deixis and scene candidates, dropping a candidate
within `FRAME_DEDUP_MIN_GAP_SECONDS` of an already-kept one and keeping the
earlier, then apply a cap resolved from the configuration's
`build.video_max_frames` key (default 24) by **distributing the budget across
the recording**: the recording SHALL be divided into as many equal-width
buckets as the cap allows and at most one candidate SHALL be taken from each
occupied bucket, so the kept frames span the recording rather than clustering
wherever candidates are densest. Within a bucket a deixis candidate SHALL be
preferred over a scene candidate; among candidates of the same reason the
higher-scoring scene peak or the earlier deixis anchor SHALL win. Where buckets
are empty, the unused slots SHALL be backfilled from the remaining unselected
candidates under that same preference, so a sparse recording still yields as
many frames as the candidates allow. Where the merged candidates do not exceed
the cap, every candidate SHALL be kept. Every candidate dropped by the cap
SHALL be reported on stderr with its timestamp and its selection reason.

#### Scenario: Near-duplicate candidates collapse
- **WHEN** a deixis candidate and a scene candidate fall within the dedup gap
- **THEN** only the earlier is kept

#### Scenario: Kept frames span the recording
- **WHEN** the merged candidates exceed the cap and cluster heavily in the
  recording's opening minutes
- **THEN** the kept frames are spread across the recording's full duration
  rather than confined to the region where candidates are densest

#### Scenario: A dense early stretch cannot starve later candidates
- **WHEN** enough deixis candidates occur early to fill the cap on their own,
  and scene candidates occur later in the recording
- **THEN** later candidates are still selected, because each bucket contributes
  at most one frame

#### Scenario: Deixis still wins inside a bucket
- **WHEN** a bucket holds both a deixis candidate and a scene candidate
- **THEN** the deixis candidate is the one kept for that bucket

#### Scenario: Empty buckets backfill rather than waste the budget
- **WHEN** some buckets hold no candidate and unselected candidates remain
- **THEN** the unused slots are filled from those remaining candidates, so the
  kept count is limited by the candidates available, not by bucket occupancy

#### Scenario: An under-cap recording keeps every candidate
- **WHEN** the merged candidates number fewer than the cap
- **THEN** every candidate is kept and none is dropped

#### Scenario: Dropped candidates are always reported
- **WHEN** the cap drops one or more candidates
- **THEN** each dropped candidate's timestamp and reason are written to stderr,
  so a capped set is never silently presented as complete
