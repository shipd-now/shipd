# drive-video

### Requirement: Recorded action modules and the semantic timeline
id: drive-recording

The `record` verb SHALL run a Playwright worker that records the browser to
video while executing an action module exporting `run(page, h, base_url)`,
loading the target's cached storage state so the recording is authenticated.
The helper object `h` SHALL provide an injected cursor, glide-and-click,
glide-and-type, an anchored annotation card, an element highlight, a
protected `hold`, a recorded wait, and a content-ready mark. The worker SHALL
write a timeline file beside the recording carrying three fields: `spans`,
the wait stretches eligible for fast-forward; `holds`, the protected windows
that must play at normal speed; and `leadingCut`, the end of the application
boot. An annotation SHALL protect its own visible window, and the worker
SHALL hold the final frame for a protected tail beat before closing.

#### Scenario: A recorded wait becomes a span
- **WHEN** an action module awaits a recorded wait helper for eight seconds
- **THEN** the timeline file's `spans` carries a stretch covering that wait

#### Scenario: An annotation is protected
- **WHEN** an action module shows an annotation card for three seconds
- **THEN** the timeline file's `holds` covers the window that card was visible

#### Scenario: Content-ready sets the leading cut
- **WHEN** an action module marks content ready after the first page settles
- **THEN** the timeline file's `leadingCut` carries that moment

### Requirement: Fast-forward post-processing
id: drive-postprocess

The `post` verb SHALL assemble a finished video from a recording and its
timeline: it SHALL cut the leading boot at `leadingCut` when present, at the
detected content start otherwise, and at a fixed fallback when neither is
available. It SHALL play every dead-air block of at least five seconds at ten
times speed, SHALL keep every other stretch at normal speed, and SHALL never
cut interior content. A block covered by a `holds` window SHALL play at normal
speed regardless of how static it is, and the final result SHALL be held at
normal speed. The verb SHALL union a spinner backstop over the timeline's
spans, detecting a waiting stretch by the fraction of the frame's cells that
change across a time window, so an animated spinner confined to a small region
is detected as dead air. Where the verb is asked for an inline-embeddable
output, it SHALL additionally write an animated GIF.

#### Scenario: A protected reveal is never sped up
- **WHEN** a static modal sits on screen for eight seconds inside a `holds`
  window
- **THEN** that stretch plays at normal speed in the output

#### Scenario: A short pause stays at normal speed
- **WHEN** a static stretch lasts three seconds
- **THEN** it is not fast-forwarded

#### Scenario: An animated spinner counts as dead air
- **WHEN** a ten-second stretch changes only a small localized region of each
  frame and the timeline marked no span there
- **THEN** the backstop reports it and the stretch is fast-forwarded

#### Scenario: Interior content is never cut
- **WHEN** the output's content is compared against the recording's body
- **THEN** every interior stretch is present, fast-forwarded or not

### Requirement: shipd-branded video frames
id: drive-brand-frames

The rendered title card SHALL carry the U+2615 coffee mark as its hero glyph
above the title, on a dark ground, with the shipd wordmark gradient running
from `#8888a0` to `#c6ff4e`. The title SHALL default to the current shipd
change name when the working tree is on a `change/<slug>` branch, SHALL fall
back to an explicitly supplied title otherwise, and SHALL never be derived
from an issue-tracker identifier. The fast-forward badge SHALL be a small flat
mark: at a 1280 by 720 frame it SHALL be at most 44 pixels tall and at most
180 pixels wide, SHALL carry the speed factor and a single chevron, and SHALL
carry no border and no glow. The badge SHALL appear only over fast-forwarded
stretches, and its corner SHALL be selectable so it never covers the region
under demonstration.

#### Scenario: The card carries the shipd mark
- **WHEN** the title card is rendered
- **THEN** its hero glyph is U+2615 and its gradient runs from `#8888a0` to
  `#c6ff4e`

#### Scenario: The title comes from the change branch
- **WHEN** a recording is post-processed on branch `change/drive-skill` with
  no explicit title supplied
- **THEN** the card's title reads `drive-skill`

#### Scenario: The badge stays small
- **WHEN** the badge is rendered for a 1280 by 720 frame
- **THEN** its height is at most 44 pixels and its width at most 180 pixels

#### Scenario: The badge only marks fast-forwarded stretches
- **WHEN** a normal-speed stretch of the output is inspected
- **THEN** no badge is composited over it

### Requirement: The action-module reference matches the helper
id: drive-helper-docs

The action-module reference `references/recording.md` SHALL document the
helper object `h` with the method names, parameter names, and parameter order
that `record_worker.py`'s `Helper` actually defines, so an action module
written from the reference runs unchanged. The reference SHALL NOT present as
part of the helper's API any `h.<name>` that `Helper` does not define. The
repository SHALL carry a test that resolves every helper name the reference
documents against `Helper` through runtime signature inspection, and that test
SHALL fail when a documented name is absent from the implementation, when a
documented parameter name is absent from that method's signature, or when the
documented parameters appear in an order the real signature does not have.

#### Scenario: Every documented helper method exists
- **WHEN** the doc-drift test inspects `Helper` for each method the reference
  documents
- **THEN** every documented method name resolves on `Helper`

#### Scenario: Documented parameter names match the implementation
- **WHEN** the test compares each documented method's parameter names against
  the signature `Helper` defines
- **THEN** every documented parameter name appears in that signature

#### Scenario: Documented parameter order matches the implementation
- **WHEN** the reference documents a method's parameters in an order the real
  signature does not declare
- **THEN** the doc-drift test fails and names that method

#### Scenario: A documented name that is not a helper member fails the test
- **WHEN** the reference presents an `h.<name>` that `Helper` defines neither
  as a method nor as an attribute
- **THEN** the doc-drift test fails and names it

#### Scenario: A renamed helper method fails the test
- **WHEN** a helper method the reference documents is renamed in
  `record_worker.py` without the reference being updated
- **THEN** the doc-drift test fails and names the missing method

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
