# public-install
Status: verified
Epic: shipd-dx

## Idea

One-command consumer install: a repo-root `install.sh` that registers the
GitHub marketplace, installs the plugin, and puts a version-independent
`shipd` launcher on PATH — plus a README install section split into install
mode and dev mode.

### Motivation

Installing shipd today means cloning the repo, registering a local directory
marketplace, and hand-symlinking `plugins/s/bin/shipd` onto PATH — a path
that assumes the consumer is the author and breaks on every plugin version
bump; the `shipd-dx` epic makes the one-command GitHub install its first
success criterion.

### Details

- `install.sh` (repo root, POSIX sh): verify `claude` and `python3` exist;
  `claude plugin marketplace add shipd-now/shipd` and
  `claude plugin install s@shipd`, both tolerating already-present state;
  write the launcher to `~/.local/bin/shipd` (creating the directory),
  `chmod +x` it, and print a PATH hint when `~/.local/bin` is not on PATH.
  It downloads nothing itself.
- The launcher is a small python3 script: it resolves the newest
  `<version>` directory under `~/.claude/plugins/cache/shipd/s/` with a
  numeric version-aware sort and `execv`s that snapshot's `bin/shipd` with
  all arguments; a missing cache prints an actionable error naming
  `claude plugin install s@shipd`.
- README: the install section leads with install mode — the advertised
  one-liner `curl -fsSL https://shipd.now/install | sh` (the canonical
  domain form) with the two `claude plugin` commands and the raw GitHub URL
  as the documented equivalent/fallback; the existing clone +
  checkout-symlink text remains as dev mode.

Affected capabilities: `shipd-install` (added). Impact: `install.sh` (new,
repo root), `README.md`, `plugins/s/skills/build/tests/test_install.py`
(new). No `plugins/s/` code changes and no version bump. No new
dependencies.

### Non-goals

- No in-repo hosting of the shipd.now domain (no CNAME, no Pages): the
  `shipd.now/install` URL is a redirect the operator wires at the DNS/host
  to the repo's raw `install.sh` — recorded here, implemented outside the
  repo.

- No package managers (Homebrew/Scoop/Winget/npm) and no GoReleaser — epic
  non-goal.
- No uninstall verb and no self-update logic — `claude plugin update
  s@shipd` remains the update path (the launcher picks new snapshots up
  automatically).
- No change to `plugins/s/bin/shipd` itself — it already resolves its
  scripts relative to its own location and runs from a snapshot unchanged.
- No modification of the dev-mode workflow (local directory marketplace,
  checkout symlink).

## Implementation

- **The launcher is python3, not shell.** Newest-version selection needs a
  numeric version sort; `sort -V` is present on GNU coreutils and current
  macOS but not guaranteed on older BSD userlands, while python3 is already
  a hard prerequisite of the engine the launcher fronts. The launcher sorts
  version directory names by their dotted-integer tuple (non-numeric names
  ignored) and `os.execv`s `<newest>/bin/shipd`. Rejected: a symlink updated
  by the installer — stale after every `claude plugin update`, which is the
  exact failure the epic names.
- **Cache layout premise (observed):** plugin content sits directly under
  `~/.claude/plugins/cache/shipd/s/<version>/` (`bin/`, `skills/`, …);
  `bin/shipd` works from there because it resolves relative to its own file.
  The cache root is overridable via `SHIPD_PLUGIN_CACHE` for tests.
- **The advertised install command is the canonical domain form**
  (`curl -fsSL https://shipd.now/install | sh`), decided by the user during
  epic delivery: the domain reads as the product, the raw GitHub URL as
  plumbing. `shipd.now/install` is a thin redirect to the repo's raw
  `install.sh`, wired once at the operator's DNS/hosting provider — the repo
  ships the script and documents both URLs, so the docs are correct the
  moment the redirect exists and the raw form always works. Rejected:
  in-repo GitHub Pages serving the domain — it starts the shipd.now web
  surface both epics explicitly deferred.
- **`install.sh` stays POSIX sh** (constitution's shell precedent: bash 3.2
  compatibility, no arrays); the launcher body is written from a quoted
  heredoc so no interpolation surprises. Marketplace/install steps run
  `claude` and treat "already exists"/"already installed" outcomes as
  success (idempotent re-run), verified in tests through a stub `claude`.
- **Verified CLI premises:** `claude plugin marketplace add <source>` and
  `claude plugin install <plugin>` are the syntaxes the installed `claude`
  2.1.224 documents (`--help` observed); the installer passes
  `shipd-now/shipd` and `s@shipd` respectively.
- **Tests** (`test_install.py`, following `test_statusline.py`'s pattern of
  testing a repo file from the plugin test suite): run `install.sh` with a
  temp `HOME`, a stub `claude` on PATH recording its argv, and a fake cache;
  assert the two claude invocations, the launcher's existence and
  executability, the PATH hint, and idempotent re-run. Launcher tests: fake
  cache with `0.6.9` and `0.6.10` proves numeric ordering (lexicographic
  would pick `0.6.9`); missing cache exits nonzero with the actionable
  error; `execv` target asserted via a stub `bin/shipd`.
- Risk: the cache path is a Claude Code internal that could move; guard: the
  launcher's error message names the override env var and the README's dev
  mode remains a full fallback.
