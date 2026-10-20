## ADDED Requirements

### Requirement: Room wake bundle is self-contained
id: copilot-room-wake-self-contained

The five runtime files that `shipd copilot add --room` installs under
`.github/shipd-room/` SHALL be self-contained for every `room.py` verb except
`run`: where the installed `room.py` runs under `python3 -I -B`, each of
`join`, `list`, `whoami`, `message`, `close` and `watch` SHALL parse
`--help` with exit `0` and no traceback. The bundled `run` SHALL fail per
room-runner `room-run-missing-modules`, so the bundle list stays the five
files named in `copilot-room-wake`. `docs/room-wake-reference.md` SHALL state
that the bundle omits `run` and point at `shipd room run`, and SHALL lint
clean. `plugin.json` SHALL carry a version one patch above `main`'s.

#### Scenario: Every wake verb loads from the installed bundle
- **WHEN** `shipd copilot add --room --root <dir>` has run and
  `python3 -I -B <dir>/.github/shipd-room/skills/room/scripts/room.py <verb> --help`
  runs for each of `join`, `list`, `whoami`, `message`, `close`, `watch`
- **THEN** each exits `0` and its stderr holds no `Traceback`

#### Scenario: The bundled run fails with one Error line
- **WHEN** the installed bundle's `room.py run 1 --role reviewer` runs
- **THEN** stderr holds exactly one line, it starts with `Error:` and names
  `shipd room run`, stderr holds no `Traceback`, and the exit code is `1`

#### Scenario: The wake reference names the omission
- **WHEN** `docs_lint.py docs/room-wake-reference.md` runs
- **THEN** it exits `0`, and the file names `shipd room run` beside the
  bundled `room.py` row
