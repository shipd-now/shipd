# shipd-install

### Requirement: One-command install script
id: install-script

A repo-root `install.sh` SHALL, when run on a machine with the `claude` CLI
and `python3` present: register the `shipd-now/shipd` GitHub marketplace via
`claude plugin marketplace add`, install the plugin via
`claude plugin install s@shipd`, write the version-independent `shipd`
launcher to `~/.local/bin/shipd` marked executable, and print a PATH hint
when `~/.local/bin` is not on the invoking PATH. If `claude` or `python3` is
missing, then the script SHALL exit nonzero with a single actionable error
line and change nothing. The script SHALL treat an already-registered
marketplace or already-installed plugin as success (idempotent re-run) and
SHALL download nothing itself beyond what the `claude` CLI performs.

#### Scenario: Fresh install performs both claude steps and writes the launcher
- **WHEN** `install.sh` runs with a stub `claude` on PATH and a temp HOME
- **THEN** `claude plugin marketplace add shipd-now/shipd` and
  `claude plugin install s@shipd` are invoked, and an executable
  `~/.local/bin/shipd` exists afterwards

#### Scenario: Missing claude CLI aborts cleanly
- **WHEN** `install.sh` runs with no `claude` on PATH
- **THEN** it exits nonzero with an actionable error and writes no launcher

#### Scenario: Re-run is idempotent
- **WHEN** `install.sh` runs a second time with the marketplace and plugin
  already present
- **THEN** it exits 0 and the launcher is still in place

### Requirement: Version-independent launcher
id: cache-launcher

The installed `shipd` launcher SHALL resolve the newest version directory
under the plugin cache root (`~/.claude/plugins/cache/shipd/s/`, overridable
via the `SHIPD_PLUGIN_CACHE` environment variable) by numeric dotted-version
ordering — ignoring non-version directory names — and SHALL replace its
process with that snapshot's `bin/shipd`, passing all arguments through
verbatim so the snapshot binary's output and exit code are the launcher's
own. If no installed snapshot exists, then the launcher SHALL exit nonzero
with one error line naming `claude plugin install s@shipd` as the fix. A
newly installed plugin version SHALL be picked up with no change to the
launcher.

#### Scenario: Newest snapshot wins numerically
- **GIVEN** cache version directories `0.6.9` and `0.6.10`
- **WHEN** the launcher runs
- **THEN** it executes `0.6.10/bin/shipd` (a lexicographic order would pick
  `0.6.9`)

#### Scenario: Arguments and exit code pass through
- **WHEN** the launcher runs `shipd --version` against a stub snapshot
- **THEN** the stub's stdout and exit code are the launcher's own

#### Scenario: Missing cache is an actionable error
- **WHEN** the launcher runs with an empty or absent cache root
- **THEN** it exits nonzero with an error naming
  `claude plugin install s@shipd`

### Requirement: Install-mode documentation
id: install-mode-docs

The repository `README.md` SHALL lead its installation documentation with
install mode — the advertised one-liner
`curl -fsSL https://shipd.now/install | sh`, with the two `claude plugin`
commands and the raw GitHub `install.sh` URL documented as equivalents, and
the launcher's PATH location — and
SHALL retain the existing clone-and-symlink instructions as an explicitly
labeled dev mode.

#### Scenario: Install mode leads
- **WHEN** a reader reaches the README's installation section
- **THEN** the `https://shipd.now/install` one-liner appears first, the raw
  GitHub URL and the two `claude plugin` commands appear as equivalents,
  and both modes are labeled

#### Scenario: Dev mode retained
- **WHEN** a reader follows dev mode
- **THEN** the checkout-symlink guidance (never symlinking the versioned
  cache path) is still present
