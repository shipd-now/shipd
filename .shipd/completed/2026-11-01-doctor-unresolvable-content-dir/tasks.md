## 1. Verify the shipped behavior against the delta

- [x] 1.1 [req: doctor-schema-check, doctor-local-state-check] Run
      `python3 -B -m unittest plugins/s/skills/build/tests/test_shipd_cli.py -k invalid_dir`
      from the repo root and confirm it reports `Ran 2 tests` and `OK`. The
      tests are `test_schema_invalid_dir_is_ok_carrying_the_error` and
      `test_local_state_invalid_dir_is_ok_carrying_the_error`. Edit no file.
- [x] 1.2 [req: doctor-schema-check, doctor-local-state-check] In a fresh
      temporary directory, run `git init -q`, write `{"dir": "../specs"}` to
      `.shipd-config.json`, and run `python3 -B <repo-root>/plugins/s/bin/shipd doctor`.
      Confirm the `schema` and `local-state` lines begin `ok` and name
      `../specs` and `skipped`, only `config` fails, and the last line is
      `doctor: 1 problem(s)`. Delete the temporary directory. Edit no file.
- [x] 1.3 [req: doctor-schema-check] Run
      `python3 -B -m unittest plugins/s/skills/build/tests/test_shipd_cli.py -k malformed_marker`
      and confirm it reports `OK`, so a garbled marker still fails. Edit no
      file.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 14 | 3.9k |
| SubagentHandback | 2 | 1.5k |
| Agent | 2 | 724 |
| (no tool) | 0 | 189 |
| **Total** | 18 | 6.2k |
