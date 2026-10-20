# room-bundle-run
Status: verified
Planned-at: aa3b0a8f7d00cbe7be74eabdf743a958aa11afda
Gated-hash: 2fcea9ca31e2

## Idea

Make `room.py run` fail with one clear `Error:` line when its modules are
missing, and pin with a test that the room wake bundle serves every other verb.

### Motivation

A consumer who runs `python3 .github/shipd-room/skills/room/scripts/room.py
run ...` from the installed room bundle gets a `ModuleNotFoundError`
traceback, with nothing to say that `run` is a local-only verb (raised by
reviewer-b on https://github.com/mikkel-bergmann/unkannybanny/pull/37).
Nothing breaks today because `room-wake.yml` never calls `run`, but no test
says which verbs the bundle supports, so a new top-level import could break
the wake without anyone noticing.

### Details

- `room.py`'s `run` dispatch turns a missing `room_run`/`session_driver`
  import into a `RoomError` with one line, and exits `1`.
- New tests: the guard through `room.main` (room suite), and an installed
  bundle run under `python3 -I -B` for every wake verb's `--help` plus the
  bundled `run`'s one-line failure (copilot verb suite).
- `docs/room-wake-reference.md` states that the bundle omits `run`.
- `plugin.json` goes from `0.6.341` to `0.6.342`.

Affected capabilities: `room-runner` (added `room-run-missing-modules`),
`shipd-cli` (added `copilot-room-wake-self-contained`). Impact:
`plugins/s/skills/room/scripts/room.py`,
`plugins/s/skills/room/tests/test_room_run.py`,
`plugins/s/skills/build/tests/test_copilot_verb.py`,
`docs/room-wake-reference.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to `ROOM_RUNTIME` in `plugins/s/bin/shipd`, its staleness rules
  or the `# shipd-copilot v<version>` marker. The bundle stays five files.
- No change to `room-wake.yml` or to how `run` behaves where its modules exist.
- No guard for `room_run_repo` missing while `room_run` is present. No install
  ever produces that state.

## Implementation

- **Decision: fail clearly, do not bundle.** `run` is a local loop that
  spawns headless harness sessions (`session_driver`). It has no use in an
  Actions job, and the `room_run.py`/`room_run_repo.py` docstrings say the
  wake leaves it out on purpose. Rejected: bundling `room_run.py`,
  `room_run_repo.py` and `session_driver.py`. That would make the consumer's
  copy three files bigger, and every edit to those modules would mark every
  consumer's bundle `stale`, all for a verb the wake cannot use (Q1).
- **`room.py` shape.** Add a module constant
  `RUN_MODULES = ("room_run", "session_driver")` near `RoomError`. In
  `main`, replace the bare `import room_run` with:

  ```python
  try:
      import room_run
  except ImportError as exc:
      if exc.name not in RUN_MODULES:
          raise
      raise RoomError(
          "`run` needs %s.py, which this copy of room.py lacks (the room "
          "wake bundle omits it); run it locally with `shipd room run`"
          % exc.name)
  ```

  The existing `except RoomError` in `main` prints the `Error:` line and
  returns `1`. The import comes after argument parsing and before any `gh`
  call, so a bundled `run` makes no network call. Checking `exc.name` keeps
  a genuine import bug inside `room_run` loud.
- **Bundle test shape.** In `CopilotRoomWakeVerbTest`, install via
  `self.install_room()`, then run
  `[sys.executable, "-I", "-B", self.path(ROOM_ROOM_PY), verb, "--help"]`
  with `cwd=self.root`. Using the installed copy (not a hand copy) ties the
  test to the real `ROOM_RUNTIME`, so the two lists cannot drift apart.
  `-I` keeps the plugin tree and the user's site packages off `sys.path`.
- **Unit test shape.** In `test_room_run.py`, simulate the missing module
  with `mock.patch.dict(sys.modules, {"room_run": None})`, which raises
  `ModuleNotFoundError` with `name == "room_run"`. For the propagate case,
  pop `room_run` from `sys.modules`, put a temp dir holding a stub
  `room_run.py` (`import shipd_no_such_module_xyz`) first on `sys.path`,
  assert `room.main` raises `ModuleNotFoundError` whose `name` is
  `shipd_no_such_module_xyz`, then restore `sys.path` and `sys.modules`.

Risk: the edited `room.py` marks every installed bundle `stale` until
`shipd copilot update` refreshes it. That is the intended staleness path,
and the version bump stales the bundled `plugin.json` anyway.

## Questions and answers

### Q1: Bundle run's modules, or fail with one line?
- **Question:** The room wake bundle leaves out `room_run.py`,
  `room_run_repo.py` and `session_driver.py`, so the bundled `room.py run`
  crashes with a traceback. Options: (1) keep the bundle unchanged, make
  `run` print one `Error:` line naming the missing module and exit `1`, and
  test that every other verb loads from an installed bundle; (2) add the
  three modules to the bundle and to `copilot-room-wake`, with a
  self-contained test that runs every verb. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. `run` spawns local harness sessions and has no use
  in Actions. Bundling it would make the consumer's copy bigger and make
  every edit to `room_run` or `session_driver` mark consumers' bundles stale.
- **Queued:** q-room-bundle-run-missing-modules

## Readiness attestation

### Problem and motivation

Consumers who run `room.py run` from their installed room bundle get a raw
traceback, and nothing tells them `run` is a local-only verb.

Evidence:

- Reported by reviewer-b on
  https://github.com/mikkel-bergmann/unkannybanny/pull/37.
- `plugins/s/skills/room/scripts/room.py:1140-1142` imports `room_run` at
  dispatch, with no guard.
- `plugins/s/skills/room/scripts/room_run.py:9-10` and
  `room_run_repo.py:12-13` record that the wake bundles `room.py` without
  `session_driver`.

### Scope and non-goals

Changes `room.py`'s `run` dispatch, two test files, one reference doc, and the
version. The bundle list and the wake workflow stay unchanged.

Evidence:

- In scope: `room.py:1132-1150`, `test_copilot_verb.py:3534-3720`,
  `docs/room-wake-reference.md:19-23` and `:99-112`.
- Out of scope: `plugins/s/bin/shipd:2042-2048` (`ROOM_RUNTIME`) and
  `room_wake_states` at `:2129-2177` stay unchanged.

### Affected capabilities and files

Two capabilities and five files are affected: the run verb's failure mode
lives in `room-runner`, and the bundle's contract lives in `shipd-cli`.

Evidence:

- Capability `room-runner`: new `room-run-missing-modules`.
- Capability `shipd-cli`: new `copilot-room-wake-self-contained`, next to
  `copilot-room-wake` (base fceeae91e82f, from `spec_status.py base-hash`),
  which stays as it is.
- Files: `plugins/s/skills/room/scripts/room.py`,
  `plugins/s/skills/room/tests/test_room_run.py`,
  `plugins/s/skills/build/tests/test_copilot_verb.py`,
  `docs/room-wake-reference.md`, `plugins/s/.claude-plugin/plugin.json`
  (`0.6.341` on `main`).
- Runnable premise: `shipd copilot add --room --root <tmp>` exited 0 and
  wrote exactly the six wake files. From that install,
  `python3 -I <room.py> <verb> --help` exited 0 for `watch`, `list`, `join`,
  `message`, `close`, `run` and `whoami`. `python3 -I <room.py> run 1 --role
  reviewer` exited 1 with a `ModuleNotFoundError: No module named
  'room_run'` traceback from `main` line 1141.

### No open task-shaping decision

The one task-shaping decision (fail clearly or bundle) is settled by the
PLANNER default, recorded as Q1. Investigation settled the rest.

Evidence:

- Fix approach: PLANNER default, Q1 (oracle INSUFFICIENT, queued
  `q-room-bundle-run-missing-modules`).
- Where the bundle test lives: settled by investigation. The existing
  `CopilotRoomWakeVerbTest` installs through the real verb.
- Version: settled by investigation, one patch above `main`'s `0.6.341`.
