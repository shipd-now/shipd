## MODIFIED Requirements

### Requirement: Doctor preflight verb
id: doctor-verb
base: 1bd04a680666

The `shipd` binary SHALL provide a read-only `doctor` verb that runs
environment preflight checks and prints one `ok <check> — <detail>`,
`warn <check> — <detail>`, or `fail <check> — <detail>` line per check
followed by a closing `doctor: ok` or `doctor: <n> problem(s)` line, and
SHALL exit `1` if any required check fails and `0` otherwise. The required
checks SHALL be: `python` (interpreter at least 3.9), `git` (present on
PATH), and `config` (a resolvable layered configuration at the working
directory; a missing content directory is reported `ok` with a note). The
warning checks — never affecting the exit code — SHALL be: `gh` (present on
PATH and `gh auth status` exiting 0), `textual` (importable), `pydantic`
(importable, probed via `importlib.util.find_spec` without importing it, so
the binary itself stays stdlib-only), and `snapshot` (when the binary runs
from a plugin cache snapshot that is not the newest version directory in the
cache; when the binary runs from a repository checkout, the check SHALL
report dev mode as `ok`). The verb SHALL mutate nothing.

#### Scenario: Healthy environment reports ok
- **WHEN** `shipd doctor` runs with python >= 3.9, git present, a resolvable
  config, gh authenticated, and the newest snapshot
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

#### Scenario: Missing pydantic only warns
- **WHEN** `shipd doctor` runs without `pydantic` importable, all required
  checks passing
- **THEN** a `warn pydantic — ` line names declared-pipeline validation as
  the only affected surface with a `pip install -r requirements.txt` hint
  and the exit code is `0`

#### Scenario: Stale snapshot warns
- **WHEN** `shipd doctor` runs from a cache snapshot directory that is not
  the newest version in the cache
- **THEN** a `warn snapshot — ` line names the newer version and the exit
  code is `0`
