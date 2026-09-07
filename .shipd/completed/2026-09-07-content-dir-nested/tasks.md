## 1. Nested `dir` validation in the engine

- [x] 1.1 [req: content-dir-key] In
      `plugins/s/skills/build/tests/test_spec_common.py`, replace
      `test_separator_in_dir_errors_naming_value` (nested values become valid)
      with tests asserting: `specs_dirname({"dir": ".agents/specs/.shipd"})`
      returns the value unchanged; `specs_dir` resolves a nested-dir config to
      `<root>/.agents/specs/.shipd`; and `ConfigError` naming the value is
      raised for `"../specs"`, `"/abs/specs"`, `"a//b"`, `"./x"`, `"a\\b"`,
      `""`, and a non-string. Run the file and observe the new tests fail.
- [x] 1.2 [req: content-dir-key] In
      `plugins/s/skills/build/scripts/spec_common.py`, relax `specs_dirname`
      to accept `/`-separated relative paths (rejecting non-string/empty
      values, absolute paths, backslashes, and empty/`.`/`..` components, each
      with a `ConfigError` naming the value), and change `specs_dir`'s in-repo
      branch to `os.path.join(root, *name.split("/"))`. Update both
      docstrings. Confirm
      `plugins/s/skills/build/tests/test_spec_common.py` now passes.

## 2. Worktree remove guard honors the configured directory

- [x] 2.1 [req: worktree-guard-content-dir] In
      `plugins/s/skills/build/tests/test_worktree.py`, add tests: a worktree
      whose `.shipd-config.json` declares `dir: ".agents/specs/.shipd"` and
      which carries an unshipped change under
      `.agents/specs/.shipd/planned/<change>/` refuses `remove` with exit 2
      listing the unshipped-change reason naming that directory; and a
      worktree with malformed `.shipd-config.json` plus an unshipped change
      under `.shipd/planned/` still refuses with exit 2 (fallback). Run the
      file and observe the new tests fail.
- [x] 2.2 [req: worktree-guard-content-dir] In
      `plugins/s/skills/build/scripts/worktree.sh`, in the `remove` guard
      (the `planned="$WORKTREE/.shipd/planned"` block), resolve the content
      directory once via
      `python3 "<script-dir>/spec_status.py" --root "$WORKTREE" config-show`
      piped to `sed -n 's/^content-dir: //p'`, falling back to `.shipd` when
      the command fails or prints nothing; use the resolved name in the
      `planned` path and in the refusal reason text. Confirm
      `plugins/s/skills/build/tests/test_worktree.py` now passes.

## 3. Ship hygiene

- [x] 3.1 [req: *] Run the full engine suite without `textual` installed —
      `python3 -m unittest discover plugins/s/skills/build/tests` — and
      confirm it passes; bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to `0.6.185`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 126 | 11.4k |
| (no tool) | 0 | 622 |
| SendMessage | 1 | 510 |
| Agent | 1 | 259 |
| Edit | 10 | 87 |
| Read | 8 | 71 |
| ToolSearch | 2 | 25 |
| Write | 2 | 16 |
| **Total** | 150 | 13.0k |
