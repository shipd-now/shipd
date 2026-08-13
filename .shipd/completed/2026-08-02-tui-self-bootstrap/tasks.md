## 1. Stdlib bootstrap module (dependency-free, seamed)

- [x] 1.1 [req: board-tui] In `plugins/s/skills/build/tests/test_tui_bootstrap.py`
      (new), add dependency-free tests with injected seams for a new
      `tui_bootstrap` module: `venv_dir` honors `XDG_CACHE_HOME` and falls back to
      `~/.cache/shipd/tui-venv`; `find_requirements` walks up from the scripts
      dir to the repo-root `requirements.txt`; `ensure_textual` is a no-op when
      `has_textual` returns True; when `textual` is missing and the venv already
      has it, it re-execs the venv python with `argv[1:]` and runs no install; on
      a fresh venv it runs `venv` then `pip install -r requirements.txt` then
      re-execs; and a failing step prints the hint and raises `SystemExit(1)`.
      Run and observe failure.
- [x] 1.2 [req: board-tui] Create
      `plugins/s/skills/build/scripts/tui_bootstrap.py` (stdlib only): pure
      `venv_dir(environ)`, `venv_python(venv_dir)`, `find_requirements(start)`,
      and `ensure_textual(argv, script, *, has_textual, venv_has_textual, run,
      execv, out, environ)` with real defaults (`importlib`/`subprocess`/
      `os.execv`), printing the one-time "Setting up the delivery board…" line on
      stderr and falling back to the `pip install` hint + `SystemExit(1)` on any
      failure. Confirm 1.1 passes.

## 2. Wire the bootstrap into dashboard.py

- [x] 2.1 [req: board-tui] In `dashboard.py`, add `import tui_bootstrap` and a top
      `if __name__ == "__main__":` block **above** the `textual` import that calls
      `tui_bootstrap.ensure_textual(sys.argv, __file__)`; change the module-scope
      `textual` import guard to re-raise `ImportError` instead of
      `print(...)+sys.exit(1)` (the `__main__` bootstrap makes it unreachable for
      script use). Leave the bottom `main()`/`__main__` and the App unchanged.
- [x] 2.2 [req: board-tui] Add a `tests_textual` check that with `textual`
      importable, `tui_bootstrap.ensure_textual` (via seams) performs no venv work
      and the module imports and runs normally — guarding the skip-when-present
      path end to end.

## 3. gitignore, version bump & verification

- [x] 3.1 [req: board-tui] Add `.venv/` to `.gitignore`.
- [x] 3.2 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.26, so 0.6.27 — pick the next free one if taken).
- [x] 3.3 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed,
      including the new `test_tui_bootstrap`), then `pip install -r
      requirements.txt` in a venv and run `plugins/s/skills/build/tests_textual`;
      both green.
- [x] 3.4 [req: *] Manually verify the bootstrap: with `textual` absent from the
      interpreter, run `python3 plugins/s/skills/build/scripts/dashboard.py tui`
      and confirm it prints the setup line, creates the cache venv, installs
      textual, re-execs, and launches the board (press `q` to quit); a second run
      reuses the venv with no install.
