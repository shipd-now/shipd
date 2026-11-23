## MODIFIED Requirements

### Requirement: Install-mode documentation
id: install-mode-docs
base: 960b2216592f

The repository `README.md` SHALL lead its `## Install` section with install
mode: the advertised one-liner `curl -fsSL https://shipd.now/install | sh`,
with the raw GitHub `install.sh` URL and the two `claude plugin` commands
documented as equivalents, and the launcher's PATH location. The section
SHALL give `shipd doctor` as the check and SHALL link `docs/install.md` for
everything else. The README SHALL NOT restate auto-update, `shipd update`,
per-repo mode, or dev mode, with exactly three exceptions it MAY keep: the
sentence that a repository vendoring shipd holds a directly runnable
`.shipd/plugin/s/bin/shipd`; the in-session `/plugin marketplace add
<path-to-your-checkout>` and `/plugin install s@shipd` steps; and the
sentence that the plugin is the engine's distribution vehicle for every
harness. The README SHALL carry no `shipd` CLI verb listing.

The install page `docs/install.md` SHALL document enabling Claude Code's
marketplace auto-update for `shipd` (the `/plugin` toggle and the
`"autoUpdate": true` settings entry), the apply semantics (next session
start, or `/reload-plugins`), and both `shipd update` — the one-command
manual upgrade, with `shipd update --check` naming the report-only form —
and `claude plugin update s@shipd` as the manual fallbacks. It SHALL
document a per-repo mode covering `shipd vendor add` as the entry command,
the four surfaces it writes (the vendored `<content-dir>/plugin/` tree, the
marketplace manifest, the `.claude/settings.json` keys, and the content
scaffold), the collaborator flow — clone, accept the folder trust dialog,
and the plugin installs from the clone itself with no network or package
registry — refresh by re-running `shipd vendor add` after a plugin update,
and removal via `shipd vendor remove`. It SHALL keep the clone-and-symlink
instructions as dev mode, with the rule against symlinking the versioned
cache path. `install-user-docs` fixes that page's headings.

The install step of `docs/getting-started.md` SHALL show the one-command
installer, SHALL link `install.md`, and SHALL NOT restate the auto-update
or upgrade instructions.

#### Scenario: Install mode leads
- **WHEN** a reader reaches the README's `## Install` section
- **THEN** the `https://shipd.now/install` one-liner appears first, and the
  raw GitHub URL and the two `claude plugin` commands appear as equivalents

#### Scenario: Dev mode retained
- **WHEN** a reader follows dev mode on `docs/install.md`
- **THEN** the checkout-symlink guidance (never symlinking the versioned
  cache path) is still present

#### Scenario: Auto-update is documented
- **WHEN** a reader finishes `docs/install.md`
- **THEN** the auto-update enable step, its apply semantics, and the
  manual `claude plugin update s@shipd` fallback are documented

#### Scenario: The update verb is documented as the manual upgrade
- **WHEN** a reader finishes `docs/install.md`
- **THEN** `shipd update` is named as the one-command manual upgrade and
  `shipd update --check` as its report-only form

#### Scenario: Per-repo mode is documented
- **WHEN** a reader reaches the per-repo section of `docs/install.md`
- **THEN** it names `shipd vendor add` and the four written surfaces,
  describes the clone-then-trust collaborator flow as registry-free, and
  names re-running `shipd vendor add` as the refresh path and
  `shipd vendor remove` as the removal path

#### Scenario: The first-change guide defers to the install page
- **WHEN** a reader reaches the install step of `docs/getting-started.md`
- **THEN** it shows `curl -fsSL https://shipd.now/install | sh`, links
  `install.md`, and contains neither `autoUpdate` nor `shipd update`

#### Scenario: README defers to the install page
- **WHEN** `README.md` is searched for `autoUpdate`, `shipd update`,
  `shipd vendor`, and `ln -s`
- **THEN** no line matches, and its `## Install` section links
  `docs/install.md` and shows `shipd doctor`

#### Scenario: The README keeps only the three permitted facts
- **WHEN** `README.md` is read outside its `## Install` section
- **THEN** it may name the runnable `.shipd/plugin/s/bin/shipd`, the two
  in-session `/plugin` steps, and the distribution-vehicle sentence, and it
  names no `shipd vendor` command, no `shipd update` command, no auto-update
  setting, and no symlink instruction
