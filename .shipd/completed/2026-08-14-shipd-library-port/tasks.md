## 1. Run the library port

- [x] 1.1 [req: library-capability-renames] Record the shipd commit to port
      from: run `git -C /Users/mikkelbergmann/projects/shipd rev-parse HEAD`
      and keep the sha for the `--ref` argument and the PR body.
- [x] 1.2 [req: library-capability-renames] In
      `/Users/mikkelbergmann/projects/shipd`, run `python3 tools/port.py apply
      --source /Users/mikkelbergmann/projects/shipd --ref <sha> --dest .
      --include .shipd/ --include .shipd-config.json` and confirm it writes the library.
      The residual scan cannot reach zero on this include set and its exit code is
      **not** the gate: the ported library contains the `shipd-port` capability
      and epic, whose own scenario prose quotes `am` tokens as examples (an
      unmapped `~/.am-designs/`, the negative case `.am-shipd-config.json`, the
      map's `am-<n>` placeholder), so a run that rewrote them would corrupt the
      spec that describes the rename. Instead enumerate the findings with `python3
      tools/port.py verify --dest .shipd` and confirm each is prose rather than a
      path or identifier the ported engine reads — an archived/immutable
      recounting, a self-referential port-spec example, or a map gap member 2
      already recorded (`AM_FLOW_LOG_DIR`, bare `am:<skill>` references). Record
      the finding count and that classification for the PR body. Any finding that
      is a live `.shipd/` path, capability slug, or delta reference is a real
      failure — stop and report it. The binding gates for this member are tasks
      2.x, 3.1, and 3.3.

## 2. Assert the renames

- [x] 2.1 [req: library-capability-renames] List the `am-` prefixed capability
      directory names in shipd at the pinned ref with `git -C
      /Users/mikkelbergmann/projects/shipd ls-tree --name-only <sha>
      .shipd/verified/`, and for each confirm a `shipd-` counterpart exists under
      `/Users/mikkelbergmann/projects/shipd/.shipd/verified/`.
- [x] 2.2 [req: library-capability-renames] Run `find
      /Users/mikkelbergmann/projects/shipd/.shipd -type d -name 'am-*'` and
      confirm it prints nothing.
- [x] 2.3 [req: library-capability-renames] Confirm an unprefixed capability
      carried its name over: check that
      `/Users/mikkelbergmann/projects/shipd/.shipd/verified/statusline/spec.md`
      exists.
- [x] 2.4 [req: library-dropped-trees] Confirm
      `/Users/mikkelbergmann/projects/shipd/openspec` and
      `/Users/mikkelbergmann/projects/shipd/.shipd` do not exist, and that
      `/Users/mikkelbergmann/projects/shipd/.shipd-config.json` exists while
      `/Users/mikkelbergmann/projects/shipd/.shipd-config.json` does not.
- [x] 2.5 [req: library-dropped-trees] Compare the `valid_themes` list in
      `/Users/mikkelbergmann/projects/shipd/.shipd-config.json` against
      `/Users/mikkelbergmann/projects/shipd/.shipd-config.json` and confirm the
      entries match.

## 3. Structural and semantic proof

- [x] 3.1 [req: library-lint-clean] In `/Users/mikkelbergmann/projects/shipd`,
      run `python3 plugins/s/skills/build/scripts/spec_lint.py` with no change
      argument and confirm it exits `0`. Fix any dangling delta path or
      requirement cross-reference it reports, then re-run until clean.
- [x] 3.2 [req: library-metrics-parity] Run the metrics engine over the same
      window in both repositories — `python3
      plugins/s/skills/build/scripts/metrics.py` in
      `/Users/mikkelbergmann/projects/shipd` and `python3
      plugins/s/skills/build/scripts/metrics.py` in
      `/Users/mikkelbergmann/projects/shipd` — and record both outputs.
- [x] 3.3 [req: library-metrics-parity] Compare the archive-derived figures, which
      requires neutralizing the un-ported machine-global build log on **both**
      sides. `metrics.py` unions the `completed/` archive with
      `<log_dir>/builds.jsonl`, which defaults to `~/.shipd/builds` — outside `.shipd/`,
      outside this member's include set, and explicitly *not* migrated per the
      epic's "Personal and machine-level state is not migrated … they start empty;
      telemetry history that matters lives in the repo's `completed/` archive"
      decision. On this machine that log is also shared with unrelated projects, so
      a raw comparison comes out 193 vs 159 and can never reach equality however
      complete the port is. So run both engines against an empty `HOME` —
      `HOME=<empty-dir> python3 plugins/s/skills/build/scripts/metrics.py summary
      --json` in shipd and `HOME=<empty-dir> python3
      plugins/s/skills/build/scripts/metrics.py summary --json` in shipd — and
      confirm `throughput.total` and the `cycle_time` block are equal. Then prove
      it more strongly than the aggregates do, by confirming the two archives'
      directory-name listings are byte-identical (`diff` of `ls .shipd/completed` and
      `ls .shipd/completed`); that, not the totals, is what establishes no archived
      change was lost in transit. Note in the PR body that the cycle-time half of
      the equality is vacuous (both `n=0`) because durations exist only in the
      un-ported log. Record also that `lead_time`/`outcomes` stay non-empty in
      shipd and empty in shipd because `.shipd/autopilot/` is **gitignored** and so
      is untracked at the pinned ref — the epic's "the port reads tracked files
      only" decision — as are `.shipd/video/` and `.shipd/state.json`. A divergence *not*
      explained by those un-ported machine-local sources means an archived change
      genuinely did not cross: identify it, port it, and re-compare.

## 4. Verification

- [x] 4.1 [req: *] In `/Users/mikkelbergmann/projects/shipd`, re-run the four
      ported unittest suites and confirm they still pass with the library present.
- [x] 4.2 [req: *] Commit the ported library in
      `/Users/mikkelbergmann/projects/shipd` on a branch, push it, and open a PR
      whose body records the shipd `--ref` sha from task 1.1 and the metrics
      comparison from task 3.3. Confirm the `ci` workflow's lint steps are now
      green.
