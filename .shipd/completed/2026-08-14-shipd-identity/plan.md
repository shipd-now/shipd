# shipd-identity
Status: verified
Epic: shipd-port
Theme: spec-engine

## Idea

Give the ported plugin its own identity — marketplace `shipd`, plugin `s` — and
install it locally so the skills actually load and run as `/s:<name>`.

### Motivation

A namespace that parses is not a namespace Claude Code will load: the plugin
manifest, the marketplace manifest, and the settings entries are what make `/s:`
real, and the port tool cannot produce them because a bare `am` is deliberately
never substituted (`.shipd/epics/shipd-port/epic.md`, Decisions). Until this member
lands, shipd is a tree of code nothing invokes.

### Details

- Correct `plugins/s/.claude-plugin/plugin.json` to name the plugin `s` and carry
  a version one bump past shipd's current one.
- Correct `.claude-plugin/marketplace.json` to name the marketplace `shipd` with a
  single plugin `s` sourced from `./plugins/s`.
- Port `.claude/settings.json` with the statusline pointed at the `plugins/s/`
  path and `s@shipd` enabled.
- Register the marketplace and install the plugin locally, then confirm the
  skills load under `/s:` in a fresh session.

Affected capabilities: `shipd-port` (added). Impact: the shipd repo
(`.claude-plugin/marketplace.json`, `plugins/s/.claude-plugin/plugin.json`,
`.claude/settings.json`) and the local Claude Code plugin install.

### Non-goals

- No uninstall or aliasing of `s@shipd`. Both plugins coexist; shipd keeps
  working, which is the epic's central constraint.
- No agent-definition renaming beyond what the tool already did — `s:oracle`,
  `s:sub-agent`, and `s:validator` come from the token map, and this member only
  confirms they resolve.
- No brand prose in the manifest descriptions; member 5 owns the copy. This member
  sets only the machine-read identity fields.
- No publishing to any remote marketplace. The install is a local `directory`
  source, exactly as shipd's is.

## Implementation

- **The bare-`am` fields are the whole point of this member.** The token map
  never substitutes a bare `am`, so after the port the manifests still read
  `"name": "am"` — correct behavior from the tool, and precisely why identity is
  a separate member rather than a side effect. The fields to set by hand are:
  `marketplace.json` → `name: "shipd"`, its plugin entry's `name: "s"` and
  `source: "./plugins/s"`; `plugin.json` → `name: "s"`. Their `keywords` arrays
  likewise carry a bare `"am"` that must become `"s"`.

- **The version is read at run time, never hard-coded.** The executor reads
  `version` from shipd's `plugins/s/.claude-plugin/plugin.json` at the moment
  this member runs and writes that value with the patch component incremented.
  shipd stays in development while this epic is delivered, so a literal pinned
  at planning time would be stale or would collide. Rejected: resetting to
  `0.1.0` — it discards the version line's meaning and breaks the
  cache-snapshot-per-version discipline that carries over.

- **Settings mirror shipd's structure, retargeted.** `statusLine.command`
  becomes `bash plugins/s/integrations/statusline.sh`, `enabledPlugins` gains
  `s@shipd`, and `extraKnownMarketplaces` declares `shipd` as a `directory`
  source at `.`. As in shipd these entries are trust-gated and redundant next
  to a user-scope install; they are kept so another checkout can self-advertise.

- **Installation is verified by invocation, not by the manifest parsing.** The
  acceptance is that a fresh session lists the skills under `/s:` and that one of
  them runs a real engine script. A manifest can be syntactically perfect and
  still not load — wrong `source` path, an unbumped version, a stale cache
  snapshot — and only starting a session surfaces that.

- **The snapshot discipline transfers.** shipd's plugin will run from
  `~/.claude/plugins/cache/shipd/s/<version>/`, not from the repo, so every later
  change touching `plugins/s/` must bump `plugin.json` and refresh. This member
  establishes that fact; member 5 writes it into shipd's `AGENTS.md`.

Risk: two marketplaces both registered as `directory` sources, one per repo, with
similar plugin content. The distinguishing keys are the marketplace name and the
plugin name, which is why both must change together — a half-rename would give
two plugins claiming the same identity.
