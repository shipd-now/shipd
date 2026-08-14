## 1. Dispatcher

- [x] 1.1 [req: cli-dispatch] Add
      `plugins/s/skills/build/tests/test_shipd_cli.py` with subprocess tests
      for the dispatcher: `shipd frobnicate` exits 2 with a usage banner on
      stderr; `shipd --help` exits 0 with the banner on stdout;
      `shipd locate no-such-change` (cwd: a temp repo with a `.shipd/`
      layout) exits 1 with `Error: change 'no-such-change' not found` on
      stderr; `shipd board --root <temp repo>` exits 0. Run the file and
      observe every test fail — the binary does not exist yet.
- [x] 1.2 [req: cli-dispatch] Create the executable `plugins/s/bin/shipd`
      (shebang `#!/usr/bin/env python3`, `chmod +x`, stdlib-only, no `.py`
      suffix): resolve `SCRIPTS = Path(__file__).resolve().parent.parent /
      "skills/build/scripts"`; define the verb table from plan.md's
      Implementation (status→`spec_status.py show`, locate→`spec_status.py
      locate`, epic→`spec_status.py epic-show`, workspace→`spec_status.py
      workspace-show`, board→`dashboard.py board`, tui→`dashboard.py tui`,
      metrics→`metrics.py` with bare `metrics` becoming `metrics.py summary`,
      lint→`spec_lint.py`); dispatch via
      `os.execv(sys.executable, [sys.executable, str(script), *mapped])`;
      unknown/missing verb prints the usage banner to stderr and exits 2;
      `help`/`-h`/`--help` prints it to stdout and exits 0. Confirm the 1.1
      dispatcher tests pass.

## 2. list

- [x] 2.1 [req: cli-list] Extend
      `plugins/s/skills/build/tests/test_shipd_cli.py` with `list` tests over
      a temp repo fixture: a worktree change `foo` (`.worktrees/foo/.shipd/
      planned/foo/plan.md`, `Status: ready`) is printed with `worktree:foo`
      and `ready`; a `foo` present in both root `planned/` and the worktree
      yields one line with location `worktree:foo`; a `completed/` entry
      appears only with `--all`, as `archived`; an empty repo prints
      `no changes in flight` with exit 0. Run and observe them fail.
- [x] 2.2 [req: cli-list] Implement `list` inside `plugins/s/bin/shipd`:
      `sys.path.insert(0, str(SCRIPTS))`, import `spec_common` and
      `spec_status`; resolve the content dir via `spec_common.specs_dir`-side
      config (`spec_common.resolve_config`); collect changes from the root's
      `planned/` then each `.worktrees/<name>`'s `planned/` (skipping
      worktrees without one), reading each status with
      `spec_status.read_status(<location root>, <change>)`; dedupe by name
      with the worktree occurrence winning; support `--root` (default cwd)
      and `--all` (append `completed/` entries as `archived`); print
      `no changes in flight` when nothing is in flight. Confirm the 2.1
      tests pass.

## 3. Version, bump, docs

- [x] 3.1 [req: cli-version] Extend
      `plugins/s/skills/build/tests/test_shipd_cli.py`: `shipd --version`
      prints the `version` from `plugins/s/.claude-plugin/plugin.json` and
      exits 0. Run and observe it fail.
- [x] 3.2 [req: cli-version] Implement `--version` in `plugins/s/bin/shipd`:
      read `version` from `Path(__file__).resolve().parent.parent /
      ".claude-plugin/plugin.json"`; on a missing/unreadable manifest print
      `Error: <reason>` to stderr and exit 1. Confirm the 3.1 test passes.
- [x] 3.3 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.96` to `0.6.97`.
- [x] 3.4 [req: *] Add a short "Put `shipd` on your PATH" note to
      `README.md`: symlink `plugins/s/bin/shipd` from the repo checkout into
      a PATH dir (e.g. `ln -s "$PWD/plugins/s/bin/shipd" ~/bin/shipd`), and
      never symlink into the versioned plugin cache
      (`~/.claude/plugins/cache/…`), which breaks on every version bump.
- [x] 3.5 [req: *] Run the full engine suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual` installed and confirm
      it passes.
