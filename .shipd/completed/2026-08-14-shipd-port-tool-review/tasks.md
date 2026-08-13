## 1. Restate the four requirements

- [x] 1.1 [req: port-source-ref] In the change's delta spec, restate
      `port-source-ref` so it requires enumeration from the tree at `--ref`
      rather than the index, forbids porting staged-but-uncommitted files, and
      requires a failed run to leave the destination untouched. Add the three
      scenarios: a staged addition is not ported, an earlier ref ports that
      ref's tree, a failed run writes nothing.
- [x] 1.2 [req: port-apply-scope] Restate `port-apply-scope` so it requires each
      file's git-recorded executable bit to survive the port, and add the
      scenario contrasting a `100755` source file with a `100644` one.
- [x] 1.3 [req: port-verbs] Add two scenarios to `port-verbs`: a `--source`
      below the repository root exits `1`, and `verify` on a missing `--dest`
      exits `1` rather than reporting a clean scan.
- [x] 1.4 [req: port-include-filter] Restate `port-include-filter` so `--include`
      matches paths equal to or lying under a prefix on whole path segments, and
      add the scenario for the `plugins/am` versus `plugins/amx` sibling.
- [x] 1.5 [req: port-residual-scan] Restate `port-residual-scan` so text files
      are written as UTF-8 rather than in the ambient locale's encoding, and add
      the scenario for non-ASCII content under `LC_ALL=C`.

## 2. Verification

- [x] 2.1 [req: *] Run `spec_lint.py` and confirm the master library is valid
      after the merge, with every `base:` hash resolving.
- [x] 2.2 [req: *] Confirm each added scenario has a passing test in the shipd
      suite: run `python3 -m unittest discover -s tools/tests` in
      `shipd-now/shipd` at commit `9953976` and confirm 25 tests pass.
- [x] 2.2b [req: port-verbs] Confirm `port-verbs`' `--dest` clause matches the
      implementation both ways: `verify --dest <missing>` exits `1`, and
      `apply --dest <missing nested path>` exits `0` having created it.
- [x] 2.3 [req: *] Confirm `.shipd/completed/2026-08-13-shipd-port-tool/` is
      untouched by this change: `git diff --stat main -- .shipd/completed/` reports
      only this change's own archived directory.
