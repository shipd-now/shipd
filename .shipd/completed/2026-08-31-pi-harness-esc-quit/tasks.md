## 1. Pi registry entry

- [x] 1.1 [req: registry-data] In
      `plugins/s/skills/build/tests/test_harness_registry.py`, add a
      `test_pi_paths` method to `ResearchedPathsTest` (beside
      `test_opencode_paths`) asserting `hr.get("pi")` has `repo_pattern`
      `.pi/prompts/shipd-{command}.md`, `user_dir` `~/.pi/agent/prompts/`,
      `dialect` `yaml`, `frontmatter` `("description", "argument-hint")`,
      and `features` `("file-references",)`. In the same class add a
      `test_pi_and_oh_my_pi_are_separate` method asserting both ids are in
      `hr.ids()` and their `repo_pattern` values differ. Run the file with
      `python3 -m unittest` and observe both new tests fail — the entry does
      not exist yet.
- [x] 1.2 [req: registry-data] In
      `plugins/s/skills/build/scripts/harness_registry.py`, append a `pi`
      entry after `opencode` in `HARNESSES`: id `pi`, name `Pi`,
      `repo_pattern` `.pi/prompts/shipd-{command}.md`, `user_dir`
      `~/.pi/agent/prompts/`, dialect `yaml`, frontmatter
      `("description", "argument-hint")`, features `("file-references",)`.
      Confirm `test_harness_registry.py` now passes.
- [x] 1.3 [req: harness-read-verbs] Run `python3 -m unittest` over
      `plugins/s/skills/build/tests/test_harness_registry.py`,
      `test_harness_generate.py`, and `test_harness_bodies.py` — the
      registry-iterating suites must pass with fourteen entries — and run
      `plugins/s/bin/shipd harness`, confirming a `pi` line appears
      alongside `oh-my-pi` with exit code 0.

## 2. Esc aborts the install multi-select

- [x] 2.1 [req: install-verb] In
      `plugins/s/skills/build/tests/test_install_tui.py`, add a module-level
      `ESCAPE = b"\x1b"` constant beside the existing `ABORT`/`INTERRUPT`
      constants, extend `test_every_abort_key_decodes_to_abort` to assert
      `it.decode_keys(ESCAPE) == [it.ABORT]`, and add a
      `test_escape_sequences_keep_their_meaning` method to the same class
      asserting `it.decode_keys(b"\x1b[A") == [it.UP]`,
      `it.decode_keys(b"\x1b[B") == [it.DOWN]`, and
      `it.decode_keys(b"\x1b[C") == []`. Run the file with
      `python3 -m unittest` and observe the bare-`Esc` assertion fail — a
      lone `\x1b` currently decodes to `[]`.
- [x] 2.2 [req: install-verb] In
      `plugins/s/skills/build/scripts/install_tui.py`, add `b"\x1b": ABORT`
      to the `_KEYS` mapping (beside `b"\x03"`) and extend the mapping's
      comment to say that the `\x1b[` branch in `decode_keys` runs first, so
      this entry only ever sees an `Esc` that introduces no escape sequence.
      Confirm the tests from 2.1 now pass.
- [x] 2.3 [req: install-verb] In
      `plugins/s/skills/build/scripts/install_tui.py`, change `HINT` to
      `"↑/↓ move · space toggle · a all · enter confirm · esc/q quit"`.
      Leave `LINE_HINT` and `line_prompt`'s abort words unchanged.
- [x] 2.4 [req: install-verb] In
      `plugins/s/skills/build/tests/test_install_tui.py`, add a
      pseudo-terminal test beside
      `test_an_abort_writes_nothing_and_restores_the_terminal` that drives
      the flow with `TOGGLE + DOWN + TOGGLE + ESCAPE` and asserts the same
      outcome — no selection record written and the terminal attributes
      restored — plus an assertion that the rendered hint contains `esc`.
      Run the file and confirm it passes.

## 3. Documentation and version

- [x] 3.1 [req: harness-mode-docs] In `README.md` (the "registry's thirteen
      harnesses" sentence, currently line 87), change "thirteen" to
      "fourteen".
- [x] 3.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.163` to `0.6.164`.
- [x] 3.3 [req: *] Run the whole stdlib engine suite —
      `python3 -m unittest discover -s plugins/s/skills/build/tests` — with
      neither `textual` nor `pydantic` installed, and confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 152 | 33.1k |
| (no tool) | 0 | 986 |
| Agent | 2 | 711 |
| Read | 32 | 404 |
| Edit | 10 | 395 |
| SendMessage | 1 | 378 |
| ToolSearch | 1 | 326 |
| **Total** | 198 | 36.3k |
