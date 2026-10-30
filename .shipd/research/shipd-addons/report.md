# How shipd should support optional add-ons

> Prepared by the shipd research skill (/s:research).

## Summary

An add-on cannot appear under `/s:`. Claude Code namespaces every plugin skill
by the `name` in the plugin's own manifest [1][3]. Two enabled plugins may share
a manifest name, but Claude Code then silently drops one copy's hooks [3]. shipd's
`s` plugin relies on `SessionStart` and `SessionEnd` hooks [10], so a second
plugin named `s` could switch off shipd's own hooks. The nearest working form is
an add-on plugin with its own prefix, such as `/shipd-ax:ax`.

Claude Code already offers what optional add-ons need. Each add-on lives in its
own repository as a plugin in a marketplace [2]. A user adds that marketplace,
installs the add-on by `name@marketplace`, and can remove it again [2][5]. A
plugin declares the plugins it needs in a `dependencies` array, with an optional
semantic-version range [4]. A dependency in another marketplace installs only
when the add-on's marketplace allowlists that marketplace, or when the user has
already enabled it [4]. A private add-on repository works through the user's own
git credentials, because Claude Code holds no token of its own [5].

**Recommendation: each add-on is its own Claude Code plugin, named
`shipd-<topic>`, published from its own repository as its own marketplace. It
declares a dependency on `s` in the `shipd` marketplace.** For the first add-on
the plugin is `shipd-ax`, installed as `shipd-ax@shipd-ax`. Non-Claude harnesses
and shipd's generator stay out of scope until a second add-on needs them.

## Namespacing: why `/s:ax` is not reachable

- A plugin skill runs as `/<plugin-name>:<skill>`, and the prefix comes from the
  manifest's `name` [1][2]. The marketplace entry name is only the install and
  enable key [2][3].
- Claude Code compares manifest names to resolve conflicts. A `--plugin-dir`
  copy replaces a same-named installed plugin, and an installed plugin shadows a
  same-named skills-directory plugin [3].
- Two same-named plugins from different marketplaces both show as enabled, but
  "the hooks of one of them are left out", and the copy loaded first keeps the
  name [3]. shipd's `s` plugin runs its voice digest and store sync from
  `SessionStart` hooks [10], so sharing the name `s` risks disabling them.
- A user can't register two marketplaces with the same `name` [2][5]. An add-on
  marketplace therefore needs its own name too, such as `shipd-ax`.
- A standalone skill saved under `~/.claude/skills/` works without a plugin
  [1], which is how `ax-claude` installs today. It gets no updates from a
  marketplace and can't declare a dependency [1][4].

## Distribution: marketplaces, private repositories and updates

- A marketplace is a repository with `.claude-plugin/marketplace.json` listing
  each plugin's `name` and `source` [2]. A source can be a relative path, a
  `github` repository, a `git-subdir`, a URL, an archive, npm, or a command [2].
- A private marketplace works because Claude Code runs `git` with the user's
  stored credentials and prompts disabled. `marketplace.json` has no token
  field [5]. On GitHub, `gh auth login` then `gh auth setup-git` stores a
  credential that works [5].
- Setting `GITHUB_TOKEN` alone does not authenticate the background update
  check. A token works only through a credential helper [5].
- Background auto-update is off by default for every third-party marketplace,
  and `marketplace.json` cannot turn it on [3][5]. Each user enables it under
  `/plugin` **Marketplaces**, or an admin sets `autoUpdate` in managed
  settings [5].
- A user gets a new copy only when the plugin's computed version changes. A
  pinned `version` in `plugin.json` holds users on the cached copy until the
  string changes. With no `version` set, users track commits [3][5].
- A repository can register a marketplace for every collaborator with
  `claude plugin marketplace add … --scope project`, which writes the
  committed `.claude/settings.json` [5].
- Within one marketplace, a symlink from one plugin into a sibling plugin is
  copied into the cache [5]. That lets a meta-plugin reuse sibling skills, but
  only inside one repository, so it does not help a cross-repository add-on.

## Dependencies and version compatibility with `s`

- A plugin lists its dependencies in `plugin.json` as names, as
  `name@marketplace` strings, or as objects with `name`, `version` and
  `marketplace` [4].
- A dependency from another marketplace is not installed unless the root
  marketplace lists it in `allowCrossMarketplaceDependenciesOn`. If the
  dependency is declared in `plugin.json` without that entry, the add-on
  installs but then fails to load [4].
- The allowlist check is skipped when the user already has the dependency
  enabled at the same scope [4]. Any shipd user already has `s@shipd` enabled,
  but the add-on should still allowlist `shipd` for a clean first install.
- A version range resolves against git tags named `<plugin>--v<version>` on the
  repository that hosts the dependency [4]. shipd publishes no `s--v*` tags
  today; its only tag is `schema-v1.0.0` [9].
- For a relative-path plugin with no satisfying tag, Claude Code installs the
  marketplace's current copy and checks the range at load. An out-of-range copy
  leaves the dependent plugin disabled, and `claude plugin list` names the
  requirement [4]. `s` is a relative-path plugin in the `shipd` marketplace [9],
  so a range on `s` acts as a load-time compatibility check even before shipd
  tags releases.
- When several installed plugins constrain one dependency, Claude Code installs
  the highest version that satisfies every range. A non-overlapping range fails
  the install [4].

## Reach beyond Claude Code: shipd's harness registry

