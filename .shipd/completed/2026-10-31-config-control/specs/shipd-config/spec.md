## ADDED Requirements

### Requirement: Config key registry
id: config-key-registry

The engine SHALL define, in `plugins/s/skills/build/scripts/config_registry.py`,
a registry carrying exactly one entry per member of
`spec_common.RECOGNIZED_CONFIG_KEYS`, each entry holding a validator, a one-line
hint, and a default layer (`repo`, `workspace`, or `user`), and optionally an
owning verb, as listed in `artefacts/registry.md`. Each validator SHALL reuse
the engine's existing accessor logic where one raises on a bad value, so a
rejected value reports the same message the accessor would. The module SHALL be
stdlib-only. A top-level key starting with `//` SHALL be treated as a comment
and never validated. `RECOGNIZED_CONFIG_KEYS` SHALL include `statusline`,
whose entry accepts what `shipd statusline layout` loads today and names that
verb as its owner.

#### Scenario: Registry covers every recognised key
- **WHEN** the registry's keys are compared with `RECOGNIZED_CONFIG_KEYS`
- **THEN** the two sets are equal

#### Scenario: A validator reuses the accessor message
- **WHEN** the `pr-mode` validator runs on `"bogus"` declared in a file
- **THEN** it reports the same text `resolve_pr_mode` raises for that file and
  value

#### Scenario: A bad statusline layout is rejected
- **WHEN** the `statusline` validator runs on `{"lines": [["spec", "spec"]]}`
- **THEN** it reports that segment `spec` appears more than once, as `shipd
  statusline layout` does today

### Requirement: The one config writer
id: config-layer-writer

The engine SHALL provide one writer, `config_registry.write_layer(path, data,
anchor)`, through which every engine write of a `.shipd-config.json` file goes.
Before touching disk it SHALL validate every top-level key whose value differs
between the file's current content and `data` on its own. It SHALL then
validate every registered key of the merged configuration resolved from
`anchor` with `data` in place of the file, changed or not. If any key fails
either check, then the writer SHALL write nothing and raise a `ConfigError`
subclass carrying one error finding per problem. The finding for a key the
write did not change SHALL carry the hint `fix it with shipd config set <key>
<value> or shipd config unset <key>`. A changed key outside the registry SHALL
fail with a did-you-mean hint when a close registry key exists. An unchanged
key outside the registry SHALL NOT block the write; it SHALL be returned as a
warning finding. The writer SHALL write atomically (a temp file in the same directory, renamed over
the target), as 2-space-indented JSON with a trailing newline, keeping an
existing file's permission mode and every key it did not change.

#### Scenario: An invalid change writes nothing
- **GIVEN** a repo layer declaring `{"voice": true}`
- **WHEN** the writer is asked to write `{"voice": true, "pr-mode": "bogus"}`
- **THEN** it raises naming `pr-mode`, and the file is byte-identical to before

#### Scenario: An unrelated invalid key blocks the write
- **GIVEN** a user layer declaring `"pr-mode": "bogus"` and an empty repo layer
- **WHEN** the writer writes `{"voice": false}` to the repo layer
- **THEN** it raises with an error finding naming `pr-mode` and the hint `fix
  it with shipd config set pr-mode <value> or shipd config unset pr-mode`,
  and the repo file is unchanged

#### Scenario: Fixing the invalid key succeeds
- **GIVEN** a user layer declaring `"pr-mode": "bogus"`
- **WHEN** the writer writes `{}` to the user layer
- **THEN** the file is written without `pr-mode` and no finding is raised

#### Scenario: An unrelated unknown key only warns
- **GIVEN** a repo layer declaring `{"vioce": false}`
- **WHEN** the writer writes `{"vioce": false, "voice": true}` to it
- **THEN** the file is written and a warning finding names `vioce`

#### Scenario: An outer write cannot hide a bad value
- **GIVEN** a repo layer declaring `"pr-mode": "auto"`
- **WHEN** the writer writes `{"pr-mode": "bogus"}` to the user layer
- **THEN** it raises naming `pr-mode` and writes nothing

### Requirement: Existing writers use the one writer
id: config-writer-migration

`spec_common.init_workspace`, the `workspace-project` verb's registry write in
`spec_status.py`, the `worktree hooks add` / `remove` writes in `worktree.py`,
and the `shipd statusline layout` save in `bin/shipd` SHALL each write
`.shipd-config.json` through `config_registry.write_layer`. Each SHALL keep its
current stdout, stderr, exit codes, and refusal messages for a valid config.
While the merged configuration holds an invalid key, each SHALL refuse, write
nothing, print the writer's `error:` and `hint:` lines, and exit 1. No other
engine code under `plugins/s/skills/build/scripts/` or in `bin/shipd` SHALL
open a `.shipd-config.json` file for writing.

#### Scenario: Hooks add output is unchanged
- **WHEN** `shipd worktree hooks add "echo hi"` runs in a repo with no config
- **THEN** it prints `post-worktree-scripts: added echo hi (<repo>/.shipd-config.json)`,
  exits 0, and the file holds the one-item list

#### Scenario: Statusline layout saves through the writer
- **WHEN** `shipd statusline layout spec,context directory --config <path>`
  runs with no file at `<path>`
- **THEN** it prints `statusline layout saved in <path>` and the two lines,
  exits 0, and `<path>` declares `{"statusline": {"lines": [["spec",
  "context"], ["directory"]]}}`

#### Scenario: A migrated writer refuses while another key is invalid
- **GIVEN** a repo layer declaring `"pr-mode": "bogus"`
- **WHEN** `shipd worktree hooks add "echo hi"` runs
- **THEN** stderr carries an `error:` line naming `pr-mode`, the file is
  unchanged, and the exit code is 1

#### Scenario: No stray writer remains
- **WHEN** the engine scripts are searched for an open-for-write of a path built
  from `CONFIG_FILENAME`
- **THEN** the only match is inside `config_registry.py`
