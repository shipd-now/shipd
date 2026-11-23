## MODIFIED Requirements

### Requirement: Install-mode documentation
id: install-mode-docs
base: ef32c3bb4f4a

The repository `README.md` SHALL lead its installation documentation with
install mode — the advertised one-liner
`curl -fsSL https://shipd.now/install | sh`, with the two `claude plugin`
commands and the raw GitHub `install.sh` URL documented as equivalents, and
the launcher's PATH location — and
SHALL retain the existing clone-and-symlink instructions as an explicitly
labeled dev mode. The install-mode documentation, and the install page
`docs/install.md`, SHALL document enabling Claude Code's marketplace
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

The install step of `docs/getting-started.md` SHALL show the one-command
installer, SHALL link `install.md`, and SHALL NOT restate the auto-update
or upgrade instructions.

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
- **WHEN** a reader finishes the install-mode section or `docs/install.md`
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

#### Scenario: The first-change guide defers to the install page
- **WHEN** a reader reaches the install step of `docs/getting-started.md`
- **THEN** it shows `curl -fsSL https://shipd.now/install | sh`, links
  `install.md`, and contains neither `autoUpdate` nor `shipd update`

## ADDED Requirements

### Requirement: Install user documentation
id: install-user-docs

The repository SHALL provide `docs/install.md`, titled "Install", as the main
page for `shipd install`, `shipd update`, and `shipd vendor`, and as the one
docs page that owns installation. The page SHALL carry
`<!-- doc-type: how-to -->` as its first line, total 150 lines or fewer, and
pass `docs_lint.py`.

The page SHALL follow the main-page shape: opening paragraphs saying what
installing shipd sets up, then `## When to use it`, `## How to run it`, and a
closing `## Reference`, in that order. `## When to use it` SHALL say which of
the three modes fits: install mode for one person, per-repo mode for a
repository's collaborators, dev mode for work on shipd itself.
`## How to run it` SHALL hold these level-3 sections, in order:

- `### Install for yourself` — the `claude` and `python3` prerequisites; the
  one-liner `curl -fsSL https://shipd.now/install | sh`; the two
  `claude plugin` commands as its by-hand equivalent; the launcher at
  `~/.local/bin/shipd` and the PATH line; that a re-run is safe.
- `### Pick your harnesses` — that a terminal install finishes with
  `shipd install`, a multi-select saved to `~/.shipd/harnesses.json`; the
  closing setup check; that a headless run writes nothing and exits 0; the
  re-run path; and a link to `harnesses.md` for `shipd harness add`.
- `### Keep it up to date` — the `/plugin` auto-update toggle and the
  `"autoUpdate": true` settings entry that keeps its `source`; that an update
  loads at the next session start or after `/reload-plugins`;
  `shipd update`, `shipd update --check`, and `claude plugin update s@shipd`.
- `### Vendor shipd into a repository` — `shipd vendor add`, the
  clone-then-trust collaborator flow with no network, the bare `shipd vendor`
  report and its four states, refresh by re-running `add`, and
  `shipd vendor remove`, which never touches spec content.
- `### Work on shipd itself` — registering the checkout as a directory
  marketplace, and never symlinking the versioned cache path.

`## Reference` SHALL hold a table of the four surfaces `shipd vendor add`
writes and a table of the three verbs with their forms. The page SHALL link
`getting-started.md`, `doctor.md`, and `harnesses.md`, and SHALL carry no
mermaid fence. Every command SHALL be a `shipd` verb, a `claude` command, or
a shell line the reader runs; the page SHALL name no engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/install.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the three modes and the upgrade path
- **WHEN** `docs/install.md` is inspected
- **THEN** it holds the one-liner, `shipd install`, `autoUpdate`,
  `shipd update --check`, `shipd vendor add`, `shipd vendor remove`, and the
  rule against symlinking the versioned cache path

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py docs/install.md` runs
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer,
  the file holds no mermaid fence, and every relative link resolves
