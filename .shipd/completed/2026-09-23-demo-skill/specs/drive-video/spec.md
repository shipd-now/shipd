## ADDED Requirements

### Requirement: Terminal recording from a tape
id: drive-tape

The CLI SHALL provide a `tape <tape-file>` verb recording a terminal session
with `vhs` and emitting the same recording-plus-timeline pair the browser
`record` verb emits, so a terminal demo reaches `post` (drive-postprocess)
unchanged. The verb SHALL resolve `vhs` on PATH; if it is absent, then the
verb SHALL report the missing tool with the `brew install vhs` remedy, record
nothing, and exit non-zero. The verb SHALL NOT start a browser, resolve a
drive target, or perform any login — a terminal recording has no target and
no session.

The verb SHALL run the tape unmodified except for resolving its output path,
so the tape the author wrote is the tape that runs, and SHALL fail loudly on a
non-zero `vhs` exit rather than post-processing a partial recording. On
success it SHALL print one JSON object carrying the recording path and the
timeline path, matching `record`'s output shape.

#### Scenario: A tape produces a recording and a timeline
- **WHEN** `tape demo.tape` runs with `vhs` present
- **THEN** a video file and a timeline JSON are written beside each other and
  their paths are printed as one JSON object

#### Scenario: A missing recorder refuses before recording
- **WHEN** `tape demo.tape` runs with `vhs` absent from PATH
- **THEN** the verb names `brew install vhs` as the remedy, writes no video,
  and exits non-zero

#### Scenario: A failing tape is never post-processed
- **WHEN** `vhs` exits non-zero part-way through a tape
- **THEN** the verb reports the failure and exits non-zero rather than
  emitting a timeline for a partial recording

#### Scenario: A terminal recording carries no browser state
- **WHEN** `tape demo.tape` runs
- **THEN** no drive target is resolved, no login is attempted, and no session
  daemon is started

### Requirement: Tape annotations drive the timeline
id: drive-tape-timeline

The timeline a tape recording emits SHALL carry `holds` and `leadingCut`
only, leaving every dead-air stretch to the post-processor's spinner backstop
(drive-postprocess) rather than deriving spans from the tape's own `Sleep`
directives. A tape's real command durations are unknown until it runs, so
statically derived spans would drift from the recording they describe, while
the backstop measures the frames that were actually captured.

The verb SHALL read its annotations from tape comments: a `#hold` comment
SHALL open a protected window at that point in the tape and a `#endhold`
comment SHALL close it, and a `#ready` comment SHALL mark the boot end that
becomes `leadingCut`. An unclosed `#hold` SHALL extend to the end of the
recording. A tape carrying no annotations SHALL still produce a valid
timeline, with empty `holds` and no `leadingCut`, so the backstop alone
carries it.

#### Scenario: A hold annotation protects its reveal
- **GIVEN** a tape carrying `#hold` before a command and `#endhold` after it
- **WHEN** the recording is post-processed
- **THEN** that stretch plays at normal speed regardless of how static it is

#### Scenario: An unannotated tape still post-processes
- **WHEN** a tape carrying no annotations is recorded and post-processed
- **THEN** the timeline carries empty `holds`, the backstop supplies every
  fast-forward span, and the branded output is produced

#### Scenario: The ready annotation becomes the leading cut
- **GIVEN** a tape carrying `#ready` after its shell prompt settles
- **WHEN** the timeline is emitted
- **THEN** its `leadingCut` is that annotation's offset

#### Scenario: No spans are derived from sleeps
- **GIVEN** a tape carrying several `Sleep` directives
- **WHEN** the timeline is emitted
- **THEN** its `spans` list is empty
