## ADDED Requirements

### Requirement: Config set and unset verbs
id: config-write-verbs

The status CLI SHALL provide `config-set <key> <value> [--layer
repo|workspace|user]` and `config-unset <key> [--layer repo|workspace|user]`,
writing through `config_registry.write_layer`. `config-set` SHALL parse
`<value>` as JSON when it parses and SHALL otherwise take it as a plain string.
Without `--layer`, the write SHALL land in the file of the layer whose
declaration of the key currently wins, else in the key's default layer: `repo`
is the git top level of `--root` (or `--root` itself outside git), `workspace`
the nearest discoverable workspace root, and `user` `~/.shipd-config.json`.
`config-unset` SHALL remove the key from that file, and SHALL print `<key> is
not set in <path>` and exit 0 when the file does not declare it. On success the
verbs SHALL print `set <key> = <json> in <path>` or `unset <key> in <path>` and
exit 0, followed by any warning findings as `warning: <message>` lines on
stderr. If the writer refuses, because the change is invalid or the merged
result holds another invalid key, then the verb SHALL write nothing, print one
`error: <message>` line per problem on stderr each followed by its `hint:
<text>` line where the problem has a hint, and exit 1. If the key has an owning
verb, then the verb SHALL refuse with the hint `use <owning verb>`. If
`--layer workspace` is given and no workspace is discoverable, then the verb
SHALL exit 1 with a single `Error:` line naming `--root`.

#### Scenario: Bogus pr-mode is rejected
- **WHEN** `config-set pr-mode bogus` runs in a repo
- **THEN** no file changes, stderr carries an `error:` line naming `pr-mode`
  and `hint: accepted values: auto, draft`, and the exit code is 1

#### Scenario: Unknown key gets a did-you-mean
- **WHEN** `config-set pr_mode draft` runs
- **THEN** stderr carries `error:` naming `pr_mode` and a `hint:` line naming
  `pr-mode`, and the exit code is 1

#### Scenario: Default layer applies when undeclared
- **GIVEN** no layer declares `voice`
- **WHEN** `config-set voice false` runs
- **THEN** `~/.shipd-config.json` gains `"voice": false` and the repo file is
  untouched

#### Scenario: Owned key points at its verb
- **WHEN** `config-set post-worktree-scripts '["make"]'` runs
- **THEN** nothing is written and stderr carries `hint: use shipd worktree
  hooks add`, exit 1

#### Scenario: Statusline points at its verb
- **WHEN** `config-set statusline '{"lines": [["spec"]]}'` runs
- **THEN** nothing is written and stderr carries `hint: use shipd statusline
  layout`, exit 1

#### Scenario: Another invalid key blocks a set
- **GIVEN** the user layer declares `"pr-mode": "bogus"`
- **WHEN** `config-set voice false` runs
- **THEN** no file changes, stderr carries an `error:` line naming `pr-mode`
  and a `hint:` line naming `shipd config unset pr-mode`, and the exit code
  is 1

#### Scenario: Unset removes the declaring layer's key
- **GIVEN** the repo layer declares `"pr-mode": "draft"`
- **WHEN** `config-unset pr-mode` runs
- **THEN** the repo file no longer declares `pr-mode` and keeps its other keys

### Requirement: Config check verb
id: config-check-verb

The status CLI SHALL provide `config-check`, validating every declared key of
every layer `--root` resolves, nearest first, and printing to stdout one
`error: <path>: <message>` line per invalid value, each followed by its `hint:`
line, one `warning: <path>: unknown key <key>` line per key outside the registry
(with a did-you-mean `hint:` when a close key exists), and a closing
`config check: <n> error(s), <m> warning(s)` line. Comment keys SHALL be
skipped. The verb SHALL exit 1 when any error is reported
and 0 otherwise. A layer file that is not valid JSON SHALL be reported as an
error line naming it.

#### Scenario: A clean config passes
- **WHEN** `config-check` runs where every layer is valid
- **THEN** it prints `config check: 0 error(s), 0 warning(s)` and exits 0

#### Scenario: An unknown key warns without failing
- **GIVEN** a repo layer declaring `"vioce": false`
- **WHEN** `config-check` runs
- **THEN** a `warning:` line names `vioce`, a `hint:` names `voice`, and the
  exit code is 0
