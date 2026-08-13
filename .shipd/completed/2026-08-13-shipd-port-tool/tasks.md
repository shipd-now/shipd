## 1. Scaffold and test harness

- [x] 1.1 [req: port-verbs] In the shipd repo, create
      `/Users/mikkelbergmann/projects/shipd/tools/` and
      `/Users/mikkelbergmann/projects/shipd/tools/tests/`, then add
      `/Users/mikkelbergmann/projects/shipd/tools/tests/test_port.py` as an empty `unittest` module with a helper that
      builds a synthetic source git repo in a `tempfile.TemporaryDirectory` (init,
      write files, `git add`, `git commit`) and returns its path. No test bodies
      yet.

## 2. Verbs, exit codes, and source reading

- [x] 2.1 [req: port-verbs] In `/Users/mikkelbergmann/projects/shipd/tools/tests/test_port.py`, add tests asserting
      `plan` writes nothing to the destination, and that a `--source` that is not
      a git repo prints `Error: ` on stderr and exits `1`. Run them and observe
      they fail — `/Users/mikkelbergmann/projects/shipd/tools/port.py` does not exist yet.
- [x] 2.2 [req: port-verbs] Create `/Users/mikkelbergmann/projects/shipd/tools/port.py` (stdlib only) with an
      `argparse` sub-parser layout exposing `plan`, `apply`, and `verify`;
      `plan`/`apply` take `--source`, `--ref` (default `HEAD`), and `--dest`,
      `verify` takes `--dest`. Wire `main()` to return `0`/`1`/`2` and
      `sys.exit(main())`. Raise a module-level error type printed as
      `Error: <message>` on stderr with exit `1`.
- [x] 2.3 [req: port-source-ref] In `/Users/mikkelbergmann/projects/shipd/tools/tests/test_port.py`, add tests
      asserting a tracked file modified but uncommitted in the source ports at its
      committed content, and that an untracked source file produces no
      destination counterpart. Run and observe failure.
- [x] 2.4 [req: port-source-ref] In `/Users/mikkelbergmann/projects/shipd/tools/port.py`, implement source enumeration
      via `git -C <source> ls-files --with-tree=<ref>` and content reads via
      `git -C <source> show <ref>:<path>`, both through `subprocess.run` with
      `check=True`. Confirm 2.3's tests pass.

## 3. The maps

- [x] 3.1 [req: port-capability-enum] In `/Users/mikkelbergmann/projects/shipd/tools/tests/test_port.py`, add tests
      asserting an enumerated slug (`shipd-plan`, present under `.shipd/verified/`) is
      renamed in content and on disk while a non-enumerated `am-widget` is left
      alone. Run and observe failure.
- [x] 3.2 [req: port-capability-enum] In `/Users/mikkelbergmann/projects/shipd/tools/port.py`, add a function that
      lists `.shipd/verified/` at the ref and returns the directory names matching
      `am-<name>`; build the per-slug rename rules from that list, word-bounded.
      Confirm 3.1's tests pass.
- [x] 3.3 [req: port-token-map] In `/Users/mikkelbergmann/projects/shipd/tools/tests/test_port.py`, add tests
      asserting: `.shipd-config.json` becomes `.shipd-config.json` with no doubled or
      partial rewrite; `ambiguous`/`stream`/`param` are untouched; and `/s:plan`,
      `s:oracle`, `plugins/s/x.py`, `s@shipd`, `~/.shipd-memory` map to their
      `s`/`shipd` forms. Run and observe failure.
- [x] 3.3b [req: port-token-map] In
      `/Users/mikkelbergmann/projects/shipd/tools/tests/test_port.py`, add tests
      asserting a bare quoted content-directory segment is rewritten — a source
      line assigning the quoted `.am` to a constant, and one passing it as a
      middle argument to a path join, both become the quoted `.shipd` — while a
      quoted `.shipd-config.json` and the word `.among` are left alone. Run and
      observe failure.
- [x] 3.4 [req: port-token-map] In `/Users/mikkelbergmann/projects/shipd/tools/port.py`, add the ordered token rule
      list exactly as enumerated in `plan.md`'s `## Implementation` (rules 1–13,
      capability slugs slotting in at position 10 and the quoted-segment rule at
      position 11), applied in order with no rule matching a bare `am`. Confirm
      3.3's and 3.3b's tests pass.
- [x] 3.5 [req: port-apply-scope] In `/Users/mikkelbergmann/projects/shipd/tools/tests/test_port.py`, add tests
      asserting a pre-existing destination `LICENSE` survives `apply`, and that
      source paths under `openspec/` and `.shipd/` produce no destination
      counterpart. Run and observe failure.
- [x] 3.6 [req: port-apply-scope] In `/Users/mikkelbergmann/projects/shipd/tools/port.py`, add the path map
      (`plugins/s/`→`plugins/s/`, `.shipd/`→`.shipd/`,
      `.shipd-config.json`→`.shipd-config.json`, plus the capability-dir renames
      under `verified/` and `completed/*/specs/`) and the `openspec/` /
      `.shipd/` exclusion; make `apply` write only mapped destinations.
      Confirm 3.5's tests pass.

- [x] 3.7 [req: port-include-filter] In
      `/Users/mikkelbergmann/projects/shipd/tools/tests/test_port.py`, add tests
      asserting `--include plugins/s/` writes the ported plugin tree and no
      `.shipd/verified/` path; that two `--include` values union; and that no
      `--include` ports everything non-excluded. Run and observe failure.
- [x] 3.8 [req: port-include-filter] In
      `/Users/mikkelbergmann/projects/shipd/tools/port.py`, add a repeatable
      `--include <prefix>` option to `plan` and `apply` that filters source paths
      by prefix (whole tree when absent), and scope the residual scan to the files
      the run wrote. Confirm 3.7's tests pass.

## 4. Residual scan

- [x] 4.1 [req: port-residual-scan] In `/Users/mikkelbergmann/projects/shipd/tools/tests/test_port.py`, add tests
      asserting an unmapped anchored form (`~/.am-designs/`) is reported as
      `<path>:<line>: <match>` with exit `2`; a fully mapped tree exits `0`; and a
      non-UTF-8 source file is copied byte-identically and produces no finding.
      Run and observe failure.
- [x] 4.2 [req: port-residual-scan] In `/Users/mikkelbergmann/projects/shipd/tools/port.py`, implement the post-write
      scan over written text files for residual `shipd` and anchored `am`
      forms, reporting `<path>:<line>: <match>` and returning `2` on any finding;
      detect non-UTF-8 files by a failed `bytes.decode("utf-8")` and copy those
      byte-for-byte, excluding them from substitution and from the scan. Confirm
      4.1's tests pass.
- [x] 4.3 [req: port-residual-scan] In `/Users/mikkelbergmann/projects/shipd/tools/port.py`, make the `verify` verb
      run that same scan against an existing `--dest` with no source involved, and
      confirm it reports and exits identically.

## 5. Verification

- [x] 5.1 [req: *] Run `python3 -m unittest discover -s tools/tests -v` in the
      shipd repo and confirm every test passes.
- [x] 5.2 [req: *] Confirm `/Users/mikkelbergmann/projects/shipd/tools/port.py` imports no third-party module: run
      `python3 -c "import ast,sys; ..."` or inspect every `import` statement, and
      confirm each names a Python 3 standard-library module.
- [x] 5.3 [req: *] Run `python3 tools/port.py plan --source
      /Users/mikkelbergmann/projects/shipd --ref HEAD --dest .` in the shipd
      repo and confirm it prints a plan, writes nothing, and exits `0`.
