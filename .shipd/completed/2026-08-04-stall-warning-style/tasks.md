## 1. Banner restyle

- [x] 1.1 [req: board-stall-signal] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, update
      `StalledEpicDetailTest`: assert the stall warning widgets and the Retry
      button mount inside a `#epic-stall-banner` container whose resolved
      `styles.background` equals the active theme's error color and whose
      resolved `styles.color` is white; the warning's first line contains
      `click Retry to start the run again`; the mounted `#epic-retry` button's
      label text is exactly `Retry` and `compact-button` is not among its
      classes; the non-stalled case mounts no `#epic-stall-banner`. Keep the
      existing dispatch-and-dismiss assertions. Run and observe the new
      assertions fail.
- [x] 1.2 [req: board-stall-signal] In
      `plugins/s/skills/build/scripts/dashboard.py`, wrap the stall warning
      `Static`s and the Retry `Button` in `EpicDetailScreen.compose` in a
      `Vertical` with `id="epic-stall-banner"`; add the role-named variable
      `"shipd-on-error": "#FFFFFF"` to `SHIPD_THEME.variables`; add to
      `EpicDetailScreen.CSS`: `#epic-stall-banner { background: $error;
      color: $shipd-on-error; padding: 0 1; height: auto; }` and
      `#epic-stall-banner Button { width: auto; }`; change the warning's first
      line to
      `stalled: %d member(s) parked needs-human — click Retry to start the
      run again`; remove `classes="compact-button"` from the Retry button
      (keep `id="epic-retry"`). Confirm the 1.1 tests pass.

## 2. Ship

- [x] 2.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to `0.6.46`.
- [x] 2.2 [req: *] Run both suites — `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and
      `/Users/mikkelbergmann/projects/shipd/.venv/bin/python3 -m unittest
      discover -s plugins/s/skills/build/tests_textual` — and confirm green.
