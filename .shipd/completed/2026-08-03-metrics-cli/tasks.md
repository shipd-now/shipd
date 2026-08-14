## 1. Pure renderer and formatting helpers

- [x] 1.1 [req: metrics-cli] In `plugins/s/skills/build/tests/test_metrics.py`,
      add tests for the new pure helpers in
      `plugins/s/skills/build/scripts/metrics.py`: `_fmt_duration` (`42s`,
      `12m`, `3.4h`, `2.1d`, `None` → "n/a"), `_fmt_tokens` (`950`, `85k`,
      `1.2M`, `None` → "n/a"), `_fmt_pct` (whole percent, `None` → "n/a"); and
      `render_summary_lines(metrics)` on a derive-shaped dict — asserts the
      throughput line (total, last-4-week counts, trend `↑`/`↓`/`→`, trend
      omitted under five weeks of history), the DORA-band line, lead/cycle
      lines showing median + p85 + `n=` (and never the word `mean`), the
      rework-rate percentage with the pre-merge-proxy label, WIP by state
      (count-descending), the cost line, and that an all-empty derive dict
      renders "n/a" values without raising. Run and observe failure.
- [x] 1.2 [req: metrics-cli] Implement `_fmt_duration`, `_fmt_tokens`,
      `_fmt_pct`, and `render_summary_lines(metrics)` in
      `plugins/s/skills/build/scripts/metrics.py` per `plan.md`'s binding
      layout (header, throughput + trend, deployment frequency, lead time,
      cycle time, rework rate, wip, cost). Pure functions, list-of-lines out,
      no I/O. Confirm 1.1 passes.

## 2. The summary verb

- [x] 2.1 [req: metrics-cli] In
      `plugins/s/skills/build/tests/test_metrics.py`, add CLI tests driving
      `metrics.main(argv)` against a fixture root (reuse the existing fixture
      helpers; capture stdout via `contextlib.redirect_stdout`):
      `main(["summary", "--root", root])` exits `0` and prints the summary
      lines; `main(["summary", "--root", root, "--json"])` prints JSON that
      parses back to the derive blocks (`throughput`, `deployment_days`,
      `lead_time`, `cycle_time`, `wip`, `outcomes`, `cost`); an empty fixture
      root exits `0` with "n/a" values; and `import metrics` alone executes no
      CLI (module import prints nothing). Run and observe failure.
- [x] 2.2 [req: metrics-cli, metrics-engine] In
      `plugins/s/skills/build/scripts/metrics.py`, replace the `__main__`
      refusal block with the CLI: `main(argv=None)` using argparse subparsers
      (`summary` with `--root` default cwd and `--json`, wired via
      `set_defaults(func=_cmd_summary)` per the `dashboard.py` pattern),
      `_cmd_summary` calling `derive` then printing `render_summary_lines`
      output or `json.dumps(..., indent=2, sort_keys=True)` under `--json`, and
      `if __name__ == "__main__": raise SystemExit(main())`. Update the module
      docstring's API-only claim to name the summary verb. Confirm 2.1 passes.

## 3. Version bump and verification

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above
      the branch base (base is 0.6.38, so 0.6.39 — pick the next free one if
      taken, verifying against branches/tags/history).
- [x] 3.2 [req: *] Run the full dependency-free suite `python3 -m unittest
      discover -s plugins/s/skills/build/tests` with `textual` NOT installed —
      it must pass including the new tests — then manually exercise the real
      behavior: run `python3 plugins/s/skills/build/scripts/metrics.py summary
      --root .` against THIS repo and sanity-check the output (non-zero
      throughput, plausible DORA band, `n=` counts, "n/a" only where data is
      genuinely absent, `--json` parses), pasting the printed summary into the
      task completion note.