- shipd declares 15 harnesses in `harness_registry.py`, and maps Claude Code to
  the plugin that already provides its surface: `PLUGIN_PROVIDED =
  {"claude-code": "s@shipd"}` [7].
- `shipd harness add` renders command bodies from a single `harness/bodies/`
  tree inside the `s` plugin [8]. When the providing plugin is installed at
  user scope, the generator skips Claude Code and retires the files it owns
  there [8]. No hook exists for a second body tree, so an add-on cannot reach
  another harness through shipd today.
- A `SKILL.md` folder follows the open Agent Skills format: required `name` and
  `description`, optional scripts and references [6]. Anthropic developed the
  format and released it as an open standard that a growing set of agent
  products support [6]. An add-on written as plain Agent Skills therefore stays
  portable, even before shipd can generate it for other harnesses.

## The four candidate models

| Model | How it installs | Prefix | Verdict |
| --- | --- | --- | --- |
| A. Own plugin, own marketplace in the add-on repo | `marketplace add <repo>`, then `install shipd-ax@shipd-ax` [2] | `/shipd-ax:` | **Recommended.** Optional by construction, works for a private repo [5], declares `s` as a dependency [4] |
| B. Own plugin listed in shipd's marketplace | `install shipd-ax@shipd` from the marketplace users already have [2] | `/shipd-ax:` | Good for public add-ons later. A `github` entry pointing at a private repository fails for users without access [5] |
| C. A second plugin also named `s` | Its own marketplace [2] | `/s:` | **Rejected.** One copy's hooks are dropped silently [3], and shipd's hooks [10] could be the ones lost |
| D. Contributed into the `s` plugin | Part of every shipd install [9] | `/s:` | **Rejected for optional add-ons.** The add-on is never optional and adds to every user's skill listing [1] |

## Recommended model in practice

- **Repository layout.** The add-on repository holds
  `.claude-plugin/marketplace.json` (name `shipd-ax`) and
  `plugins/shipd-ax/.claude-plugin/plugin.json` (name `shipd-ax`). Its skills go
  under `plugins/shipd-ax/skills/<skill>/SKILL.md` [2]. The entry name and the
  manifest name stay equal, because a mismatch breaks installs [2].
- **Dependency.** `plugin.json` declares `{ "name": "s", "marketplace":
  "shipd", "version": "^0.6" }`, and `marketplace.json` sets
  `"allowCrossMarketplaceDependenciesOn": ["shipd"]` [4].
- **Versioning.** The add-on pins `version` and bumps it on each release [5].
  shipd starts tagging `s--v<version>` releases, for example with
  `claude plugin tag --push`, so ranges on `s` resolve against tags [4].
- **Install steps for a user.**
  1. Run `gh auth setup-git` for the private repository [5].
  2. Run `claude plugin marketplace add mikkel-bergmann/shipd-axel`.
  3. Run `claude plugin install shipd-ax@shipd-ax`, then enable auto-update in
     `/plugin` [5].
- **Naming convention.** Plugin and marketplace names follow `shipd-<topic>`, so
  every add-on is recognizable and never collides with `s` [2][3].
- **shipd's side, later.** `shipd doctor` could report installed `shipd-*`
  add-ons and their range on `s`. A harness extension could take a second body
  tree. Neither blocks the first add-on.

## Gaps & caveats

- The docs do not say whether two same-named plugins' **skills** merge under one
  prefix or shadow each other. They document only the dropped hooks [3]. Model C
  was rejected on the hooks finding, without testing skill behaviour.
- The minimum Claude Code version for dependency ranges differs between doc
  snapshots: one search result says v2.1.110, the fetched page cites v2.1.265 for
  a related feature [4]. Check this before relying on ranges.
- The Agent Skills client list did not render when fetched [6], so this report
  makes no claim about which specific harnesses load an add-on's skills.
- Whether `shipd doctor` should check add-ons, and how a harness extension would
  look, are design questions for shipd, not findings.
- Unverified: whether `claude plugin tag` works for a relative-path plugin that
  sits in the marketplace repository root's `plugins/` directory, as `s` does.

## Sources

1. Claude Code — Plugins overview — https://code.claude.com/docs/en/plugins
2. Claude Code — Create a marketplace — https://code.claude.com/docs/en/plugin-marketplaces
3. Claude Code — Plugin loading reference — https://code.claude.com/docs/en/plugins/loading.md
4. Claude Code — Plugin dependencies — https://code.claude.com/docs/en/plugins/dependencies
5. Claude Code — Host and maintain a marketplace — https://code.claude.com/docs/en/plugins/host-marketplace.md
6. Agent Skills — Overview — https://agentskills.io/
7. shipd — `harness_registry.py` — https://github.com/shipd-now/shipd/blob/main/plugins/s/skills/build/scripts/harness_registry.py
8. shipd — `harness_generate.py` and `harness_bodies.py` — https://github.com/shipd-now/shipd/blob/main/plugins/s/skills/build/scripts/harness_generate.py and https://github.com/shipd-now/shipd/blob/main/plugins/s/skills/build/scripts/harness_bodies.py
9. shipd — marketplace and plugin manifests, and repository tags — https://github.com/shipd-now/shipd/blob/main/.claude-plugin/marketplace.json, https://github.com/shipd-now/shipd/blob/main/plugins/s/.claude-plugin/plugin.json and https://github.com/shipd-now/shipd/tags
10. shipd — `hooks/hooks.json` — https://github.com/shipd-now/shipd/blob/main/plugins/s/hooks/hooks.json
