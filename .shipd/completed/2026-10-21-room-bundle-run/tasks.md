## 1. Run fails with one line

- [x] 1.1 [req: room-run-missing-modules] In
      `plugins/s/skills/room/tests/test_room_run.py`, add a
      `RunMissingModuleTest(RunTestBase)` with two tests per plan.md's "Unit
      test shape": (a) under `mock.patch.dict(sys.modules, {"room_run":
      None})`, `self.run_verb(FakeGh(), "7", "--role", "reviewer")` returns
      code `1`, empty stdout, a stderr of exactly one line starting `Error:`
      that contains `room_run` and `shipd room run` and no `Traceback`, and
      `gh.calls == []`; (b) a stub `room_run.py` importing
      `shipd_no_such_module_xyz` makes `room.main` raise
      `ModuleNotFoundError` with that `name`. Run the room suite and observe
      (a) fail.
- [x] 1.2 [req: room-run-missing-modules] In
      `plugins/s/skills/room/scripts/room.py`, add
      `RUN_MODULES = ("room_run", "session_driver")` below `class RoomError`
      and replace the bare `import room_run` in `main` with the guarded
      import from plan.md's "`room.py` shape", message text verbatim. Run
      `python3 -m unittest discover -s plugins/s/skills/room/tests` and
      confirm `OK`.

## 2. Bundle self-containment

- [x] 2.1 [req: copilot-room-wake-self-contained] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, add to
      `CopilotRoomWakeVerbTest`: `test_every_wake_verb_loads_from_the_bundle`
      (after `self.install_room()`, run `[sys.executable, "-I", "-B",
      self.path(ROOM_ROOM_PY), verb, "--help"]` with `cwd=self.root` for each
      of `join`, `list`, `whoami`, `message`, `close`, `watch`; assert exit 0
      and no `Traceback` in stderr) and
      `test_bundled_run_fails_with_one_error_line` (same invocation with
      `run 1 --role reviewer`; assert exit 1, stderr is exactly one line
      starting `Error:` containing `shipd room run`, no `Traceback`). Confirm
      both pass.
- [x] 2.2 [req: copilot-room-wake-self-contained] In
      `docs/room-wake-reference.md`, extend the `room.py` row of the managed
      files table to say the bundled copy omits `run`, which prints one
      `Error:` line there. Add a `## Known limits` bullet: "**The bundle
      cannot run `run`.** `run` drives a local harness session, so the
      bundle leaves out its modules; use `shipd room run` from a developer
      machine." Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/room-wake-reference.md`
      and confirm exit 0.
- [x] 2.3 [req: copilot-room-wake-self-contained] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.341` to `0.6.342`.

## 3. Verify

- [x] 3.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/room/tests` and `python3 -m unittest
      plugins/s/skills/build/tests/test_copilot_verb.py`, and grep each
      output for `OK`/`FAILED`; both report `OK`.
