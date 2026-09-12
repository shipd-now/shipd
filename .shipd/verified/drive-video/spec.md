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
