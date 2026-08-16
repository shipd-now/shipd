## 1. CLI dispatch (test-first)

- [x] 1.1 [req: cli-dispatch] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, replace
      `test_board_html_writes_one_snapshot` (~line 209) with a fall-through
      test: `shipd board html --out <path> --once` exits `2` with
      `unrecognized arguments` on stderr and writes no file; also update the
      provisioning comment at ~line 71 to stop naming `html`. Run
      `python3 -m unittest tests.test_shipd_cli` from
      `plugins/s/skills/build` and observe the new test fail (the binary
      still consumes `html`).
- [x] 1.2 [req: cli-dispatch] In `plugins/s/bin/shipd`, remove the `"html"`
      entry from the board-mode mapping (~line 66) and the `[text|html]`
      usage-banner text (~line 81, now `[text]`). Confirm the test from 1.1
      passes.

## 2. Dashboard engine removal

- [x] 2.1 [req: board-html] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, delete the
      "HTML renderer and the html verb" test section (~lines 654-690).
- [x] 2.2 [req: board-html] In
      `plugins/s/skills/build/scripts/dashboard.py`, remove
      `render_board_html` (~1229-1289), `_write_html_atomic` and `_cmd_html`
      (~4363-4380), the `html` subparser block (~4418-4430), the now-unused
      `import html` (~line 27), and the html mentions in the module docstring
      (~lines 6-7) and the self-provision comment (~line 866, "every verb
      (`tui`/`board`/`html`)" → the remaining verbs). Run
      `python3 -m unittest tests_textual.test_dashboard` from
      `plugins/s/skills/build`.

## 3. Docs and ship hygiene

- [x] 3.1 [req: board-html] In `README.md`, remove the
      `shipd board html --out <file>` line (~225) and rewrite the board-mode
      sentence (~232) so the optional mode word is `text` only.
- [x] 3.2 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.105` to `0.6.106` (plugin-cache rule in `AGENTS.md`).
- [x] 3.3 [req: *] From `plugins/s/skills/build`, run
      `python3 -m unittest discover -s tests` and
      `python3 -m unittest discover -s tests_textual`; both must pass. Also
      run `plugins/s/bin/shipd board text --root <worktree-root>` and confirm
      the text board still prints with exit `0`.
