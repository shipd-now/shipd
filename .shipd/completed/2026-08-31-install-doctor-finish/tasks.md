## 1. The finish seam in install_tui

- [x] 1.1 [req: install-doctor-finish] In
      `plugins/s/skills/build/tests/test_install_tui.py`, add tests for a
      `finish` callable passed to `it.run`: give `PtyTest.drive` an optional
      `finish` argument it forwards to `it.run`, then assert (a) a confirmed
      toggle-and-enter run calls it exactly once with the flow's terminal
      handle, (b) an aborted run (`q`) never calls it, (c) a bare-confirm run
      with no harness selected calls it once, and (d) the headless path
      (`open_tty` patched to `None`, as in `NoTerminalTest`) never calls it.
      Run the file and observe the failures — `run` takes no `finish` yet.
- [x] 1.2 [req: install-doctor-finish] In
      `plugins/s/skills/build/scripts/install_tui.py`, add a `finish=None`
      parameter to `run` (line 494) and to `main` (line 536), `main` passing
      it through to `run`. Restructure `run`'s confirmed branch so that, after
      `save_record(chosen)`, both the empty-selection note path and the
      `install_selection` report path fall through to a single
      `if finish is not None: finish(tty)` call before returning 0; the abort
      branch, the headless branch, and the `install_selection` refusal branch
      (exit 1) return without calling it. Extend the module docstring's layer
      list to name the hook. Re-run
      `python3 plugins/s/skills/build/tests/test_install_tui.py` and confirm
      it passes.

## 2. The doctor finish in the binary

- [x] 2.1 [req: install-doctor-finish] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add a
      `DoctorFinishTest` driving `shipd.doctor_finish(handle, root=..., checks=...)`
      with a stub `checks` callable over fabricated `(level, name, detail)`
      triples, asserting: an all-`ok` set writes the heading constant, one
      line per check, the `doctor: ok` summary, and **no** pointer line; a set
      containing a `fail` writes that line, the `doctor: 1 problem(s)`
      summary, and one pointer line containing `/s:doctor`; a set containing
      only a `warn` also writes the pointer; and `doctor_finish` returns
      `None` in every case rather than an exit code. Then extend
      `InstallVerbTest` with a test that patches `shipd._load_install_tui` and
      `shipd.iu` so `iu.main` records its keyword arguments, and asserts
      `cmd_install` passes `finish=shipd.doctor_finish` and returns `iu.main`'s
      own code. Run the file and observe the failures.
- [x] 2.2 [req: install-doctor-finish] In `plugins/s/bin/shipd`, in the
      `install` section beside `cmd_install` (line 1979), add two module
      constants — the finish heading and the pointer line naming `/s:doctor`
      as the flow that works through the findings — and
      `def doctor_finish(handle, root=None, checks=None)`: default `checks` to
      `default_checks` (line 869) and `root` to `os.getcwd()`; write a blank
      line, the heading, and a blank line to `handle` and flush it *before*
      calling `checks(root)`; pass the results to `doctor_report` (line 887)
      and write its lines to `handle`; when any result's level is not `ok`,
      write a blank line and the pointer line. Discard `doctor_report`'s exit
      code and return `None` — the preflight's verdict must not reach the
      caller.
- [x] 2.3 [req: install-doctor-finish] In `plugins/s/bin/shipd`, change
      `cmd_install` (line 1979) to `return iu.main(args, finish=doctor_finish)`
      and extend its docstring to say the verb closes a confirmed selection
      with the read-only preflight whose verdict never changes the exit code.
      Re-run `python3 plugins/s/skills/build/tests/test_shipd_cli.py` and
      confirm it passes.

## 3. Documentation and version

- [x] 3.1 [req: harness-mode-docs] In `README.md`, extend the install finish
      paragraph (the "On a terminal the installer finishes by running
      `shipd install`" block, lines 89-104) to state that a confirmed finish
      closes by running the read-only `shipd doctor` preflight on the same
      terminal, that findings are worked through with `/s:doctor`, and that
      the headless and aborted paths run no preflight. Keep the existing
      "Verify with: `shipd doctor`" snippet as the standalone re-check.
- [x] 3.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.165` to `0.6.166` —
      the cache snapshot is keyed by version, so `plugins/s/` edits without a
      bump keep sessions on the stale snapshot (AGENTS.md).
- [x] 3.3 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` (the
      CI command) from the worktree root and confirm the whole stdlib suite
      passes, then run `plugins/s/bin/shipd install </dev/null` and confirm
      the headless output and exit code are unchanged.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 88 | 10.6k |
| Edit | 13 | 2.8k |
| (no tool) | 0 | 738 |
| Monitor | 1 | 689 |
| Agent | 2 | 688 |
| Read | 25 | 330 |
| ToolSearch | 2 | 25 |
| **Total** | 131 | 15.8k |
