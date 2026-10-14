## 1. Precondition and version

- [x] 1.1 [req: room-verb-tests] Merge `main` into the change branch after
      `room-schema` has merged; confirm `python3 -c "import room_schema"` from
      `plugins/s/skills/room/scripts/` exits 0 and that `room_schema` exposes
      `AgentCard`, `Message`, `Task`, `parse_comment`, `render_comment`,
      `build_tasks`, `next_state`, `next_round`, `at_round_cap`,
      `SchemaError`, `InvalidTransition`, `MESSAGE_MARKER`, `CARD_MARKER`.
      Stop and report if any symbol is missing.
- [x] 1.2 [req: room-verb-tests] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to one patch above the value
      `main` carries (`0.6.285` when `main` holds `0.6.284`).

## 2. Config key

- [x] 2.1 [req: room-config-key] In
      `plugins/s/skills/build/tests/test_spec_common.py`, after the
      `resolve_pr_mode` class (line 3551), add a `ResolveRoomTest` class:
      no key → `(None, 6)`; a workspace-root layer declaring
      `{"agent": "claude-mikkel", "max_rounds": 4}` governs a member repo;
      `{"max_rounds": 0}` raises `ConfigError` naming `room`, `max_rounds`,
      and the file; `{"agent": ""}` raises; a non-object value raises;
      `{"agent": "x", "interval": 5}` returns `("x", 6)`. Run it and observe
      the AttributeError.
- [x] 2.2 [req: room-config-key] In
      `plugins/s/skills/build/scripts/spec_common.py` add `"room"` to
      `RECOGNIZED_CONFIG_KEYS` (sorted position, line 395-418), and after
      `resolve_pr_mode` add `ROOM_KEY = "room"`, `DEFAULT_ROOM_MAX_ROUNDS = 6`,
      and `resolve_room(root)` per the plan's Config resolver decision.
- [x] 2.3 [req: room-config-key] Add a `// room` entry to
      `plugins/s/skills/build/references/shipd.config.example.json` (after
      `// pr-mode`) describing `agent` (no default; the verb refuses without a
      name) and `max_rounds` (default 6), and a `| \`room\` | ... |` row to
      the key table in `docs/customise.md` after the `pr-mode` row. Run
      `python3 -m unittest plugins/s/skills/build/tests/test_config_sample.py`
      and the task 2.1 class until both pass.

## 3. Dispatch

- [x] 3.1 [req: cli-dispatch] In
      `plugins/s/skills/build/tests/test_shipd_cli.py` add `"room"` to
      `VERBS` (line 41-46) and three tests in `DispatchTest`:
      `shipd.VERB_TABLE.get("room") == ("room.py", [])`;
      `shipd.SKILL_SCRIPT_DIRS["room.py"]` ends with `plugins/s/skills/room/scripts/`;
      `self.cli("room", "--help")` stdout equals a subprocess run of
      `python3 plugins/s/skills/room/scripts/room.py --help` with both exit
      0; and `self.cli("room", "frobnicate")` exits 2 with `room.py`'s usage
      (`usage: room` in stderr, no `shipd <verb>` banner). Observe them fail.
- [x] 3.2 [req: cli-dispatch] In `plugins/s/bin/shipd` add
      `"room": ("room.py", [])` to `VERB_TABLE`, define `SKILL_SCRIPT_DIRS =
      {"room.py": PLUGIN_ROOT / "skills" / "room" / "scripts"}` beneath it
      with a comment naming the constitution's network rule, change the exec
      site (line 2822) to `SKILL_SCRIPT_DIRS.get(script, SCRIPTS) / script`,
      and add the banner line `  room <verb> <pr> [args]    the PR room:
      join, list, message, close` after `worktree`, naming `room list` in the
      `--json` sentence.

## 4. room.py scaffold and gh seam

- [x] 4.1 [req: room-gh-seam] Create `plugins/s/skills/room/tests/test_room.py`
      with the `HERE`/`SCRIPTS` prologue from `test_room_schema.py`, `import
      room` and `import room_schema`, and a `FakeGh` class modelled on
      `plugins/s/skills/review/tests/test_review_gate.py:86-160`: constructor
      `(number=7, repo="o/r", comments=None, review_comments=None, pages=1,
      fail=None)`; answers `["pr","view",...]` with `{"number","url"}`,
      `["repo","view",...]` with `{"nameWithOwner"}`, the `issues/<n>/comments`
      GET with the stored comments and the `pulls/<n>/comments` GET with the
      stored review comments (each asserting `--paginate` and `--slurp`
      present, each split into `pages` arrays; a test seeds a review comment
      with a lower id than an issue comment and asserts the union is ordered
      by id),
      POST by appending `{"id": next, "user": {"login": "bot"}, "body",
      "html_url"}`, PATCH by replacing the body; records every `(args,
      input)`; `fail` names an args prefix to answer `(1, "", "boom")`. Add a
      `_run(argv, gh, env=None)` helper capturing stdout/stderr and the
      return of `room.main(argv, gh=gh)`.
- [x] 4.2 [req: room-gh-seam] Add tests: `list 7` over two pages reports
      cards from both; a failing `pr view` yields exit 1 and one `Error: `
      line; a comment `<!-- shipd-room {not json} -->` yields a `WARNING:
      comment <id>:` line, exit 0, and the other comments reported; a source
      test asserts `room.py` imports no third-party module and names
      `room_schema`, `spec_common`, `cli_common`.
