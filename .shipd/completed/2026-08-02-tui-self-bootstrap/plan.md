# tui-self-bootstrap
Status: verified

## Idea

Make `dashboard.py` auto-provision its `textual` dependency: when `textual` is
missing, create/reuse a cached virtualenv, install the pinned dependency, and
re-exec — so the board "just works" with no manual `pip install` and without
touching the system Python.

### Motivation

`textual` is not installed by `claude plugin update` (it only refreshes the file
snapshot — no pip), so today the board errors with a manual `pip install` hint;
users expect the TUI to run after a plugin update, and the current
module-scope `textual` import even makes the stdlib `board`/`html` verbs require
it.

### Details

- Add a stdlib `tui_bootstrap.py` with `ensure_textual(argv, script)`: if
  `textual` is importable, no-op; otherwise create-or-reuse a venv at
  `${XDG_CACHE_HOME:-~/.cache}/shipd/tui-venv`, `pip install -r
  requirements.txt` into it (printing a one-time "Setting up the delivery
  board…" line on stderr), and `os.execv` the same command with that venv's
  interpreter. On provisioning failure (e.g. offline) print the clear install
  hint and exit non-zero.
- Call `ensure_textual` at the top of `dashboard.py`'s `__main__` path, **before**
  the `textual` import — so any verb (`tui`/`board`/`html`) provisions the
  dependency when it is missing, and provisioning is skipped when `textual` is
  already present. Replace the module-scope `sys.exit(1)`-on-`ImportError` guard
  with a plain re-raised `ImportError` (the `__main__` bootstrap makes it
  unreachable for script use).
- Add `.venv/` to `.gitignore`.

Affected capability: `delivery-dashboard` (modified `board-tui`). Impact: new
`plugins/s/skills/build/scripts/tui_bootstrap.py`, `dashboard.py` (entry +
import guard), `.gitignore`, tests in `plugins/s/skills/build/tests/`; plugin
version bump.

### Non-goals

- No change to the board's rendering, data layer, or the pinned `textual`
  version — only how the dependency gets installed.
- No auto-provisioning at module **import** time — only on a `__main__` script
  invocation; importing `dashboard` without `textual` raises a normal
  `ImportError`.
- No system-wide install and no `--break-system-packages`; the cached venv is the
  only textual home the bootstrap creates.
- No auto-upgrade of an existing venv's `textual` beyond what satisfies
  `requirements.txt` on first creation.

## Implementation

- **`tui_bootstrap.py` is stdlib-only and fully seamed for tests.**
  `ensure_textual(argv, script, *, has_textual, venv_has_textual, run, execv,
  out, environ)` takes injectable seams (default: real `importlib`/`subprocess`/
  `os.execv`), so the missing-`textual` path is unit-testable in the
  dependency-free `tests/` suite without creating a venv or hitting the network.
  Pure helpers: `venv_dir(environ)` (honors `XDG_CACHE_HOME`, else `~/.cache`),
  `venv_python(venv_dir)`, and `find_requirements(start_dir)` (walks up from the
  scripts dir to the repo-root `requirements.txt`). Rejected: putting the
  bootstrap in `dashboard.py` — it must run before the `textual` import and must
  be importable/testable without `textual`, so it belongs in its own stdlib
  module.
- **Provisioning order and reuse.** If the cached venv already has `textual`
  (probe via `venv_python -c "import textual"`), skip install and re-exec
  straight away; otherwise `python -m venv <dir>` then `<venv>/bin/python -m pip
  install -r <requirements>` before the re-exec. Every failed step falls through
  to the hint + `SystemExit(1)`.
- **Entry wiring.** `dashboard.py`: `import tui_bootstrap` at the top; in the
  top `if __name__ == "__main__":` block (added above the `textual` import) call
  `tui_bootstrap.ensure_textual(sys.argv, __file__)`. The existing bottom
  `__main__`/`main()` is unchanged. The module-scope `textual` import drops its
  `sys.exit` and re-raises `ImportError`.

Risk: a corrupted/half-built cached venv could wedge provisioning; guarded by the
`venv_has_textual` probe (a venv failing the probe is rebuilt via the install
path) and the failure fallback to the manual hint.
