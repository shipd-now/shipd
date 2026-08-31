# shipd-update-verb
Status: verified

## Idea

Add a `shipd update` verb that reports whether a newer plugin version is
published and, unless `--check` is given, installs it.

### Motivation

Upgrading shipd today means remembering two Claude Code CLI incantations
(`claude plugin marketplace update shipd`, `claude plugin update s@shipd`) and
comparing versions by eye; the `shipd` binary — the one command a user already
has on their PATH — offers no way to learn that an update exists.

### Details

- Add `update` to the binary's curated verbs, in-binary like `doctor` /
  `install` (it drives subprocesses and prints its own report, so it must not
  `execv`).
- Resolve the **installed** version as the newest snapshot under the plugin
  cache root and the **available** version from the registered `shipd`
  marketplace's own copy of the plugin manifest, after refreshing that
  marketplace through the `claude` CLI.
- When available > installed: run `claude plugin update s@shipd`, then report
  the resulting version and the restart-to-apply note. With `--check`, report
  what an update would do and change nothing.
- Document the verb in the README's install-mode auto-update guidance and the
  CLI verb listing.

Affected capabilities: `shipd-cli` (modified `cli-dispatch`, added
`cli-update`), `shipd-install` (modified `install-mode-docs`). Impact:
`plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_shipd_cli.py`,
`README.md`, `plugins/s/.claude-plugin/plugin.json`. No new dependencies —
stdlib plus `subprocess` calls to the already-required `claude` CLI.

### Non-goals

- No background or on-every-invocation update check — `update` is explicit.
- No GitHub API or raw-network access from the binary; every fetch is the
  `claude` CLI's, exactly as `install.sh` already delegates.
- No changes to `install.sh`, the launcher, or the `doctor` `snapshot` check
  (which reports an already-downloaded-but-not-loaded snapshot, a different
  condition).
- No `--json` mode; `update` is not one of the banner's read verbs.

## Implementation

**Placement.** `cmd_update` lives in `plugins/s/bin/shipd` alongside
`cmd_doctor` / `cmd_install`, dispatched from `main` before the `VERB_TABLE`
lookup. Rejected: an engine script under `skills/build/scripts/` — the
constitution forbids network access there, and the verb operates on the user's
plugin cache, not the spec library.

**Version resolution.** Two sides, both read locally:

- *Installed*: the newest directory under the cache root — `$SHIPD_PLUGIN_CACHE`
  when set, else `~/.claude/plugins/cache/shipd/s` — selected with the existing
  `VERSION_DIR_RE` / `_version_key` / `_subdirs` helpers, the same rule the
  launcher and `check_snapshot` already use.
- *Available*: `~/.claude/plugins/known_marketplaces.json` → the `shipd` entry's
  `installLocation` → `<location>/.claude-plugin/marketplace.json` → the
  `plugins` entry named `s` → its relative-path `source` →
  `<location>/<source>/.claude-plugin/plugin.json` → `version`. Verified
  against this machine: the registration carries
  `installLocation` and the manifest declares `"source": "./plugins/s"`.
  Rejected: querying the GitHub API — it needs auth, misses the directory-source
  (dev) installs, and duplicates what the marketplace clone already holds.

**Freshness.** Before reading the available version, run
`claude plugin marketplace update shipd` (verified present:
`claude plugin marketplace --help` lists `update [options] [name]`) with a
`MARKETPLACE_TIMEOUT = 120` second bound, output captured. A nonzero exit or a
timeout is a hard `Error:` and exit 1 — reporting "up to date" from a stale
clone would be worse than reporting that the check could not run.

**Interfaces** (all in `plugins/s/bin/shipd`):

```python
CLAUDE_MARKETPLACE = "shipd"      # registered marketplace name
CLAUDE_PLUGIN_ID = "s@shipd"      # installed plugin id
CLAUDE_PLUGIN_NAME = "s"          # entry name inside the marketplace manifest
MARKETPLACE_TIMEOUT = 120

class UpdateError(Exception): ...          # message is the Error: reason

def _plugins_home():                        # Path(~/.claude/plugins), $HOME-relative
def _cache_root():                          # $SHIPD_PLUGIN_CACHE or <home>/cache/shipd/s
def newest_installed(cache_root):           # newest version string, or None
def marketplace_location(plugins_home):     # installLocation string, or None
def marketplace_version(location):          # version string; raises UpdateError
def _claude_run(args, timeout=None):        # subprocess.run(["claude", *args], capture_output=True, text=True)
def cmd_update(args):                       # argparse over [--check]; returns 0/1/2
```

`_claude_run` is the single subprocess seam, mirroring `_gh_run` in the doctor
path, so tests stub it instead of shelling out. `newest_installed`,
`marketplace_location`, and `marketplace_version` take their roots as arguments
so tests point them at temp directories.

**Report shape** (stdout, one line per fact, no color):

- up to date: `up to date — 0.6.165 is the newest published version`
- `--check` with an update: `update available: 0.6.165 -> 0.6.170 — run \`shipd update\` to apply`
- applying: `updating s@shipd: 0.6.165 -> 0.6.170` before the apply, then
  `updated to 0.6.170 — start a new session to load it` after it.

The apply step runs `claude plugin update s@shipd` through `_claude_run`; its
captured stdout is printed so the CLI's own progress reaches the user, and a
nonzero exit is an `Error:` with exit 1. After a zero exit the newest installed
snapshot is re-resolved and *that* version is what the report names — the
binary states what the cache actually holds, never what it hoped for.

**Errors** (each a single `Error:` line on stderr, exit 1, per
`cli-conventions` `error-output-convention`): `claude` absent from PATH; the
`shipd` marketplace not registered (names `claude plugin marketplace add
shipd-now/shipd`); the marketplace refresh failing or timing out; the
marketplace manifest missing, unparseable, carrying no `s` entry, or carrying a
non-relative-path `source`; no installed snapshot under the cache root (names
`claude plugin install s@shipd`, mirroring the launcher's wording). An
unrecognized flag is argparse's usage error, exit 2.

**Risk.** A dev-mode install registers the marketplace as a `directory` source
pointing at a checkout, so `available` is whatever that checkout declares and
`update` may report "up to date" against uncommitted work. That is the honest
answer for that install and needs no special case; the comparison is `>`, so a
checkout ahead of the cache still reads as an available update and a checkout
behind it reads as up to date.

**Version bump.** `plugins/s/.claude-plugin/plugin.json` 0.6.163 -> **0.6.165**
(0.6.164 is claimed by a change in flight elsewhere), per AGENTS.md's rule that
every `plugins/s/` change bumps the plugin version in the same PR.
