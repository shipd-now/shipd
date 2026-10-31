## ADDED Requirements

### Requirement: Layout status verb
id: layout-status-verb

The status CLI SHALL provide a read-only `init-status` verb that reports
whether the root is set up, accepting `--root DIR` after the verb (as `init`
does), an `--unattended` flag, and the `--json` flag. The verb SHALL resolve
the content directory exactly as `init` does — through the layered
configuration, honoring `dir` and `store_root` from any layer — and SHALL
report one verdict:

- `ready` when the `verified/`, `planned/`, `completed/`, and `research/`
  directories all exist under the resolved content directory;
- `first-run` when the layout is not complete, the root itself holds no
  `.shipd-config.json` file, and the resolved content directory does not
  exist — a `.shipd-config.json` in a workspace or user layer SHALL NOT count
  as the project being set up;
- `layout-missing` in every other case.

The verb SHALL be unattended when the `--unattended` flag is given or when the
environment variable `SHIPD_UNATTENDED` equals exactly `1`; any other value,
or its absence, SHALL be attended. The verb SHALL derive one action from the
verdict: `none` for `ready`, `scaffold` for `layout-missing`, `wizard` for an
attended `first-run`, and `scaffold` for an unattended `first-run`.

The text report SHALL be exactly four lines, in this order: `verdict:
<verdict>`, `content-dir: <path>` (relative to the root when the content
directory lies inside it, absolute otherwise), `unattended: true|false`, and
`action: <action>`. Under `--json` the verb SHALL print one object with the
keys `verdict`, `content_dir` (absolute path), `unattended` (boolean), and
`action`. The verb SHALL exit `0` for every verdict. The verb SHALL create,
modify, and remove nothing, and like `init` it SHALL be exempt from the schema
compatibility gate. If the layered configuration cannot be read, then the
verb SHALL report it through the standard `Error:` convention and exit
non-zero.

#### Scenario: A bare repository is on its first run
- **GIVEN** a root with no `.shipd-config.json` and no `.shipd/` directory,
  and no `SHIPD_UNATTENDED` in the environment
- **WHEN** `spec_status.py init-status --root <root>` runs
- **THEN** it prints `verdict: first-run`, `content-dir: .shipd`,
  `unattended: false`, and `action: wizard`, exits `0`, and the root is
  unchanged on disk

#### Scenario: Repo config without folders is layout-missing
- **GIVEN** a root whose own `.shipd-config.json` declares `{"dir": "specs"}`
  and which has no `specs/` directory
- **WHEN** `init-status` runs on it
- **THEN** it prints `verdict: layout-missing`, `content-dir: specs`, and
  `action: scaffold`

#### Scenario: A partial layout is layout-missing
- **GIVEN** a root with no `.shipd-config.json` whose `.shipd/` holds only
  `verified/`
- **WHEN** `init-status` runs on it
- **THEN** it prints `verdict: layout-missing`

#### Scenario: Workspace config alone does not set the project up
- **GIVEN** a root with no `.shipd-config.json` and no content directory,
  beneath a parent directory whose `.shipd-config.json` declares a
  `workspace` key
- **WHEN** `init-status` runs on the root
- **THEN** it prints `verdict: first-run`

#### Scenario: An initialized root is ready
- **GIVEN** a root on which `spec_status.py init` has run
- **WHEN** `init-status` runs on it
- **THEN** it prints `verdict: ready` and `action: none`

#### Scenario: Unattended first run scaffolds instead of opening the wizard
- **GIVEN** a bare root as in the first scenario
- **WHEN** `init-status` runs with `SHIPD_UNATTENDED=1` in its environment,
  and again with no such variable but the `--unattended` flag
- **THEN** both runs print `verdict: first-run`, `unattended: true`, and
  `action: scaffold`

#### Scenario: Only the value 1 switches unattended on
- **GIVEN** a bare root
- **WHEN** `init-status` runs with `SHIPD_UNATTENDED=0`
- **THEN** it prints `unattended: false` and `action: wizard`

#### Scenario: JSON output carries the same verdict
- **GIVEN** a bare root
- **WHEN** `init-status --json` runs on it
- **THEN** stdout is one JSON object whose `verdict` is `first-run`, whose
  `content_dir` is the absolute path of `<root>/.shipd`, whose `unattended`
  is `false`, and whose `action` is `wizard`

#### Scenario: A malformed repo config is an error
- **GIVEN** a root whose `.shipd-config.json` is not valid JSON
- **WHEN** `init-status` runs on it
- **THEN** it prints an `Error:` line naming that file and exits non-zero
