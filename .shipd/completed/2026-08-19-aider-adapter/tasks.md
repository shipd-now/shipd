## 1. Registry and template

- [x] 1.1 [req: registry-data] In
      `plugins/s/skills/build/tests/test_harness_registry.py`, update the
      structural invariant to require `{command}` only in non-
      `conventions-file` dialects' patterns (and its absence in
      `conventions-file` patterns), and update the aider assertions to
      `repo_pattern == "shipd-conventions.md"` with `user_dir is None` and
      empty features. Run and observe the aider assertions fail.
- [x] 1.2 [req: registry-data] In
      `plugins/s/skills/build/scripts/harness_registry.py`, set the aider
      entry's `repo_pattern` to `"shipd-conventions.md"`. The 1.1 tests
      pass.
- [x] 1.3 [req: dialect-rendering] Add
      `plugins/s/harness/bodies/_conventions.md` per `plan.md`'s
      Implementation: the shipd intro and spec-driven loop prose, the
      `{preamble}` and `{command_index}` placeholders, the `/run` and
      `--read` guidance for aider, and the closing
      `read: shipd-conventions.md` note for `.aider.conf.yml`.

## 2. Renderer and actions

- [x] 2.1 [req: dialect-rendering, harness-add-remove] Extend
      `plugins/s/skills/build/tests/test_harness_generate.py`: the
      conventions render substitutes both placeholders (no `{preamble}` or
      `{command_index}` in output), indexes every
      `harness_bodies.commands()` entry as `shipd-<command>` with its
      description, contains the preamble's scripts snippet, and starts
      with the ownership marker; `add aider --root <tmp>` writes exactly
      one file (`shipd-conventions.md`, marked), reports the
      `.aider.conf.yml` `read:` step, and re-runs byte-identically;
      `add aider --user` (isolated `HOME`) exits 0, reports skipped,
      writes nothing; `remove aider --root` deletes the marked file and
      keeps an unmarked neighbor; `status` for aider walks
      absent → installed → stale. Run and observe the new tests fail.
- [x] 2.2 [req: dialect-rendering, harness-add-remove] Implement in
      `plugins/s/skills/build/scripts/harness_generate.py`: a
      `conventions-file` branch in `render_file` (read `_conventions.md`
      and `_preamble.md` from the bodies dir, substitute `{preamble}` and
      `{command_index}` — one `- shipd-<command> — <description>` line per
      command — and emit `MARKER` first, replacing the current
      `ValueError`); surface resolution treating a `{command}`-less
      `repo_pattern` as a single whole-harness target file (branch on the
      dialect before per-command iteration); the aider add-report line
      naming the `read:` wiring. The 2.1 tests pass.
- [x] 2.3 [req: harness-add-remove] In `README.md`'s harness-mode section,
      add one sentence: aider has no command files, so
      `shipd harness add aider` writes an ownership-marked
      `shipd-conventions.md` to wire into `.aider.conf.yml` via `read:`.
- [x] 2.4 [req: *] Run the CI suite command
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v`
      without `textual`/`pydantic` installed and observe all tests pass.

## 3. Ship the snapshot

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      the next patch above the branch's post-base-merge value.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| (no tool) | 0 | 20.1k |
| Bash | 38 | 19.5k |
| Edit | 8 | 3.8k |
| Write | 3 | 3.2k |
| Agent | 2 | 2.0k |
| Read | 3 | 324 |
| **Total** | 54 | 49.0k |
