## 1. Fall back to the current selection

- [x] 1.1 [req: locate-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, change the `locate`
      subparser's `change` argument to `nargs="?", default=None`, matching
      `show`/`status`/`validate`/`set-status`/`sync`/`check-base`.
- [x] 1.2 [req: locate-verb] In `cmd_locate` in the same file, resolve the
      argument through `_resolve_change(root, change)` as the first
      statement, and update the docstring to state the fallback.
- [x] 1.3 [req: locate-verb] Add tests to
      `plugins/s/skills/build/tests/test_spec_status.py`'s `LocateTest`
      covering the fallback (a change is selected via `use` and `locate`
      runs with no argument) and the error path (no argument, no
      selection).
- [x] 1.4 [req: locate-verb] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm it is green.
