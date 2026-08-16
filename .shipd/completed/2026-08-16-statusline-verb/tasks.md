## 1. Statusline verb

- [x] 1.1 [req: statusline-verb] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add in-process tests
      for the new verb against temp `--settings` paths (the doctor-checks
      injection style): install creates a fresh settings file with the
      `statusLine` entry; unrelated keys survive a rewrite; a differing
      existing registration refuses with exit 1 without `--force` and
      replaces with it; a second identical install is idempotent; checkout
      mode registers the absolute `plugins/s/integrations/statusline.sh`
      path;
      snapshot mode registers a `sort -V` newest-snapshot command; the bare
      verb mutates nothing; malformed JSON refuses without writing. Run and
      observe them fail.
- [x] 1.2 [req: statusline-verb] In `plugins/s/bin/shipd`, implement the
      verb: a `statusline_command(plugin_root)` helper choosing the
      checkout path or the snapshot-resolving command via the existing
      `VERSION_DIR_RE` dev/cache detection, and `cmd_statusline(args)` with
      the bare read-only report and `install [--force] [--settings PATH]`
      writing via same-directory temp file + `os.replace`. Make 1.1 pass.
- [x] 1.3 [req: cli-dispatch] Wire `statusline` into the binary's dispatch
      and usage banner, note the mutating-verb exception in the module
      docstring, and extend the banner/dispatch tests (the `VERBS` tuple in
      `test_shipd_cli.py`) to include it.

## 2. Doctor check

- [x] 2.1 [req: doctor-verb] In `test_shipd_cli.py`, add tests for
      `check_statusline` with an injected settings path: no file or no
      `statusLine` key → `warn` naming `shipd statusline install`; a
      registered command → `ok`; unparseable JSON → `warn`. Run and observe
      them fail.
- [x] 2.2 [req: doctor-verb] In `plugins/s/bin/shipd`, implement
      `check_statusline(settings_path=None)` (read-only, defaulting to
      `~/.claude/settings.json`) and append it to `default_checks`. Make
      2.1 pass.

## 3. Skill and docs

- [x] 3.1 [req: doctor-remedy-boundaries] In
      `plugins/s/skills/doctor/SKILL.md`, add the `statusline` row to the
      remedy table: a `warn statusline` finding proposes the consent-gated
      `shipd statusline install`, run with the binary resolved as the
      preflight was.
- [x] 3.2 [req: statusline-verb] In `README.md` (Statusline section) and
      `docs/getting-started.md` (section 1), lead the registration with
      `shipd statusline install`, keeping the existing manual
      `settings.json` snippets as the fallback path.
- [x] 3.3 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` (patch bump; the plugin cache
      snapshot is keyed by it).
- [x] 3.4 [req: statusline-verb] In `docs/quickstart.md`: update section 2's
      doctor check list to the full current set (`python`, `git`, `config`,
      `gh`, `textual`, `pydantic`, `snapshot`, `statusline`) and note that a
      `warn statusline` line is fixed with one command, `shipd statusline
      install`; in section 6, add a short pointer that `shipd statusline
      install` registers the ☕ statusline so the change's status and task
      progress stay visible in every session, linking
      `getting-started.md` for what the line shows.

## 4. Verify

- [x] 4.1 [req: *] Run the engine suite
      (`python3 -m unittest discover plugins/s/skills/build/tests`) and
      confirm it passes — including without `textual`/`pydantic`
      importable, per the constitution; then run `shipd statusline`,
      `shipd statusline install --settings <temp>`, and `shipd doctor` end
      to end, observing the report, the written entry, and the
      `statusline` check line.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 82 | 26.5k |
| Edit | 26 | 24.1k |
| (no tool) | 0 | 6.4k |
| Read | 20 | 2.6k |
| Agent | 3 | 2.0k |
| ScheduleWakeup | 1 | 352 |
| **Total** | 132 | 61.9k |
