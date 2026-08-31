## MODIFIED Requirements

### Requirement: Doctor preflight verb
id: doctor-verb
base: f1ca8e839454

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
or an unknown preset), with `pipeline` reported
directly after `config`. The warning checks SHALL be: `gh` (present on
PATH and `gh auth status` exiting 0), `difft` (present on PATH, probed
via `shutil.which` so the binary stays stdlib-only, reported directly
after `gh`; the warning detail SHALL name the semantic review's
text-engine degradation as the affected surface and the tiered
`semdiff doctor --fix` installer as the remedy, and a present binary
SHALL report `ok`), `textual` (importable, probed via
`importlib.util.find_spec` without importing it, so the binary itself
stays stdlib-only), `snapshot` (when the binary
runs from a plugin cache snapshot that is not the newest version
directory in the cache; when the binary runs from a repository checkout,
the check SHALL report dev mode as `ok`), and `statusline` (when the
Claude Code user settings file — default `~/.claude/settings.json` — is
absent or carries no `statusLine` key, probed read-only; the warning
detail SHALL name `shipd statusline install` as the remedy, and a
present registration SHALL report `ok`). The `pip install` hint on the
`textual` detail SHALL name `-r requirements.txt` when a
`requirements.txt` exists at the working-directory root, and the pinned
package specifier (`'textual>=8.2.8,<9'`)
otherwise — a vendored per-repo install has no checkout to `-r` from.
Where the running interpreter is externally managed (PEP 668) — probed
read-only via the `EXTERNALLY-MANAGED` marker file in the interpreter's
stdlib directory resolved through `sysconfig` — the hint SHALL prepend
`--user --break-system-packages` to either form, so the printed command
is runnable by the interpreter that printed it; on an unmanaged
interpreter both hint forms SHALL remain unchanged. The verb SHALL report
no check for a package the engine does not depend on, so it SHALL report
no `pydantic` check and SHALL never escalate a dependency finding from a
declared `autonomous-pipeline`. The verb SHALL mutate nothing.

#### Scenario: Healthy environment reports ok
- **WHEN** `shipd doctor` runs with python >= 3.9, git present, a resolvable
  config, a resolvable pipeline, gh authenticated, difft present, and the
  newest snapshot
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

#### Scenario: Missing difft only warns
- **WHEN** `shipd doctor` runs with no `difft` on PATH, all required checks
  passing
- **THEN** a `warn difft — ` line names the review's text-engine degradation
  and the `semdiff doctor --fix` remedy, and the exit code is `0`

#### Scenario: Present difft reports ok
- **WHEN** `shipd doctor` runs with `difft` on PATH
- **THEN** the `difft` check line begins `ok`

#### Scenario: Missing textual only warns
- **WHEN** `shipd doctor` runs without `textual` importable, all required
  checks passing
- **THEN** a `warn textual — ` line names the board as the only affected
  surface and the exit code is `0`

#### Scenario: No pydantic check is reported
- **WHEN** `shipd doctor` runs in any repo, with or without a declared
  `autonomous-pipeline` and with `pydantic` unimportable
- **THEN** no output line names `pydantic`, and neither the exit code nor
  the `pipeline` line's level depends on whether pydantic is importable

#### Scenario: Missing requirements.txt pins the hint
- **WHEN** `shipd doctor` runs without `textual` importable on an unmanaged
  interpreter in a repo whose root carries no `requirements.txt`
- **THEN** the `textual` detail's hint names `pip install
  'textual>=8.2.8,<9'` and never `-r requirements.txt`

#### Scenario: Externally managed interpreter flags the checkout hint
- **WHEN** `shipd doctor` runs without `textual` importable on an
  externally managed interpreter (the `EXTERNALLY-MANAGED` marker present)
  in a repo with a `requirements.txt` at its root
- **THEN** the `textual` detail's hint names
  `pip install --user --break-system-packages -r requirements.txt`

#### Scenario: Externally managed interpreter flags the pinned hint
- **WHEN** `shipd doctor` runs without `textual` importable on an externally
  managed interpreter in a repo whose root carries no `requirements.txt`
- **THEN** the `textual` detail's hint names
  `pip install --user --break-system-packages 'textual>=8.2.8,<9'`

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
  that cannot resolve — malformed entries or an unknown preset
- **THEN** a `fail pipeline — ` line carries the resolver's own error line
  and the exit code is `1`

#### Scenario: A declared pipeline resolves with no third-party package
- **WHEN** `shipd doctor` runs with `pydantic` unimportable in a repo
  declaring an `autonomous-pipeline` list, and again declaring the `eco`
  preset
- **THEN** the `pipeline` line is `ok` in both runs and the exit code is
  `0`
