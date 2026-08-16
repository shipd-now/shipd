## 1. Status CLI JSON

- [x] 1.1 [req: json-output] Add failing tests in
      `plugins/s/skills/build/tests/test_spec_status.py`: `status --json`
      (change and epic-fallback kinds), `show --json` (change with and
      without a checklist, epic fallback, bare workspace report),
      `epic-show --json` (lanes, member fields, worktree name for a
      worktree-hosted epic), `locate --json` (array with root and worktree
      rows), `workspace-show --json`, and byte-identical text output
      without the flag.
- [x] 1.2 [req: json-output] Implement the flag in
      `plugins/s/skills/build/scripts/spec_status.py`: each of the five
      verbs computes its existing data, then renders text or
      `json.dumps` from the same values; argparse gains `--json` on
      exactly those five subparsers. Run the 1.1 tests green.

## 2. shipd list JSON

- [x] 2.1 [req: list-json] Add failing tests in
      `plugins/s/skills/build/tests/test_shipd_cli.py`: `list --json` rows
      (including `--all` archived rows), the empty-array case, and
      `--json` passthrough on a delegated verb.
- [x] 2.2 [req: list-json] Implement `--json` in `cmd_list` in
      `plugins/s/bin/shipd`. Run the 2.1 tests green.

## 3. Lint JSON

- [x] 3.1 [req: lint-json] Add failing tests in
      `plugins/s/skills/build/tests/test_spec_lint.py`: clean-library
      object shape and exit 0; a structural finding in `errors` with the
      flagless exit code; warnings carried in `warnings`.
- [x] 3.2 [req: lint-json] Implement `--json` in
      `plugins/s/skills/build/scripts/spec_lint.py`, rendering the same
      finding strings the text mode prints. Run the 3.1 tests green.

## 4. Ship

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 4.2 [req: *] Run `plugins/s/skills/build/tests/` (no `textual`) and
      `plugins/s/skills/build/tests_textual/`; both green.
