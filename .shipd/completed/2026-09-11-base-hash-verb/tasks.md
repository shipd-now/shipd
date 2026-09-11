## 1. The base-hash verb

- [x] 1.1 [P1] [req: base-hash-verb] In `plugins/s/skills/build/tests/test_spec_status.py`, add tests for a `base-hash` verb against a fixture master library: a known capability and requirement id prints that requirement's content hash and exits zero; the printed hash equals `spec_common.content_hash` for the same parsed requirement; an unknown capability and an unknown requirement id each produce one stderr line beginning `Error: ` with a non-zero exit; a missing requirement-id argument prints usage on stderr and exits 2; and a run leaves every file under the content directory byte-identical. Run them and observe them fail — the verb does not exist yet.
- [x] 1.2 [P2] [req: base-hash-verb] In `plugins/s/skills/build/scripts/spec_status.py`, register a `base-hash` subparser taking a `capability` and a `requirement-id` positional, following the registration shape of the neighbouring `check-base` and `config-show` parsers, and list the verb in the module's usage header beside them.
- [x] 1.3 [P3] [req: base-hash-verb] In `plugins/s/skills/build/scripts/spec_status.py`, implement the handler: resolve the capability's master through `spec_merge.master_path` and hash the requirement through `spec_common.content_hash` — the same two primitives `cmd_check_base` uses — print the hash, and exit zero. Report a missing capability or a missing requirement id as one `Error: <reason>` line naming what was not found, with a non-zero exit. Keep it read-only: write no file and change no status. Confirm the tests from task 1.1 pass.

## 2. The emission reference

- [x] 2.1 [P4] [req: base-hash-through-the-engine] In `plugins/s/skills/build/tests/test_prompt_notation.py`, add a test that **executes** the base-hash command documented in `plugins/s/skills/plan/references/emission.md`: extract the command from the reference's base-hash section, run it against a capability and requirement id that exist in this repository's master library, and assert it exits zero and prints exactly `spec_common.content_hash` for that requirement. Do not assert on the command's text alone — a textual match would pass on a command that cannot run, which is the defect being fixed. Run it and observe it fail against the current reference.
- [x] 2.2 [P5] [req: base-hash-through-the-engine] In `plugins/s/skills/plan/references/emission.md`, replace the base-hash section's inline snippet — the one piping `cat verified` into `python3 -` while also feeding it a heredoc, which exits 1 with a `SyntaxError` — with the single documented `base-hash` call, keeping the surrounding prose about which entries need a `base:` line. Leave no inline program in that section. Confirm the test from task 2.1 passes.

## 3. Ship

- [x] 3.1 [P6] [req: *] Bump the version in `plugins/s/.claude-plugin/plugin.json` from `0.6.208` to `0.6.209`.
- [x] 3.2 [P7] [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests` and confirm the whole engine suite passes with the new tests included.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 101 | 32.4k |
| Edit | 9 | 4.3k |
| (no tool) | 0 | 2.2k |
| Read | 13 | 1.9k |
| Agent | 2 | 1.5k |
| **Total** | 125 | 42.3k |
