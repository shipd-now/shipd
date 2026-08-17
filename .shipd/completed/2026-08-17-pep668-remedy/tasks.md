## 1. PEP 668-aware hint composition

- [x] 1.1 [req: doctor-verb] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add failing tests
      for the hint forms with the marker probe injected both ways: marker
      present + `requirements.txt` at root →
      `pip install --user --break-system-packages -r requirements.txt`;
      marker present + no `requirements.txt` → the flagged pinned specifier
      (both packages); marker absent → today's two unflagged forms,
      byte-identical, in the `warn` and escalated `fail pydantic` details
      alike.
- [x] 1.2 [req: doctor-verb] In `plugins/s/bin/shipd`, add a read-only
      externally-managed probe (`os.path.isfile` of the
      `EXTERNALLY-MANAGED` marker under `sysconfig.get_path("stdlib")`),
      injectable in the `check_pydantic(root, find_spec=…)` style, and make
      `_install_hint` prepend `--user --break-system-packages` to either
      hint form when it reports managed. Make the 1.1 tests pass.

## 2. Remedy relay in the doctor skill

- [x] 2.1 [req: doctor-remedy-boundaries] In
      `plugins/s/skills/doctor/SKILL.md`, rewrite the remedy table's
      `textual` and `pydantic` rows to run `python3 -m ` followed by the
      `pip install` command the finding's own detail names, and add the
      dialog rule that an option whose command carries
      `--break-system-packages` states that flag; keep every other row and
      the one-remedy-round contract unchanged. (Docs-only surface — no
      runtime test.)

## 3. Release

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version to
      the next free patch version (`0.6.129` at planning time; take the
      next free one if main moved).
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) from
      the worktree root and confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 79 | 32.1k |
| Edit | 15 | 11.7k |
| (no tool) | 0 | 8.3k |
| Write | 2 | 2.9k |
| Read | 14 | 1.9k |
| Agent | 2 | 1.1k |
| SendMessage | 1 | 951 |
| **Total** | 113 | 58.9k |
