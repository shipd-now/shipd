## MODIFIED Requirements

### Requirement: One-command install script
id: install-script
base: 25861412bc0d

A repo-root `install.sh` SHALL, when run on a machine with the `claude` CLI
and `python3` present: register the `shipd-now/shipd` GitHub marketplace via
`claude plugin marketplace add`, install the plugin via
`claude plugin install s@shipd`, write the version-independent `shipd`
launcher to `~/.local/bin/shipd` marked executable, and print a PATH hint
when `~/.local/bin` is not on the invoking PATH. After a successful
install, the script SHALL print an auto-update notice naming the
per-marketplace enable surfaces — the `/plugin` → Marketplaces toggle for
`shipd` and the `"autoUpdate": true` settings entry — and the apply
semantics (updates land after session start and activate at the next
launch), while never editing any settings file itself. If `claude` or
`python3` is
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

#### Scenario: Success prints the auto-update notice
- **WHEN** `install.sh` completes successfully
- **THEN** stdout carries the auto-update notice naming the `/plugin`
  marketplace toggle and the `"autoUpdate": true` settings alternative,
  and no settings file was created or modified

#### Scenario: Aborts print no auto-update notice
- **WHEN** `install.sh` aborts on a missing prerequisite
- **THEN** the auto-update notice is absent from the output

### Requirement: Install-mode documentation
id: install-mode-docs
base: 41b2661411e7

The repository `README.md` SHALL lead its installation documentation with
install mode — the advertised one-liner
`curl -fsSL https://shipd.now/install | sh`, with the two `claude plugin`
commands and the raw GitHub `install.sh` URL documented as equivalents, and
the launcher's PATH location — and
SHALL retain the existing clone-and-symlink instructions as an explicitly
labeled dev mode. The install-mode documentation, and the quickstart's
install step, SHALL document enabling Claude Code's marketplace
auto-update for `shipd` (the `/plugin` toggle and the `"autoUpdate": true`
settings entry), the apply semantics (next session start, or
`/reload-plugins`), and `claude plugin update s@shipd` as the manual
fallback.

#### Scenario: Install mode leads
- **WHEN** a reader reaches the README's installation section
- **THEN** the `https://shipd.now/install` one-liner appears first, the raw
  GitHub URL and the two `claude plugin` commands appear as equivalents,
  and both modes are labeled

#### Scenario: Dev mode retained
- **WHEN** a reader follows dev mode
- **THEN** the checkout-symlink guidance (never symlinking the versioned
  cache path) is still present

#### Scenario: Auto-update is documented
- **WHEN** a reader finishes the install-mode section or the quickstart's
  install step
- **THEN** the auto-update enable step, its apply semantics, and the
  manual `claude plugin update s@shipd` fallback are documented
