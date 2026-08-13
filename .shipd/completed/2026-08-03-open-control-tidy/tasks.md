# Tasks

## 1. Even three-cell controls with a gap

- [x] 1.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`: in
      `EpicHeaderControlPlacementTest.test_runnable_controls_pack_after_the_title`,
      replace the `open.region.offset == run.region.top_right` assertion with
      `open.region.x == run.region.right + 1` and
      `open.region.y == run.region.y` (one-cell gap), and add
      `self.assertEqual(run.region.width, 3)` and
      `self.assertEqual(open_.region.width, 3)`; in `CompactControlTest`, add
      a `region.width == 3` assertion next to every existing
      `region.height == 1` assertion (the header pair and the three modal ✕
      controls). Run
      `/Users/mikkelbergmann/projects/shipd/.venv/bin/python -m unittest
      discover -s plugins/s/skills/build/tests_textual` from the worktree
      root and observe the gap and open-width assertions fail (the open
      control is currently four cells wide and flush to the run control).
- [x] 1.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`: change the open
      control's Button label from `"☰"` to `"≡"` (U+2261, one cell under
      Rich); in `BoardApp.CSS`, replace `.compact-button`'s `width: auto;` with
      `width: 3;`, keeping `min-width: 3;` (Textual's base Button rule sets
      `min-width: 16`, which clamps the button without that override); in `_mount_epic_groups`'s `_flush`,
      when `run_button` is constructed, set
      `open_button.styles.margin = (0, 0, 0, 1)` (one-cell left margin in the
      controls-layer flow, so the open control lands one cell after the run
      control; no margin when the epic is not runnable, keeping the open
      control flush to the title); extend the open-control comment with the
      glyph note (`☰` measures two cells under Rich, `≡` measures one — the
      swap keeps every compact control exactly three cells wide) and the
      conditional-margin note. Update the `☰` mention in
      `CompactControlTest`'s docstring to `≡`.
- [x] 1.3 [req: board-epic-grouping] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.36` to `0.6.37`.
- [x] 1.4 [req: board-epic-grouping] From the worktree root, run both suites:
      `/Users/mikkelbergmann/projects/shipd/.venv/bin/python -m unittest
      discover -s plugins/s/skills/build/tests_textual` and
      `python3 -m unittest discover -s plugins/s/skills/build/tests` — all
      green.
