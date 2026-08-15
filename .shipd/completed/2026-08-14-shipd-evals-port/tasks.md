## 1. Port the harness

- [x] 1.1 [req: evals-fixture-layout] In `/Users/mikkelbergmann/projects/shipd`,
      run `python3 tools/port.py apply --source
      /Users/mikkelbergmann/projects/shipd --ref <sha> --dest . --include
      evals/` using the same shipd sha the earlier ports used, and confirm it
      exits `0` with no residual findings.

## 2. Verify the fixtures

- [x] 2.1 [req: evals-fixture-layout] For each case directory under
      `/Users/mikkelbergmann/projects/shipd/evals/cases/`, confirm its `fixture/`
      holds a `.shipd` directory containing the grammar README and the same
      lifecycle subdirectories the corresponding shipd fixture had at the
      pinned ref.
- [x] 2.2 [req: evals-fixture-layout] Run `find
      /Users/mikkelbergmann/projects/shipd/evals -type d -name '.shipd'` and confirm
      it prints nothing.

## 3. Verify the runner

- [x] 3.1 [req: evals-runner-namespace] In
      `/Users/mikkelbergmann/projects/shipd/evals/run.py`, confirm the headless
      session is launched against a plugin directory ending in `plugins/s` and
      that the skill it drives is `/s:plan`. Correct anything the map missed.
- [x] 3.2 [req: evals-runner-namespace] In
      `/Users/mikkelbergmann/projects/shipd/evals/run.py`, confirm the
      change-discovery globs resolve under the `.shipd` content directory in both
      the scratch root and one level of worktrees, and that the host grammar
      README it copies into each scratch fixture is read from the `.shipd` path.
      Correct anything the map missed.

## 4. Verification

- [x] 4.1 [req: evals-verified-run] In `/Users/mikkelbergmann/projects/shipd`,
      run the harness's own unit suite at
      `/Users/mikkelbergmann/projects/shipd/evals/tests/` and confirm it passes
      with no session launched.
- [x] 4.2 [req: evals-verified-run] In `/Users/mikkelbergmann/projects/shipd`,
      run `python3 evals/run.py` and confirm every case reports a pass rate of 1.0
      and the runner exits `0`. If exactly one case fails, re-run that case with
      `--runs 3` before treating it as a defect, since eval outcomes are
      model-dependent.
- [x] 4.3 [req: *] Confirm the evals are not referenced by
      `/Users/mikkelbergmann/projects/shipd/.github/workflows/ci.yml` — they stay
      local and on demand.
- [x] 4.4 [req: *] Commit the ported harness in
      `/Users/mikkelbergmann/projects/shipd` on a branch, push, and open a PR
      recording the live-run result from task 4.2.
