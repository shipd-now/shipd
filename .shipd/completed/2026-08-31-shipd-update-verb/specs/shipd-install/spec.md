## MODIFIED Requirements

### Requirement: Install-mode documentation
id: install-mode-docs
base: fc3502ae30e6

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
`/reload-plugins`), and both `shipd update` — the one-command manual upgrade,
with `shipd update --check` naming the report-only form — and
`claude plugin update s@shipd` as the manual
fallbacks. The README's `shipd` CLI verb listing SHALL name `update` among
the verbs. The installation documentation SHALL additionally document a
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

#### Scenario: The update verb is documented as the manual upgrade
- **WHEN** a reader finishes the install-mode section
- **THEN** `shipd update` is named as the one-command manual upgrade,
  `shipd update --check` as its report-only form, and the README's `shipd`
  CLI verb listing includes `update`

#### Scenario: Per-repo mode is documented
- **WHEN** a reader reaches the installation documentation's per-repo mode
- **THEN** it is explicitly labeled, names `shipd vendor add` and the four
  written surfaces, describes the clone-then-trust collaborator flow as
  registry-free, and names re-running `shipd vendor add` as the refresh
  path and `shipd vendor remove` as the removal path
