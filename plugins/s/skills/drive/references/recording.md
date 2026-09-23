# Recording a demo — the action-module and tape contracts

Loaded by `SKILL.md` (both `/s:drive`'s and `/s:demo`'s) when the request
wants a recorded demo, not just a verified drive. This reference holds both
media's authoring rules in one place: the contract between an **action
module** — a short Python file you write for one specific browser demo — and
`record_worker.py`, the Playwright worker that runs it while recording video
(drive-recording); and the contract between a **tape** — a `vhs` script — and
`drive.py tape`, which runs it unmodified and derives its timeline from the
tape's own comments (drive-tape, drive-tape-timeline).

## The action-module contract

An action module is a plain `.py` file with one required top-level function:

```python
def run(page, h, base_url):
    ...
```

- `page` — the live Playwright `Page`, already authenticated with the
  target's cached storage state. Drive it directly for anything the helper
  object does not cover (`page.goto`, `page.locator`, assertions on page
  state, and so on).
- `h` — the helper object below. Prefer it over raw `page` calls for
  anything the viewer will see: it is what makes the recording legible and
  what feeds the semantic timeline `postprocess.py` reads.
- `base_url` — the target's resolved `url`, so the module never hardcodes an
  environment.

`record_worker.py` imports the module by path and calls `run(page, h,
base_url)` once. The function returns when the demo is complete; the worker
then holds the final frame for a protected tail beat and closes. Raise on
failure — a module that cannot complete its scripted actions should fail
loudly rather than let the recording trail off silently.