- [x] 4.3 [req: room-gh-seam] Create `plugins/s/skills/room/scripts/room.py`:
      docstring, `HERE`, `BUILD_SCRIPTS = HERE/../../build/scripts` inserted
      on `sys.path`, imports, `class RoomError(Exception)`, `_default_gh`,
      `_gh_json(gh, args, input=None)` (raises `RoomError` with the stderr
      text on rc != 0), `_resolve_room(gh, pr)`, `_read_room(gh, repo,
      number)` (reads `issues/<n>/comments` and `pulls/<n>/comments`, orders
      the union by comment id, parses each body with `parse_comments`,
      warn-and-skip via `cli_common.warn`), `_post`, `_patch`, an
      argparse `main(argv=None, gh=None)` with the four subparsers and a
      shared parent parser carrying `--agent`, `--root`, `--max-rounds`,
      catching `RoomError` → `cli_common.err` + return 1. Run the 4.2 tests
      until they pass (verb bodies may be stubs returning 0 here).

## 5. Identity and join

- [x] 5.1 [req: room-agent-identity, room-join-verb] Add tests: `join 7
      --agent codex-a --skill review-finding --harness codex` on an empty PR
      records one POST whose body's first line parses to an `AgentCard`
      named `codex-a` with skills `("review-finding",)` and `version` equal
      to the plugin manifest's; a second `join` with `--description x`
      records a PATCH on that id and the room still holds one card; `join 7`
      with no `--agent`, `SHIPD_ROOM_AGENT` unset, and `--root` a temp dir
      exits 2 with usage text naming `--agent`, `SHIPD_ROOM_AGENT`, and
      `room.agent`; `join 7` with `SHIPD_ROOM_AGENT=codex-a` posts as
      `codex-a`; `--root` a temp dir whose `.shipd-config.json` declares
      `room.agent` posts under that name.
- [x] 5.2 [req: room-agent-identity, room-join-verb] In `room.py` implement
      `_agent_name(opts, parser, root)` (flag, env, `resolve_room`, else
      `parser.error`), `_max_rounds(opts, root)`, `_plugin_version()`
      reading `plugins/s/.claude-plugin/plugin.json` (three levels above `HERE`), `_require_card(cards,
      name, context)` raising the `has not joined` `RoomError`, and
      `cmd_join` (upsert by card name, JSON on stdout, `joined` line on
      stderr). Run the 5.1 tests until they pass.

## 6. List

- [x] 6.1 [req: room-list-verb] Add tests: a PR with cards `codex-a`,
      `claude-b` and an opener from `codex-a` to `claude-b` prints both
      cards and a `#<id>  input-required  from codex-a  to claude-b  round 1
      last codex-a` line; `--json` returns `cards` of length 2 and one task
      with `messages` 1 and the listed keys; a PR of unmarked comments prints
      `(none)` under both blocks.
- [x] 6.2 [req: room-list-verb] Implement `cmd_list` in `room.py` per the
      requirement's text and JSON shapes, formatting task lines with
      `_task_line(task)`. Run the 6.1 tests until they pass.

## 7. Message and close

- [x] 7.1 [req: room-message-verb] Add tests (agent `codex-a` and `claude-b`
      both joined unless stated): `message 7 --new --to claude-b "please
      check"` posts a marker with no `taskId` and metadata
      `{"round":1,"state":"input-required","to":"claude-b"}`, stdout `task`
      equals the comment id; `--new` without `--to` posts `submitted`;
      `--new --skill review-finding` sets `metadata.skill`; a reply on task
      10 (`input-required`, round 1, last `codex-a`) as `claude-b` with
      `--to codex-a --state completed` posts `taskId` 10 and round 2; a reply
      without `--state` and without `--to` posts `working`, with `--to` posts
      `input-required`; `--task 99` exits 1 with `not found`; a reply on a
      `completed` task posts nothing and exits 1 with `no transition`; at
      round 6 with `--max-rounds 6` as the other party the only post is
      `failed`/`round-cap`/round 7 and the exit is 1 with `round cap
      reached`; an unjoined agent exits 1 with `has not joined`.
- [x] 7.2 [req: room-message-verb] Implement `cmd_message` in `room.py`:
      resolve, read, require card, find task (or `--new`), compute state via
      `next_state` (map `InvalidTransition` to the `no transition`
      `RoomError`), compute round, run the cap check, build the `Message`,
      render, post, print JSON. Run the 7.1 tests until they pass.
- [x] 7.3 [req: room-close-verb] Add tests: `close 7 --task 10` as `claude-b`
      posts `completed`, round 2, no `reason`, text `closed: completed`;
      `close 7 --task 10 --state failed --reason stalled` at round 6 with max
      6 posts `{"reason":"stalled","round":7,"state":"failed"}` and exits 0;
      `close` on a `canceled` task exits 1 with `no transition`.
- [x] 7.4 [req: room-close-verb] Implement `cmd_close` in `room.py` sharing
      `cmd_message`'s resolve/read/require/find/post helpers, with no cap
      check. Run the 7.3 tests until they pass.

## 8. Verification

- [x] 8.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/room/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`; grep each output for `OK` (not the
      tail). Run `python3 plugins/s/skills/document/scripts/docs_lint.py
      docs/customise.md`, `python3 plugins/s/skills/build/scripts/version_guard.py
      --base main --head HEAD`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py room-cli-verb`; all exit 0.
