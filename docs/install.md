<!-- doc-type: how-to -->

# Install

Installing shipd sets up two things: the `s` plugin in Claude Code, and the
`shipd` launcher on your PATH. The plugin runs every `/s:` command. The
launcher runs the `shipd` CLI from the newest installed plugin snapshot.

After the install, follow [Your first change](getting-started.md) to run one
change end to end.

## When to use it

- **Install mode** installs shipd for one person, on one machine.
- **Per-repo mode** vendors shipd into a repository, so every collaborator who
  clones it gets the same shipd.
- **Dev mode** runs shipd from a checkout, for work on shipd itself.

## How to run it

### Install for yourself

The installer needs `claude` and `python3` on your PATH. Run it:

```bash
curl -fsSL https://shipd.now/install | sh
```

The installer downloads nothing itself. It registers the marketplace and
installs the plugin through the Claude Code CLI. These two commands do the same
by hand:

```bash
claude plugin marketplace add shipd-now/shipd
claude plugin install s@shipd
```

The installer then writes the launcher to `~/.local/bin/shipd`. When that
directory is not on your PATH, it prints the line to add to your shell profile:
`export PATH="$HOME/.local/bin:$PATH"`. A re-run is safe: an existing
marketplace or plugin counts as success.

### Pick your harnesses

On a terminal, the installer finishes by running `shipd install`. That command
opens a multi-select over the registry's fifteen harnesses. It saves your
selection to `~/.shipd/harnesses.json`. It then generates the `shipd` command
files for each selected harness that has a user-global command directory.

A confirmed finish closes with the setup check, on one progress line. The check
installs missing local tooling without asking. It then lists only the problems
that remain, each with its fix. [Doctor](doctor.md) owns the full check list.

A headless run, such as CI, prints a short note, writes nothing, and exits 0.
An aborted picker also writes nothing. Re-run `shipd install` at any time to
reopen the selection, preloaded from the record.

A harness with only a repo-level surface needs `shipd harness add` instead.
See [Harnesses](harnesses.md).

### Keep it up to date

Claude Code turns auto-update off by default for third-party marketplaces such
as `shipd`. Turn it on once, in one of two ways:

- In a session, open `/plugin`, then **Marketplaces**, then `shipd`, and toggle
  auto-update on.
- In `~/.claude/settings.json`, add `"autoUpdate": true` to the `shipd` entry
  under `extraKnownMarketplaces`.

Keep the entry's existing `source` value. An entry without a `source` is
invalid, and Claude Code ignores it.

Claude Code fetches an update shortly after a session starts. The update loads
at the next session start, or at once after `/reload-plugins`.

To upgrade by hand, run:

```bash
shipd update
```

`shipd update` compares your installed snapshot with the published version and
installs a newer one. `shipd update --check` reports only and installs
nothing. `claude plugin update s@shipd` is the fallback manual upgrade.

### Vendor shipd into a repository

From a machine that already has shipd, run this once in the target repository:

```bash
shipd vendor add
```

The command writes the four surfaces in the [Reference](#reference) table, and
nothing else. Commit them.

A collaborator then clones the repository, opens Claude Code, and accepts the
folder trust dialog. The plugin installs from the clone, with no marketplace
registration, no package registry, and no network.

Bare `shipd vendor` reports each surface as `installed`, `stale`, `foreign`,
or `absent`, and changes nothing. To refresh after a plugin update, re-run
`shipd vendor add`. It is a no-op when nothing changed.

To remove the vendored plugin, run:

```bash
shipd vendor remove
```

`shipd vendor remove` deletes the vendored tree and the managed settings keys.
It never touches your spec content under `verified/`, `planned/`, or
`completed/`. Both `add` and `remove` refuse a vendored tree this install does
not own, unless you pass `--force`.

### Work on shipd itself

Clone the repository and register the checkout as a directory marketplace:

```bash
git clone https://github.com/shipd-now/shipd.git
cd shipd
claude plugin marketplace add "$PWD"
claude plugin install s@shipd
```

For the CLI, symlink `plugins/s/bin/shipd` from your checkout into a PATH
directory. Never symlink the versioned plugin cache. That path changes on every
version bump, so the link breaks at the next plugin update.

## Reference

The surfaces `shipd vendor add` writes, under the content directory
(`.shipd` by default):

| surface | what it holds |
| --- | --- |
| `.shipd/plugin/s/` | A byte-identical copy of the plugin you run |
| `.shipd/plugin/.claude-plugin/marketplace.json` | The `shipd` marketplace manifest |
| `.claude/settings.json` | The `enabledPlugins` and `extraKnownMarketplaces` keys |
| `.shipd/{verified,planned,completed}/` | The content scaffold, created only where missing |

The verbs this page owns:

| verb | what it does |
| --- | --- |
| `shipd install` | Pick harnesses and install their user-global commands |
| `shipd update [--check]` | Install a newer published plugin, or report only |
| `shipd vendor [add\|remove]` | Report, install, or remove a vendored plugin |
