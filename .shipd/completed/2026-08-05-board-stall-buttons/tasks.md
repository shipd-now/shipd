# Tasks — board-stall-buttons

## 1. Stall banner redesign

- [x] 1.1 [req: board-stall-signal] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, rewrite the
      stall-banner test block (currently asserting error background, white
      text, bold header, `margin.bottom == 1`, and the three-cell inset) to
      assert the new design: the banner is a `Horizontal` whose background
      resolves the theme `error` color at 10% alpha, holding a one-cell
      `.stall-accent-bar` Static with solid `error` background; a
      `.stall-title` Static reading `STALLED` (bold, error color) beside a
      `.stall-summary` reading `1 member(s) parked · needs-human`; a
      `.stall-member-row` with the slug, muted stage, and a
      `.stall-reason-chip` (warning color on 10% warning tint); a
      `.stall-note` Static carrying the checkpoint reassurance line; and a
      `#epic-retry` Button labeled exactly `Retry run` with class
      `button-primary` beside a `.stall-age` Static reading `parked … ago`.
      Resolve expected colors via `app.get_css_variables()` per suite
      convention. Run the suite and observe these tests fail.
- [x] 1.2 [req: board-stall-signal] In
      `plugins/s/skills/build/scripts/dashboard.py`, change `_age` to
      `_age(updated_at, verb="updated")`, using `verb` in all four return
      strings; add pure-renderer tests in
      `plugins/s/skills/build/tests_textual/test_dashboard.py` covering
      `verb="parked"` (`parked 5s ago`-shape and the `parked ?` fallback) and
      the unchanged default.
- [x] 1.3 [req: board-stall-signal] In
      `plugins/s/skills/build/scripts/dashboard.py`, rework the
      `EpicDetailScreen` stall banner: add the module constant `_STALL_NOTE`
      and rebuild the `compose` banner block and the `#epic-stall-banner` CSS
      to the structure, classes, and copy bound in `plan.md`
      (`## Implementation`), wiring `Retry run` to the existing `epic-retry`
      id and the `parked <age> ago` label to
      `_age(hb.get("updated_at"), verb="parked")`. Confirm the 1.1 tests now
      pass.

## 2. Button hierarchy

- [x] 2.1 [req: board-control-hierarchy] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add tests
      asserting: the run-confirm `Yes` button carries `button-primary`
      (background resolves the theme accent, dark bold label) and `No`
      carries `button-secondary` (background resolves `$bg-hover`, muted
      text); the active `.mode-active` mode button resolves the solid accent
      background with dark text while inactive `.mode-button`s resolve
      `$bg-hover` with `$fg-muted`; and a modal title bar's `✕` compact
      button resolves `$accent` background with `$background` glyph color.
      Run the suite and observe these tests fail.
- [x] 2.2 [req: board-control-hierarchy] In
      `plugins/s/skills/build/scripts/dashboard.py`, add the
      `.button-primary` / `.button-secondary` classes (with hover states) to
      `BoardApp.CSS` per `plan.md`, restyle `.mode-button` / `.mode-active`,
      add the `.modal-title-bar .compact-button` accent override to every CSS
      block that styles a modal title bar, and tag the run-confirm `Yes` /
      `No` buttons with the new classes in `EpicRunConfirmScreen.compose`.
      Confirm the 2.1 tests now pass.

## 3. Theme cleanup and ship gates

- [x] 3.1 [req: board-stall-signal] In
      `plugins/s/skills/build/scripts/dashboard.py`, remove the now-unused
      `shipd-on-error` entry from `SHIPD_THEME.variables` and confirm no
      reference to it remains in the file or in
      `plugins/s/skills/build/tests_textual/test_dashboard.py`.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      `0.6.57` (cache-snapshot rule: every `plugins/s/` change bumps in the
      same PR).
- [x] 3.3 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` (must
      pass with no `textual` import required) and the `tests_textual` suite
      with `textual` installed; both green.
