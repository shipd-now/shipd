## 1. Vendor verb — state model and report

- [x] 1.1 [req: vendor-verb] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add failing tests for
      the bare `shipd vendor --root <tmp>` report: an empty repo prints
      `absent` for every managed surface and exits `0`; an owned install at
      the running version prints `installed`; an older vendored
      `plugin.json` version or an extraneous file under
      `<content-dir>/plugin/s/` prints `stale`; a
      `<content-dir>/plugin/s/` without a parseable manifest naming `s`
      prints `foreign`. Build fixtures by invoking the verb itself where
      possible, mutating files for the drift cases.
- [x] 1.2 [req: vendor-verb] In `plugins/s/bin/shipd`, add the vendor state
      model beside the copilot one (`copilot_states`): resolve the content
      dir via `spec_common.resolve_config` (default `.shipd`), define the
      managed surfaces, implement ownership (the vendored copy of the plugin
      manifest — the counterpart of the source
      `plugins/s/.claude-plugin/plugin.json` — parsing with name `s`, version
      as marker) and the `installed`/`stale`/`foreign`/`absent` classification
      including byte-compare drift and extraneous-file detection against
      `PLUGIN_ROOT`, plus the read-only bare report. Make the 1.1 report
      tests pass.

## 2. Vendor verb — add and remove

- [x] 2.1 [req: vendor-verb] In `test_shipd_cli.py`, add failing tests for
      `vendor add`: fresh install writes a byte-identical
      `<content-dir>/plugin/s/` tree (tests included), the marketplace
      manifest (`shipd`, plugin `s`, source `./s`), merged
      `.claude/settings.json` keys (`enabledPlugins."s@shipd"`,
      `extraKnownMarketplaces.shipd` directory source at
      `<content-dir>/plugin` with `autoUpdate: true`, statusline command),
      and the three scaffold dirs with `.gitkeep`; a custom content `dir` in
      `.shipd-config.json` relocates the tree and the settings path;
      repeated `add` is a no-op; a stale install is rewritten and its
      extraneous file pruned; an existing `statusLine` value is preserved;
      a foreign plugin dir refuses with exit `1` and writes nothing, and
      `--force` replaces it.
- [x] 2.2 [req: vendor-verb] In `plugins/s/bin/shipd`, implement
      `vendor add`: per-file atomic writes via the `_copilot_write` pattern,
      full-tree sync to byte equality with pruning, marketplace manifest
      generation, settings merge through the `_read_settings`/
      `_write_settings` pattern aimed at `<root>/.claude/settings.json`
      (statusline only when no `statusLine` key exists), scaffold creation,
      and the foreign refusal with `--force` override. Make the 2.1 tests
      pass.
- [x] 2.3 [req: vendor-verb] In `test_shipd_cli.py`, add failing tests for
      `vendor remove`: an owned install is deleted with the two managed
      settings keys and the vendored-pointing `statusLine` removed, while
      scaffold dirs and a `planned/` change survive; a foreign `statusLine`
      value survives; an absent install exits `0`; a foreign plugin dir
      refuses with exit `1` unless `--force`.
- [x] 2.4 [req: vendor-verb] In `plugins/s/bin/shipd`, implement
      `vendor remove` with the ownership guards and settings-key removal.
      Make the 2.3 tests pass.

## 3. Dispatch wiring

- [x] 3.1 [req: cli-dispatch] In `test_shipd_cli.py`, extend the usage-banner
      test to require `vendor` among the curated verbs, and add a test that
      `shipd vendor` with an unknown mode word exits `2`. Run and observe
      failure.
- [x] 3.2 [req: cli-dispatch] In `plugins/s/bin/shipd`, register `vendor` as
      an in-binary verb beside `copilot` (dispatch, usage banner, argument
      parsing for `add`/`remove`/`--root`/`--force`). Make the 3.1 tests
      pass.

## 4. Context-aware doctor hints

- [x] 4.1 [req: doctor-verb] In `test_shipd_cli.py`, add failing tests: with
      no `requirements.txt` at the doctor root, the `pydantic` and `textual`
      details hint the pinned specifiers (`'pydantic>=2.12,<3'`,
      `'textual>=8.2.8,<9'`) and never `-r requirements.txt`; with a
      `requirements.txt` present, the `-r requirements.txt` hint is
      unchanged, in both the `warn` and declared-pipeline `fail` forms of
      the pydantic check.
- [x] 4.2 [req: doctor-verb] In `plugins/s/bin/shipd`, make
      `check_pydantic` and `check_textual` choose the hint by probing
      `<root>/requirements.txt`, and update the mirror comment in
      `requirements.txt` to name all three sites (requirements.txt, the
      doctor skill's remedy table, the doctor hint fallback). Make the 4.1
      tests pass.

## 5. Docs and release

- [x] 5.1 [req: install-mode-docs] In `README.md`, add the explicitly labeled
      per-repo mode to the installation documentation: `shipd vendor add`,
      the four written surfaces, the registry-free clone-then-trust
      collaborator flow, refresh by re-running `shipd vendor add`, removal
      via `shipd vendor remove`.
- [x] 5.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version to the
      next free patch version (`0.6.125` — main took `0.6.124` in flight).
- [x] 5.3 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) from
      the worktree root and confirm it passes without `textual` or
      `pydantic` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 49 | 21.1k |
| Write | 5 | 8.0k |
| Edit | 10 | 5.6k |
| Read | 26 | 2.7k |
| Agent | 3 | 1.3k |
| (no tool) | 0 | 690 |
| ToolSearch | 2 | 490 |
| **Total** | 95 | 39.8k |