An action module performs only what the demo needs to show. It is not a test:
it does not assert, and it does not need to guess selectors — probe the live
DOM with `drive.py probe` first (`SKILL.md`'s probe-before-selecting rule)
and write the module against what `probe` actually returned.

## The helper API (`h`)

Every `h` method that shows something on screen also feeds the timeline file
`record_worker.py` writes beside the recording (`spans`, `holds`,
`leadingCut` — drive-recording). Use the helper for viewer-facing action so
that timeline stays accurate; a raw `page.click()` is invisible to the
timeline and to the viewer, since it leaves no cursor motion for the
recording to show.

The helper also injects a **cursor overlay** — a synthetic pointer element
drawn into the page so the recording always shows where the demo is acting.
It is created once, when the helper is built, and every glide method below
moves it. The overlay is internal: it is not part of the helper's API, and an
action module never reads or positions it directly.

- **`h.glide_click(selector, steps=24)`** — glides the injected cursor
  smoothly to `selector` over `steps` intermediate moves, then clicks it. Use
  this for every click the viewer should be able to follow.
- **`h.glide_type(selector, text, steps=24, delay=40)`** — glides the cursor
  to `selector` over `steps` moves, clicks it, then types `text` at `delay`
  milliseconds per keystroke so the viewer can read it forming.
- **`h.annotate(text, anchor_selector=None, duration=2.5)`** — shows an
  annotation card carrying `text` for `duration` seconds — the text comes
  first, and the card is anchored near `anchor_selector` when one is given and
  floats unanchored otherwise. The card's visible window is added to the
  timeline's `holds` automatically — an annotation protects itself; the
  action module does not need to also wrap it in `h.hold(...)`.
- **`h.highlight(selector, duration=1.5)`** — draws an outline around
  `selector` for `duration` seconds. A highlight does **not** protect itself;
  wrap it in `h.hold(...)` when the highlighted moment is itself the reveal the
  viewer must read (e.g. drawing attention to a value that just changed),
  not merely decorative emphasis on something already covered by a
  surrounding hold or annotation.
- **`h.hold(seconds)`** — marks the next `seconds` as a protected window:
  `postprocess.py` plays it at normal speed regardless of how static the frame
  is. Use it around any reveal that is not already an annotation — a modal
  that opened and needs to be read, a toast, a value the demo is proving
  changed.
- **`h.wait(seconds)`** — a recorded wait: pauses for `seconds` and records
  the stretch as a `spans` entry, eligible for fast-forward by
  `postprocess.py` when it turns out to be dead air (loading, a transition,
  network latency). Use this instead of a bare `page.wait_for_timeout` for
  any pause with nothing the viewer needs to read — an unrecorded pause is
  invisible to the fast-forward pass and always plays at normal speed.
- **`h.content_ready()`** — marks the moment the first page has visually
  settled (the application has finished booting). The worker records the first
  call's instant as the timeline's `leadingCut`, so `postprocess.py` cuts
  everything before it; later calls are ignored. Call this once, as early as
  the module can, right after the first navigation's content is actually on
  screen.

## The reveal rule

**Every reveal the viewer must read is wrapped in a protected hold or an
annotation** — never left to survive on the strength of not looking static
enough to fast-forward. `postprocess.py`'s spinner backstop and dead-air
detection are deliberately aggressive (drive-postprocess): a stretch with
only small, localized pixel change — a spinner, a blinking cursor, a
loading bar — reads as dead air and gets fast-forwarded even with no
timeline span marking it. A reveal is anything the viewer is meant to
consciously register, not just anything on screen. Attach an `h.annotate(...)`
naming it or a `h.hold(...)` framing it before the action module moves on.

## Terminal recording — the tape contract

A **tape** is a plain `vhs` script — the same file `vhs` itself runs, with no
sidecar and no drive-specific syntax. `drive.py tape <tape-file>` runs it
completely unmodified: the only thing the verb does beyond invoking `vhs` is
read the tape's own `Output <path>` directive back out, to know where the
recording landed, and read the tape's own comments back out, to build the
timeline. Nothing about the tape's content is drive-specific except those
comments — a tape without any of them is still a perfectly ordinary `vhs`
file, runnable with `vhs` directly.

The timeline `tape` emits carries `holds` and `leadingCut` only — never
`spans` (drive-tape-timeline). A tape's `Sleep` directives describe the
*intended* length of a pause, not the real recorded duration, so no span is
ever derived from one; every dead-air stretch is left to `post`'s spinner
backstop, exactly as an unannotated tape is (below).

Three comments carry the annotations, each on its own line:

- **`#hold`** — opens a protected window at this point in the tape;
  everything from here forward plays at normal speed regardless of how
  static it looks, until the matching `#endhold`. An unclosed `#hold` (no
  `#endhold` before the tape ends) extends to the end of the recording.
- **`#endhold`** — closes the most recently opened `#hold`.
- **`#ready`** — marks the point the shell prompt has settled after the
  terminal's own startup; that offset becomes the timeline's `leadingCut`, so
  `post` cuts everything before it. Only the first `#ready` in a tape is
  honored.

Offsets accumulate from the tape's own timing directives in the order they
appear: each `Sleep <duration>` adds its duration, and each keystroke adds
one typing interval — `Type "text"` costs one interval per character, a bare
keypress (`Enter`, `Tab`, `Enter 3`) costs one per press. The interval is
`vhs`'s 50ms default, overridden for the rest of the tape by
`Set TypingSpeed <duration>` or for one line by `Type@<duration>`.

Keystrokes have to be counted because they are real recorded time: a tape
that types three commands before its first reveal has already spent a second
or more of video, and a hold computed without that would protect a stretch
that has not happened yet. A command's own runtime needs no modeling — `vhs`
launches it and moves straight to the next directive, so it runs *during* the
`Sleep` that follows rather than adding to the clock. Give a command a `Sleep`
long enough to finish in, and the clock stays aligned with the recording.

A `#hold`/`#endhold` pair still protects nothing unless a `Sleep` sits
between them: the window's whole purpose is to keep a static stretch at
normal speed, and a pair enclosing no pause encloses no stretch.

### A worked tape

```
Output demo.mp4
Set FontSize 20
Set Width 1200
Set Height 600

Type "shipd status"
Enter
Sleep 1s
#ready

Type "shipd build my-change"
Enter
#hold
Sleep 3s
#endhold
Sleep 500ms
Type "echo done"
Enter
Sleep 1s
```

Here the shell prompt is considered settled once `shipd status` has been
typed, entered, and given a second to print — 12 keystrokes plus `Enter` at
50ms, then `Sleep 1s`, so `#ready` puts `leadingCut` at `1.65`. The
three-second reveal after `shipd build` is protected by the
`#hold`/`#endhold` pair: the 21 keystrokes and `Enter` before it cost a
further `1.10`, so the window is `2.75` to `5.75` and plays at normal speed
rather than being swept into the backstop's fast-forward. The half-second
`Sleep` before the final `echo done` carries no annotation. The backstop
classifies it, as it does every other unannotated stretch.
