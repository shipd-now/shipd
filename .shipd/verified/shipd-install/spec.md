# shipd-install

### Requirement: One-command install script
id: install-script

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
launch), while never editing any settings file itself. Where a controlling
terminal is available (`/dev/tty` opens read-write), the script SHALL then
run the just-written launcher's `install` verb with its input and output
bound to `/dev/tty`, fail-soft: a nonzero exit from that step SHALL print
one note and SHALL NOT fail the installer. Where no controlling terminal is
available, the script SHALL skip that step and its output SHALL remain
unchanged. If `claude` or `python3` is
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

#### Scenario: Headless runs skip the interactive finish unchanged
- **WHEN** `install.sh` runs to success with no usable `/dev/tty`
- **THEN** the launcher's `install` verb is not invoked, the script exits
  0, and the output matches the pre-existing success output

#### Scenario: A failing interactive finish never fails the installer
- **WHEN** the guarded step runs and the launcher's `install` verb exits
  nonzero
- **THEN** the script prints one note about the skipped finish and still
  exits 0

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
labeled dev mode. The install-mode documentation, and the quickstart's
install step, SHALL document enabling Claude Code's marketplace
auto-update for `shipd` (the `/plugin` toggle and the `"autoUpdate": true`
settings entry), the apply semantics (next session start, or
`/reload-plugins`), and `claude plugin update s@shipd` as the manual
fallback. The installation documentation SHALL additionally document a
per-repo mode, explicitly labeled, covering: `shipd vendor add` as the
entry command, the four surfaces it writes (the vendored
`<content-dir>/plugin/` tree, the marketplace manifest, the
`.claude/settings.json` keys, and the content scaffold), the collaborator
flow — clone, accept the folder trust dialog, and the plugin installs from
the clone itself with no network or package registry — refresh by
re-running `shipd vendor add` after a plugin update, and removal via
`shipd vendor remove`.

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

#### Scenario: Per-repo mode is documented
- **WHEN** a reader reaches the installation documentation's per-repo mode
- **THEN** it is explicitly labeled, names `shipd vendor add` and the four
  written surfaces, describes the clone-then-trust collaborator flow as
  registry-free, and names re-running `shipd vendor add` as the refresh
  path and `shipd vendor remove` as the removal path

### Requirement: Installer brand mark
id: installer-brand-mark

After a successful install, `install.sh` SHALL print its completion line with the ☕ brand mark directly before the product name — `Installed the ☕ shipd launcher at <path>` — while the PATH hint, the auto-update notice, and every failure path stay otherwise unchanged.

#### Scenario: Success line is branded
- **WHEN** `install.sh` completes successfully
- **THEN** stdout carries a completion line containing `☕ shipd launcher`

#### Scenario: Aborts stay unbranded
- **WHEN** `install.sh` aborts on a missing prerequisite
- **THEN** its output carries no `☕` mark
