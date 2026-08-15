## ADDED Requirements

### Requirement: Pointer localization by gated frame differencing
id: video-cursor-localization

`video_ingest.py` SHALL locate the on-screen pointer for a selected frame at
time `t` by extracting `CURSOR_DIFF_FRAMES` grayscale frames spaced
`CURSOR_DIFF_STEP_SECONDS` apart and ending at `t` in a single `ffmpeg` pass,
scaled to a fixed working width `CURSOR_WORK_WIDTH`, written to a file and read
as bytes — raw pixel data SHALL NOT be returned through the injectable runner,
whose stdout is decoded as text. Tile energies SHALL be compared relative to the
strongest change in the same difference, never against an absolute constant. A
changed region SHALL be reported as the pointer only when all four hold: it
spans at most `CURSOR_MAX_SPAN_TILES` tiles in each dimension; it is absent from
the persistent-churn mask of tiles changing in both earlier differences; it is
the sole survivor of those filters, or — where several survive — the sole one
absent from the preceding difference; and its energy exceeds every other changed
region's by `CURSOR_DOMINANCE`. If no region satisfies all four, then no pointer
SHALL be recorded for that frame, and the frame SHALL still be extracted and
indexed. Localization SHALL report the pointer's position in the **source**
recording's pixel coordinates.

#### Scenario: A moving pointer is located
- **WHEN** the pointer moves shortly before a selected frame's timestamp and
  nothing else on screen changes
- **THEN** its position is reported, expressed in source pixel coordinates

#### Scenario: A large redraw is not a pointer
- **WHEN** the difference's strongest region spans more than
  `CURSOR_MAX_SPAN_TILES` tiles, as a modal opening does
- **THEN** no pointer is recorded and the frame is still extracted and indexed

#### Scenario: Persistent churn is excluded
- **WHEN** a small region changes in every difference of the window, as a
  ticking counter does, and the pointer changes only in the last
- **THEN** the churning region is masked out and the pointer is the reported
  position

#### Scenario: Competing candidates record nothing
- **WHEN** more than one cursor-sized region survives the filters and more than
  one of them is absent from the preceding difference
- **THEN** no pointer is recorded rather than one being chosen

#### Scenario: A wholly static frame records nothing
- **WHEN** no pixel changes across the window
- **THEN** no pointer is recorded and the ingest still succeeds

#### Scenario: Thresholds survive a change of scale
- **WHEN** the same pointer motion is differenced at two different source
  resolutions
- **THEN** it is located in both, because every threshold is relative to the
  strongest change in the same difference

#### Scenario: Raw pixels never cross the text runner
- **WHEN** the window's grayscale frames are obtained
- **THEN** `ffmpeg` writes them to a file and they are read as bytes, the
  runner carrying only the invocation's exit status

### Requirement: Verified carry-forward of a resting pointer
id: video-cursor-carry-forward

Where a selected frame yields no confident localization, `video_ingest.py` SHALL
carry forward the most recently located pointer position from an earlier
selected frame **only if** the two frames' pixels over that position's region
are identical, compared byte for byte at the working scale. If that region
changed between the two frames, then no pointer SHALL be recorded. A carried
position SHALL be marked as carried and SHALL record the timestamp it was
carried from. If no pointer has been located yet in the recording, then nothing
SHALL be carried.

#### Scenario: A resting pointer is carried forward
- **GIVEN** a pointer was located at an earlier selected frame
- **WHEN** a later frame is inconclusive and the pointer's region is unchanged
  between the two frames
- **THEN** the earlier position is recorded for the later frame, marked as
  carried and naming the timestamp it came from

#### Scenario: A changed region blocks the carry
- **WHEN** a later frame is inconclusive and the pointer's region has changed
  since it was located
- **THEN** no pointer is recorded for that frame

#### Scenario: Nothing is carried before the first localization
- **WHEN** the recording's earliest selected frames are all inconclusive
- **THEN** none of them carries a pointer

### Requirement: Pointer zoom crops and index entries
id: video-cursor-crops

Where a pointer position is known for a selected frame, `video_ingest.py` SHALL
extract a zoom crop from the **source** recording at its native resolution — a
window `CURSOR_CROP_WIDTH_FRACTION` of the source width at a 4:3 aspect,
centred on the pointer and clamped to the frame's bounds, scaled to a long edge
of `CURSOR_CROP_LONG_EDGE` — into the bundle's `frames/` directory beside the
full frame, and SHALL record a `cursor` object on that frame's `frames.json`
entry holding the pointer's `x`, `y`, `w` and `h` in source pixel coordinates,
the crop's `file`, and its `origin` of `located` or `carried`. A frame with no
known pointer SHALL carry no `cursor` key at all. Where the resolved
configuration's `build.video_cursor` key is false, no localization, crop, or
`cursor` entry SHALL be produced and ingest behaviour SHALL be otherwise
unchanged.

#### Scenario: A crop lands beside its full frame
- **WHEN** a pointer is located for a selected frame
- **THEN** a crop is written into the bundle's `frames/` directory and the
  frame's index entry names it

#### Scenario: Coordinates are in source pixel space
- **WHEN** a pointer is recorded for a recording whose frames were downscaled
  on extraction
- **THEN** the recorded `x`, `y`, `w` and `h` address the source recording's
  pixels, not the downscaled frame's

#### Scenario: A pointer at the edge yields a clamped crop
- **WHEN** the pointer sits close enough to an edge that the centred window
  would fall outside the frame
- **THEN** the window is clamped into the frame's bounds and the crop is still
  written

#### Scenario: Absence is never a position
- **WHEN** a frame has no known pointer
- **THEN** its index entry carries no `cursor` key, rather than a null or
  zeroed position

#### Scenario: Configuration disables the stage
- **WHEN** `build.video_cursor` is false
- **THEN** no crop is written and no index entry carries a `cursor` key, and
  the frames and transcript are produced exactly as before
