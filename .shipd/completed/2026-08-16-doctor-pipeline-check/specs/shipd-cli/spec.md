## MODIFIED Requirements

### Requirement: Doctor preflight verb
id: doctor-verb
base: 0cc112b9c3d0

The `shipd` binary SHALL provide a read-only `doctor` verb that runs
environment preflight checks and prints one `ok <check> — <detail>`,
`warn <check> — <detail>`, or `fail <check> — <detail>` line per check
followed by a closing `doctor: ok` or `doctor: <n> problem(s)` line, and
SHALL exit `1` if any check reports `fail` and `0` otherwise. The
required checks SHALL be: `python` (interpreter at least 3.9), `git`
(present on PATH), `config` (a resolvable layered configuration at the
working directory; a missing content directory is reported `ok` with a
note), and `pipeline` (the effective autonomous pipeline at the working
directory, resolved through the engine's resolver: `ok` naming the
resolved entry count and provenance when it resolves — the built-in
default included — and `fail` carrying the resolver's own error line
when a declared pipeline cannot resolve, whether from malformed entries,
an unknown preset, or missing pydantic), with `pipeline` reported
directly after `config`. The warning checks SHALL be: `gh` (present on
PATH and `gh auth status` exiting 0), `textual` (importable), `pydantic`
(importable, probed via `importlib.util.find_spec` without importing it,
so the binary itself stays stdlib-only), `snapshot` (when the binary
runs from a plugin cache snapshot that is not the newest version
directory in the cache; when the binary runs from a repository checkout,
the check SHALL report dev mode as `ok`), and `statusline` (when the
Claude Code user settings file — default `~/.claude/settings.json` — is
absent or carries no `statusLine` key, probed read-only; the warning
detail SHALL name `shipd statusline install` as the remedy, and a
present registration SHALL report `ok`). The `pydantic` check SHALL
stay `warn` when pydantic is not importable and no declared pipeline
requires it, and SHALL escalate to `fail` — naming the supplying config
path — when the resolved configuration declares an `autonomous-pipeline`
whose validation requires pydantic: a list value, or a known preset name
other than `default`. An absent key, the `default` preset, an unknown
preset name, or an unresolvable configuration SHALL NOT escalate it. The
verb SHALL mutate nothing.

#### Scenario: Healthy environment reports ok
- **WHEN** `shipd doctor` runs with python >= 3.9, git present, a resolvable
  config, a resolvable pipeline, gh authenticated, and the newest snapshot
- **THEN** every line begins `ok` and the closing line is `doctor: ok` with
  exit code `0`

#### Scenario: Missing git fails the preflight
- **WHEN** `shipd doctor` runs with no `git` on PATH
- **THEN** a `fail git — ` line with an actionable hint is printed and the
  exit code is `1`

#### Scenario: Unauthenticated gh only warns
- **WHEN** `shipd doctor` runs with `gh` absent or `gh auth status` failing,
  all required checks passing
- **THEN** a `warn gh — ` line is printed and the exit code is `0`

#### Scenario: Missing textual only warns
- **WHEN** `shipd doctor` runs without `textual` importable, all required
  checks passing
- **THEN** a `warn textual — ` line names the board as the only affected
  surface and the exit code is `0`

#### Scenario: Missing pydantic only warns without a declared pipeline
- **WHEN** `shipd doctor` runs without `pydantic` importable in a repo whose
  configuration declares no `autonomous-pipeline`, all required checks
  passing
- **THEN** a `warn pydantic — ` line names declared-pipeline validation as
  the only affected surface with a `pip install -r requirements.txt` hint
  and the exit code is `0`

#### Scenario: Stale snapshot warns
- **WHEN** `shipd doctor` runs from a cache snapshot directory that is not
  the newest version in the cache
- **THEN** a `warn snapshot — ` line names the newer version and the exit
  code is `0`

#### Scenario: Unregistered statusline only warns
- **WHEN** `shipd doctor` runs against a settings file with no `statusLine`
  key, all required checks passing
- **THEN** a `warn statusline — ` line names `shipd statusline install` as
  the remedy and the exit code is `0`

#### Scenario: Registered statusline reports ok
- **WHEN** `shipd doctor` runs against a settings file whose `statusLine`
  key holds a command
- **THEN** the `statusline` check line begins `ok`

#### Scenario: Resolvable pipeline reports its provenance
- **WHEN** `shipd doctor` runs in a repo whose effective pipeline resolves
  (a declared list or preset, or no declaration at all)
- **THEN** an `ok pipeline — ` line names the resolved entry count and the
  provenance (`default` when no layer declares the key)

#### Scenario: Unresolvable declared pipeline fails the preflight
- **WHEN** `shipd doctor` runs in a repo declaring an `autonomous-pipeline`
  that cannot resolve — malformed entries, an unknown preset, or a
  declaration requiring pydantic while it is not importable
- **THEN** a `fail pipeline — ` line carries the resolver's own error line
  and the exit code is `1`

#### Scenario: Declared pipeline escalates missing pydantic
- **WHEN** `shipd doctor` runs without `pydantic` importable in a repo whose
  configuration declares an `autonomous-pipeline` list (or a known preset
  other than `default`)
- **THEN** a `fail pydantic — ` line names the supplying config path with
  the `pip install -r requirements.txt` hint and the exit code is `1`

#### Scenario: Default preset never escalates pydantic
- **WHEN** `shipd doctor` runs without `pydantic` importable in a repo
  declaring `"autonomous-pipeline": "default"`
- **THEN** the `pipeline` line is `ok`, the `pydantic` line is `warn`, and
  the exit code is `0`
