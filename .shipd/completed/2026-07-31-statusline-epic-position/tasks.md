## 1. Epic position marker

- [x] 1.1 [req: statusline-rendering] In
      `plugins/s/skills/build/tests/test_statusline.py`, add tests with a
      fixture epic file (`.shipd/epics/some-epic/epic.md` carrying a
      `| Change | ... |` members table): (a) a picked change listed as the
      2nd of 3 member rows renders
      `(EPIC: some-epic, spec 2/3)` after the name; (b) no epic file →
      literal `(EPIC)`; (c) epic file whose table lacks the change's row →
      literal `(EPIC)`; (d) a worktree candidate reads the epic file under
      its own worktree's `.shipd/epics/`, not the root's (give the two files
      different tables and assert the worktree's position wins); (e) a
      standalone change still renders no `(EPIC` text. Run the file and
      observe the new tests fail.
- [x] 1.2 [req: statusline-rendering] In
      `plugins/s/integrations/statusline.sh`: add an `epic_position()`
      helper (args: epic file path, change name) that filters `^|` table
      rows, drops `---` separator rows and the header row whose first cell
      is `Change`, numbers the member rows, and prints `pos total` for the
      row whose first cell equals the change name (nothing on any miss) —
      sed/grep/while-read only, bash 3.2. In the render section, when the
      picked candidate's epic slug is non-empty, derive the epic file as
      `base="${d%/planned/"$name"/}"` from `${cand_dir[$pick]}` →
      `$base/epics/<slug>/epic.md`, call `epic_position`, and render
      ` (EPIC: <slug>, spec <pos>/<total>)` on a hit or ` (EPIC)`
      otherwise, in the same spot the bare marker occupies today. Confirm
      the 1.1 tests pass.

## 2. Ship gate

- [x] 2.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next free patch above
      `origin/main`'s current value at the time this task runs (0.6.7 as
      of planning — re-read origin/main first; other changes are merging
      concurrently).
- [x] 2.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from
      the repo root and observe zero failures; then pipe a session JSON at
      a fixture workspace (epic member change + members table) through
      `plugins/s/integrations/statusline.sh` and observe the enriched
      marker in the raw output.
