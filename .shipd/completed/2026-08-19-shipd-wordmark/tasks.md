## 1. Wordmark module

- [x] 1.1 [req: wordmark-static, wordmark-animation, wordmark-cli] Add
      `plugins/s/skills/build/tests/test_wordmark.py` covering: piped
      `render` output byte-identical to the fenced banner lines at
      `README.md:2-5` with no `\x1b`; `NO_COLOR=1` on a TTY-like stream →
      no `\x1b`; colored render carries `\x1b[38;2;136;136;160m` on the
      leftmost glyph column, `\x1b[38;2;198;255;78m` on the rightmost, and
      per-line `\x1b[0m`; `ART` equals the README fence lines; `animate` on
      a non-TTY stream writes one plain render with zero spy-sleep calls;
      `animate` on a TTY-like stream with a spy sleep is bounded, hides
      `\x1b[?25l` and restores `\x1b[?25h` the cursor, records every
      color-phase delay strictly smaller than every reveal-phase delay, and
      ends with the static colored glyph output; `python3 wordmark.py` and
      `python3 wordmark.py --animate` piped each print exactly one plain
      banner and exit 0. Write the tests unittest-style (the suite's
      convention), run
      `python3 -m unittest plugins.s.skills.build.tests.test_wordmark -v`
      from the repo root (or discovery scoped to the file), and observe it
      fail — the module does not exist yet.
- [x] 1.2 [req: wordmark-static] Add
      `plugins/s/skills/build/scripts/wordmark.py` with `ART` (the four
      banner lines copied byte-for-byte from `README.md:2-5`, trailing
      spaces preserved), a per-column linear RGB interpolation helper from
      `(136, 136, 160)` to `(198, 255, 78)`, and `render(stream)` writing
      plain lines when `cli_common.color_enabled(stream)` is false and the
      truecolor-gradient lines (per-glyph `\x1b[38;2;r;g;bm`, `\x1b[0m` at
      line end) when true.
- [x] 1.3 [req: wordmark-animation] In the same file add
      `animate(stream, *, reveal_delay=0.035, color_delay=0.012,
      sleep=time.sleep)`: color-disabled streams get exactly one plain
      `render` and no sleep calls; otherwise hide the cursor, run the
      left-to-right white letter-by-letter reveal at `reveal_delay`, then
      the faster left-to-right gradient wipe at `color_delay` (frames redrawn
      in place via `\x1b[<n>A`), settle on the static colored render, and
      restore the cursor in a `finally`.
- [x] 1.4 [req: wordmark-cli] In the same file add an `argparse` `main`
      (bare run → `render(sys.stdout)`; `--animate` → `animate(sys.stdout)`;
      exit 0) behind `if __name__ == "__main__"`; then run the CI suite
      command `python3 -m unittest discover -s plugins/s/skills/build/tests
      -v` without `textual`/`pydantic` installed, and observe all tests
      pass, the new wordmark tests included.

## 2. Ship the snapshot

- [x] 2.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version`
      from `0.6.137` to `0.6.138` — the cache snapshot is keyed by version,
      so the new module only reaches installed launchers with the bump.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 50 | 21.1k |
| Write | 2 | 9.3k |
| Edit | 9 | 5.5k |
| (no tool) | 0 | 3.9k |
| Agent | 2 | 789 |
| Read | 7 | 767 |
| **Total** | 70 | 41.4k |
