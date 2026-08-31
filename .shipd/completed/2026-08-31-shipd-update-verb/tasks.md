## 1. Tests first

- [x] 1.1 [req: cli-dispatch, cli-update] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add `"update"` to the
      module-level `VERBS` tuple. Run the file and observe the banner
      assertions fail — the binary does not name `update` yet.
- [x] 1.2 [req: cli-update] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add a
      `ShipdUpdateVerbTests` class exercising `shipd.cmd_update` in process
      (the style the doctor-check tests use: a temp `HOME`, a fabricated cache
      root via `SHIPD_PLUGIN_CACHE`, a fabricated
      `known_marketplaces.json` + marketplace tree, and a stub patched over
      `shipd._claude_run`), covering: a newer published version being applied
      (`claude plugin update s@shipd` invoked; stdout names the old and new
      versions and the start-a-new-session note; exit 0); `--check` reporting
      the pending update and invoking no apply (exit 0); an already-current
      cache reporting the newest published version and invoking no apply
      (exit 0); `0.6.10` beating `0.6.9` in the installed-version resolution;
      an unregistered `shipd` marketplace erroring with
      `claude plugin marketplace add shipd-now/shipd` (exit 1); a nonzero
      marketplace refresh erroring without reporting any comparison (exit 1);
      an empty cache root erroring with `claude plugin install s@shipd`
      (exit 1); and a nonzero apply erroring (exit 1). Run the file and observe
      the class fail — `cmd_update` does not exist yet.

## 2. The update verb

- [x] 2.1 [req: cli-update] In `plugins/s/bin/shipd`, add the module-level
      constants `CLAUDE_MARKETPLACE = "shipd"`, `CLAUDE_PLUGIN_ID = "s@shipd"`,
      `CLAUDE_PLUGIN_NAME = "s"`, `MARKETPLACE_TIMEOUT = 120`, an
      `UpdateError(Exception)` whose message is the `Error:` reason, and the
      helpers `_plugins_home()`, `_cache_root()`, `newest_installed(cache_root)`,
      `marketplace_location(plugins_home)`, `marketplace_version(location)`, and
      the subprocess seam `_claude_run(args, timeout=None)` — exactly the
      signatures and resolution rules `plan.md`'s `## Implementation` section
      records. Reuse the existing `VERSION_DIR_RE`, `_version_key`, and
      `_subdirs` helpers for the installed-version resolution; keep everything
      stdlib-only.
- [x] 2.2 [req: cli-dispatch, cli-update] In `plugins/s/bin/shipd`, add
      `cmd_update(args)` — argparse over the single `--check` flag, the
      compare/apply flow and the exact report lines and error lines from
      `plan.md`'s `## Implementation` section — dispatch it from `main` in the
      in-binary block alongside `install` (never through `VERB_TABLE`), and add
      an `update [--check]` line to the `USAGE` banner's verb list.
- [x] 2.3 [req: cli-update] Run
      `python3 plugins/s/skills/build/tests/test_shipd_cli.py` and confirm the
      whole file passes, including the tests added in tasks 1.1 and 1.2.

## 3. Documentation and release

- [x] 3.1 [P1] [req: install-mode-docs] In `README.md`, document `shipd update`
      as the one-command manual upgrade in the install-mode auto-update
      paragraph that currently ends with the `claude plugin update s@shipd`
      fallback (naming `shipd update --check` as the report-only form and
      keeping the existing `claude plugin update s@shipd` fallback), and add a
      `shipd update [--check]` line to the `shipd` CLI verb listing under
      `## The shipd CLI`.
- [x] 3.2 [P1] [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.163` to `0.6.165`
      (`0.6.164` is claimed by a change in flight elsewhere).
- [x] 3.3 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests -t .` from
      the repo root, or the project's documented equivalent) and confirm it
      passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 87 | 29.0k |
| (no tool) | 0 | 6.6k |
| Agent | 1 | 262 |
| Read | 5 | 4 |
| **Total** | 93 | 35.9k |
