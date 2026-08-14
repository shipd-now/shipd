## 1. Board modes

- [x] 1.1 [req: cli-dispatch] Extend
      `plugins/s/skills/build/tests/test_shipd_cli.py` with board-mode tests,
      reusing the existing `HAS_TEXTUAL` skip guard (line 52) for every case
      that invokes `dashboard.py` as a subprocess: `shipd board --help`
      output is byte-identical to `dashboard.py tui --help` with exit 0;
      `shipd board text --root <temp repo>` output matches `dashboard.py
      board --root <temp repo>` with exit 0; `shipd board html --out <tmp
      file> --once` writes the file once and exits 0; `shipd tui` exits 2
      with the usage banner on stderr (no guard needed — no delegation).
      Update the existing board-delegation test to the `board text` form.
      Run the file and observe the new tests fail.
- [x] 1.2 [req: cli-dispatch] In `plugins/s/bin/shipd`: add a
      `BOARD_MODES` table (`None` → `dashboard.py tui`, `"text"` →
      `dashboard.py board`, `"html"` → `dashboard.py html`); in `main`,
      when the verb is `board`, consume the first trailing argument only if
      it is exactly `text` or `html` and delegate through the ordinary
      `os.execv` path with the remaining arguments verbatim; remove the
      `tui` entry from `VERB_TABLE`; update `USAGE` to show
      `board [text|html]` and drop the `tui` line. Confirm the 1.1 tests
      pass.
- [x] 1.3 [req: cli-dispatch] Update `README.md`'s `## The shipd CLI` verb
      table: `shipd board` is the interactive board, `shipd board text` the
      one-shot text board, `shipd board html --out <file>` the
      self-refreshing HTML page; remove the `shipd tui` line.
- [x] 1.4 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.97` to `0.6.98`.
- [x] 1.5 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual` installed and confirm
      it passes (board-mode delegation tests skip; everything else green).
