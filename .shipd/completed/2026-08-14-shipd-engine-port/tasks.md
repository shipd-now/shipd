## 1. Run the port

- [x] 1.1 [req: engine-namespace-constants] Record the shipd commit to port
      from: run `git -C /Users/mikkelbergmann/projects/shipd rev-parse
      origin/main` and keep the sha for the `--ref` argument and the PR body.
      `origin/main` rather than the main checkout's `HEAD`, which lags behind the
      remote tip.
- [x] 1.2 [req: engine-namespace-constants] In
      `/Users/mikkelbergmann/projects/shipd`, run `python3 tools/port.py apply
      --source /Users/mikkelbergmann/projects/shipd --ref <sha> --dest .
      --include plugins/s/ --include requirements.txt` and confirm it writes the
      tree. Enumerate its residual findings under `plugins/s/` and confirm each
      falls outside this member's constants table (they are map gaps in member 1's
      tool, reported not fixed — see plan.md); the binding no-residual gate is
      task 2.5's four-pattern check, not this command's exit code.

## 2. Verify the constants

- [x] 2.1 [req: engine-namespace-constants] In
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/build/scripts/spec_common.py`,
      confirm `CONFIG_FILENAME` is `.shipd-config.json`, `DEFAULT_DIR` is
      `.shipd`, and `DEFAULT_MEMORY_DIR` is `~/.shipd-memory`. Correct any value
      the map missed.
- [x] 2.2 [req: engine-namespace-constants] In
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/build/scripts/metrics.py`
      and
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/build/scripts/build_report.py`,
      confirm the default build log dir is `~/.shipd/builds` in both. Correct any
      value the map missed.
- [x] 2.3 [req: engine-namespace-constants] In
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/build/scripts/tui_bootstrap.py`,
      confirm the venv cache path ends with a shipd directory containing tui-venv; and in
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/build/scripts/worktree.sh`,
      confirm the idle-window variable is `SHIPD_WORKTREE_IDLE_MINUTES`.
- [x] 2.4 [req: engine-namespace-constants] In
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/review/scripts/semdiff.py`,
      confirm the content-directory cohort literal is `.shipd`.
- [x] 2.5 [req: engine-namespace-constants] Run `grep -rn
      '\.shipd-config\.json\|~/\.shipd-memory\|~/\.shipd/builds\|SHIPD_WORKTREE_IDLE_MINUTES'`
      over `/Users/mikkelbergmann/projects/shipd/plugins/s/` and confirm there is
      no match.

## 3. CI workflow

- [x] 3.1 [req: engine-ci-workflow] Create
      `/Users/mikkelbergmann/projects/shipd/.github/workflows/ci.yml` modeled on
      shipd's, with a job named `ci`. Inside the workflow every path is
      **repo-relative**, never absolute: the four unittest suites are discovered
      at plugins/s/skills/build/tests, plugins/s/skills/build/tests_textual,
      plugins/s/skills/review/tests, and plugins/s/skills/video-ingest/tests.
      Add the master-library lint and the `.shipd/planned/*/` lint loop, plus the
      `bash -n` shell syntax checks against the ported `statusline.sh`,
      `claim_task.sh`, and `worktree.sh`.
- [x] 3.2 [req: engine-ci-workflow] Check every `discover -s` path and every
      script path named in
      `/Users/mikkelbergmann/projects/shipd/.github/workflows/ci.yml` against the
      shipd tree and confirm each exists.

## 4. Verification

- [x] 4.1 [req: engine-suites-green] Resolve the `.shipd`/`.am` → `.shipd`
      collision in
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/build/tests/test_build_report.py`:
      rename `test_no_shipd_path_read_or_written` to
      `test_no_am_path_read_or_written` and assert that after `write_log_entry`
      neither `~/.am` nor `~/.shipd` exists under the isolated `$HOME`. Correct
      the two docstrings stating the same invariant — `BuildConfigTest`'s class
      docstring in that file and `write_log_entry`'s in
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/build/scripts/build_report.py`
      — to read "never `~/.shipd/` or `~/.shipd/`". Also correct the `.am`
      docstring reference in
      `/Users/mikkelbergmann/projects/shipd/plugins/s/skills/review/scripts/semdiff.py`
      to `.shipd`, so it matches the cohort literal task 2.4 verified.
- [x] 4.2 [req: engine-suites-green] In `/Users/mikkelbergmann/projects/shipd`,
      run `python3 -m pip install -r requirements.txt`, then run each of the four
      suites with `python3 -m unittest discover -s <path> -v` and confirm all four
      report no failures and no errors.
- [x] 4.3 [req: *] Commit the ported tree in
      `/Users/mikkelbergmann/projects/shipd` on branch `change/shipd-engine-port`,
      whose commit message records the shipd `--ref` sha from task 1.1 and
      notes that the two lint steps stay red until the library port lands, and
      push it. Then attempt `gh pr create`; the `gh` CLI here authenticates as an
      account without access to `shipd-now/shipd`, so a 404/auth failure is an
      expected outcome to report back, not a task failure — the pushed branch is
      the deliverable and the PR is opened by a human.
