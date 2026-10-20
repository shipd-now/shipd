## ADDED Requirements

### Requirement: Run fails with one line where its modules are absent
id: room-run-missing-modules

If `room.py run` is invoked where `room_run` or `session_driver` cannot be
imported, as in the room wake bundle under `.github/shipd-room/`, then
`room.py` SHALL print exactly one `Error:` line on stderr naming the missing
module and pointing at `shipd room run`, SHALL print no traceback and nothing
on stdout, SHALL make no `gh` call, and SHALL exit `1`. If the import fails
on any other module, then the `ImportError` SHALL propagate unchanged. The
check SHALL be covered in `plugins/s/skills/room/tests/test_room_run.py`
through `room.main`, with no network.

#### Scenario: A run without its module prints one Error line
- **WHEN** `room.main(["run", "7", "--role", "reviewer", ...])` runs with
  `room_run` unimportable
- **THEN** stderr holds exactly one line, it starts with `Error:` and names
  `room_run` and `shipd room run`, stderr holds no `Traceback`, stdout is
  empty, no `gh` call was made, and the exit code is `1`

#### Scenario: An unrelated import failure still propagates
- **WHEN** `room_run` itself imports a module that does not exist
- **THEN** `room.main` raises `ModuleNotFoundError` naming that module rather
  than printing the one-line error
