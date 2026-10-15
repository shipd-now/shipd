## 1. Precondition and version

- [x] 1.1 [req: room-skill-docs] Merge `main` into the change branch after
      `room-schema`, `room-cli-verb`, and `room-watch` have merged; confirm
      `shipd room --help` lists `join`, `list`, `message`, `close`, and
      `watch`, that `watch` accepts `--since`, `--timeout`, and `--once`, and
      that `plugins/s/skills/room/tests/` exists. Stop and report if any is
      missing.
- [x] 1.2 [req: room-skill-docs] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to one patch above the value
      `main` carries.

## 2. Tests first

- [x] 2.1 [req: room-skill-loop, room-skill-stops, room-skill-no-code, room-skill-body, room-skill-docs]
      Add
      `plugins/s/skills/room/tests/test_room_skill.py` (stdlib `unittest`,
      importing `harness_bodies` from `plugins/s/skills/build/scripts` via
      `sys.path`, as `test_harness_bodies.py` does) with one test per delta
      scenario: verb order and the `--skill review-finding --skill question
      --skill status` and `--timeout 600` strings in `SKILL.md`; every
      `shipd room message` line
      carries `--state`; the empty-watch stop, the round-cap stop, and the
      foreground-only `watch` rule are present; the no-code rule names
      `/s:fix` and `/s:plan`; `render("room", ())` has `shipd room list` and
      no `shipd room watch`; `render("room", ("background-tasks",))` has
      `shipd room watch` and `--timeout 600`; `AGENTS.md`, `README.md`, and
      `docs/cheatsheet.md` contain `/s:room`; `docs_lint.py docs/pr-room.md`
      exits 0 (subprocess). Run it and observe the failures.

## 3. Skill and body

- [x] 3.1 [req: room-skill-loop, room-skill-stops, room-skill-no-code] Write
      `plugins/s/skills/room/SKILL.md`: frontmatter `name: room` and a
      `description` with trigger phrases ("join the PR room", "answer the
      room", "/s:room"); a version announcement as `plugins/s/skills/memory/SKILL.md` does;
      the numbered loop per the plan's "Loop" decision; the stop list; the
      foreground-only `watch` rule; the prose-only rule and the
      already-addressed `review-finding` rule. Invoke the binary as
      `"${CLAUDE_PLUGIN_ROOT}/bin/shipd" room …`.
- [x] 3.2 [req: room-skill-body] Write `plugins/s/harness/bodies/room.md`
      (description marker, `<!-- include:preamble -->`, the loop gated on
      `<!-- if:background-tasks -->` with the single `list --json` read in
      `<!-- else -->`, a `file-references` pointer to `{refs}/room.md`) and
      `plugins/s/harness/references/room.md` holding the NDJSON line fields
      and the stop list. Keep the words `subagent` and `sub-agent` out of
      every ungated segment. Run `test_room_skill.py` and
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p
      'test_harness_*.py'` until both pass.

## 4. Docs and registration

- [x] 4.1 [req: room-skill-docs] Author `docs/pr-room.md` through the
      `/s:document` standard as a `how-to` ("Hold an agent conversation on a
      pull request"): join, read, watch, reply, close, the round cap, and the
      prose-only boundary; link `customise.md` for the `room` key. Run
      `docs_lint.py docs/pr-room.md` until it exits 0.
- [x] 4.2 [req: room-skill-docs] Add `/s:room` to `AGENTS.md`'s skill
      sentence in "Spec layout and lifecycle", a row to the README
      **Orchestration** table, a row to the `docs/cheatsheet.md` command
      table, and `s:room` to the cheatsheet's "Epics, driven" group. Run
      `test_room_skill.py` until it passes.

## 5. Verification

- [x] 5.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/room/tests -v` and `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`; grep each output for `OK`, not the
      tail. Run `version_guard.py --base main --head HEAD` and
      `spec_lint.py room-skill`; all exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| (no tool) | 0 | 3.0k |
| Bash | 85 | 3.0k |
| SubagentHandback | 8 | 74 |
| Write | 7 | 74 |
| Agent | 5 | 8 |
| **Total** | 105 | 6.1k |
