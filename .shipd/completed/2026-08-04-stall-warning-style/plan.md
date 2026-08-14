# stall-warning-style

Status: verified

## Idea

Style the epic-detail stall warning as a rectangular error-red banner with
white text, make its message point at the Retry button, and render the Retry
button's full label.

### Motivation

The just-shipped stall warning renders as bare unstyled lines, its message
never tells the user the run can be restarted, and the Retry button was given
the 3-cell `compact-button` class (the ✕-control style) so its label truncates
to "R" — the user asked for a red banner with white text, guidance text, and a
button that reads "Retry".

### Details

- Wrap the stall warning lines and the Retry button in a banner container
  rendered with the registered theme's error color as its background and white
  text.
- Extend the warning's first line to state the run can be started again by
  clicking Retry.
- Drop `compact-button` from the Retry button so its full `Retry` label shows.

Affected capabilities: `delivery-dashboard` (modified — the
`board-stall-signal` requirement). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`, plugin version bump.

### Non-goals

- No change to the group-header ✗ marker — the user confirmed it as shipped.
- No change to the stall predicate, the Retry dispatch, or the autopilot
  reclaim — presentation only.
- No change to the board's HTML page.

## Implementation

- **Banner container.** In `EpicDetailScreen.compose`, wrap the existing
  warning `Static`s and the Retry `Button` in a `Vertical` with
  `id="epic-stall-banner"`, styled in `EpicDetailScreen.CSS` as
  `background: $error; color: $shipd-on-error; padding: 0 1; height: auto;`
  — `$error` follows the registered shipd theme (`error="#FF4D3D"`), and the
  white foreground (the user's explicit design call) routes through a new
  role-named theme variable `"shipd-on-error": "#FFFFFF"` added to
  `SHIPD_THEME.variables`, because the existing
  `test_widget_css_carries_no_hard_coded_colors` guard bans hex literals *and*
  the named tokens `black`/`white` in widget CSS — every chrome color must be
  theme-owned. Rejected: `color: white` literal — trips that guard. Rejected:
  relaxing the guard — it enforces the board-shipd-theme rule and the token
  route satisfies both it and the user's ask. Rejected: `color: auto`
  auto-contrast — it may resolve to black on this red and the user asked for
  white specifically.
- **Message.** The banner's first line becomes
  `stalled: <n> member(s) parked needs-human — click Retry to start the run
  again`. Per-member lines are unchanged (still `markup=False`).
- **Button label.** Remove `classes="compact-button"` from the Retry button
  (that class pins 3-cell ✕ controls and truncated the label to "R"); keep
  `id="epic-retry"`. With the class gone the button renders its full label
  like the confirm modal's Yes/No buttons. Give it `width: auto` inside the
  banner CSS block if the default sizing pads excessively.
- **Tests.** Update `StalledEpicDetailTest` in
  `tests_textual/test_dashboard.py`: the warning widgets mount inside
  `#epic-stall-banner`, the banner's resolved background is the theme's error
  color and its color is white, the header line contains `click Retry to start
  the run again`, and the mounted Retry button's label text is exactly
  `Retry` with no `compact-button` class. The existing dispatch/dismiss and
  non-stalled (no banner) assertions stay, retargeted to the banner id.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` → `0.6.46`.

Risk: none beyond visual regression; the textual geometry tests and the
existing retry-dispatch tests pin the behavior around the restyle.
