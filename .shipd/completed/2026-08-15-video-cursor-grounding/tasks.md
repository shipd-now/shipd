## 1. Cursor pipeline port

- [x] 1.1 [req: video-cursor-localization, video-cursor-carry-forward, video-cursor-crops, video-skill-cursor-crop]
      Port the new test file:
      `python3 tools/port.py apply --source /Users/mikkelbergmann/projects/automikk --ref af7ec71 --include plugins/am/skills/video-ingest/tests/test_video_cursor.py --dest .`
      from the worktree root (expected exit 0 — this file ports
      residual-free). Run
      `python3 -m unittest discover -s plugins/s/skills/video-ingest/tests -q`
      and observe the new cursor cases fail against the current
      `video_ingest.py` (baseline before this change is 101 tests, OK).
- [x] 1.2 [req: video-cursor-localization, video-cursor-carry-forward, video-cursor-crops]
      Port the implementation:
      `python3 tools/port.py apply --source /Users/mikkelbergmann/projects/automikk --ref af7ec71 --include plugins/am/skills/video-ingest/scripts/video_ingest.py --dest .`
      from the worktree root (expected exit 0 — verified residual-free by a
      scratch port; the overwrite replaces 5 lines and adds the cursor
      pipeline). Re-run the suite from task 1.1; all tests pass.

## 2. Skill surface

- [x] 2.1 [req: video-skill-cursor-crop] Port the skill doc:
      `python3 tools/port.py apply --source /Users/mikkelbergmann/projects/automikk --ref af7ec71 --include plugins/am/skills/video-ingest/SKILL.md --dest .`
      from the worktree root. This apply is expected to exit 2 naming exactly
      two residuals at `plugins/s/skills/video-ingest/SKILL.md:28` and `:29`
      (bare `am:video-ingest` forms upstream never fixed; the overwrite
      reverts shipd's existing fix) — edit both lines back to
      `s:video-ingest`. Then review `git diff` on the file: the net change is
      only the #211 cursor-crop additions. Confirm cleanliness with
      `python3 tools/port.py verify --dest .` and grep its output for the
      path `plugins/s/skills/video-ingest/SKILL.md` — that file must not
      appear; do NOT
      re-run `apply` as the check (it rewrites from source and reverts the
      fix). Any residual named on a line the port did not touch beyond those
      two is handled the same way (fix to the `s:`/`shipd` form); a residual
      inside the newly ported text itself is unexpected and question-worthy.

## 3. Ship gate

- [x] 3.1 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` by one patch level.
- [x] 3.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/video-ingest/tests -q`
      (video suite including the ported cases),
      `python3 -m unittest discover -s plugins/s/skills/build/tests -q`
      (engine suite, untouched but re-confirmed), and
      `python3 plugins/s/skills/build/scripts/spec_lint.py` (master library
      clean); all exit 0.
