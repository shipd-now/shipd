# workspaces-root
Status: verified

## Idea

Add a recognized layered config key, `workspaces_root`, that mandates one
parent directory for all job workspaces, enforced when a workspace is created
(`workspace-init`) or cloned (`/s:workspace clone`).

### Motivation

The user organizes engagements as job workspaces under one parent directory
(e.g. `~/workflows/`), but nothing in the engine or the `/s:workspace` skill
knows or enforces that pattern — a workspace can be created or cloned anywhere.
A config-declared root makes the pattern a mandate every creation path honors.

### Details

- New key `workspaces_root` in `spec_common.RECOGNIZED_CONFIG_KEYS` and the
  copyable sample config, with an accessor `workspaces_root_dir(root)`
  (`~` expansion, absolute-only, `ConfigError` on malformed).
- Enforcement inside `sc.init_workspace`, so every caller of the
  `workspace-init` verb inherits it: bare names resolve into the declared root
  (leaf created), explicit targets outside it are refused naming both paths
  and the key.
- `/s:workspace` skill: `init` names the declared root in its target round;
  `clone` without a dest lands under the declared root, and an explicit dest
  outside it is refused with the same error shape.
- `shipd doctor`'s existing `config` check validates the key (fail on
  malformed value, warn when the declared root directory is missing).
- Plugin version bump in the same PR.

Affected capabilities: `shipd-config`, `shipd-workspace`, `spec-status`,
`shipd-cli` (all modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/references/shipd.config.example.json`,
`plugins/s/skills/build/scripts/spec_status.py`, `plugins/s/bin/shipd`,
`plugins/s/skills/workspace/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`; no new dependencies.

### Non-goals

- No behavior change when the key is undeclared — every surface works exactly
  as today.
- No re-rooting of explicit paths: an explicit target outside the root is
  refused, never silently moved into it.
- No changes to `workspace-sync` or member materialization; members live
  inside their workspace regardless of this key.
- No new doctor check name and no doctor remedy — report-only, folded into
  the existing `config` check.
- No docs/workspaces.md rewrite; the sample-config entry documents the key.

## Implementation

- **Key name and semantics.** `workspaces_root`, matching the snake_case
  convention of the other path keys (`store_root`, `wiki_base`, `memory_dir`).
  Value: non-empty string, `~` expands, expanded value must be absolute —
  the `wiki_base`/`memory_dir` pattern (spec_common.py:1300–1370). Rejected:
  `store_root`'s relative-to-config-file resolution — that is a deliberate
  exception for committed workspace configs; this key's natural home is the
  user layer (`~/.shipd-config.json`), where relative values have no anchor.
  New module constant `WORKSPACES_ROOT_KEY = "workspaces_root"` (the drift
  test's `*_KEY` scan requires registry membership) and accessor
  `workspaces_root_dir(root)` returning `None` when undeclared, the expanded
  normalized absolute path when declared, raising `ConfigError` naming
  `workspaces_root` on a malformed value. Resolution goes through the normal
  layered chain (`resolve_config`), so any layer may declare it.
- **Registry and sample move together.** Add the key to
  `RECOGNIZED_CONFIG_KEYS` (spec_common.py:369) and a `// workspaces_root`
  comment entry to
  `plugins/s/skills/build/references/shipd.config.example.json` in the same
  task — `tests/test_config_sample.py` fails if either lags. Comment entry
  only (the key has no default), so copying the sample changes no behavior.
- **Enforcement lives in `sc.init_workspace`** (spec_common.py:1144), not the
  CLI wrapper, so `shipd workspace init`, the skill, and any future caller
  inherit it. Sequence, before the existing guards: (1) resolve config from
  `os.path.abspath(path)` (`load_layered_config` walks path strings, so a
  not-yet-existing target resolves fine); (2) when the key is declared and
  the argument is a **bare name** — a single-component relative path, no
  separator, not `.`/`..` — re-target to `<root>/<name>`: the declared root
  must be an existing directory (`ConfigError` naming `workspaces_root` and
  the missing root otherwise), and the leaf is created with `os.mkdir` when
  absent (verified premise: today `workspace-init bare-slug` exits 1 with
  `target directory does not exist`, so the convenience requires leaf
  creation); (3) when the key is declared and the final target lies outside
  the root — compared on `os.path.realpath` of both, target inside iff
  `os.path.commonpath([root, target]) == root` — raise `ConfigError` naming
  the target, the declared root, and `workspaces_root`. Containment is
  **descendant-of-root**, not direct-child: a `--nested` job workspace
  legitimately sits deeper inside a member; the root itself is a valid
  target. Existing guards (discoverable-workspace refusal, target-must-exist
  for explicit paths, nested/git options) run unchanged on the final target.
  Rejected: enforcement in `cmd_workspace_init` — skips future engine
  callers.
- **CLI verb unchanged in shape.** `workspace-init <path>` keeps its
  signature; the new refusals surface through the existing
  `ConfigError → StatusError → exit non-zero` path (spec_status.py:3066).
  Docstring and parser help mention the declared-root behavior.
- **Skill flows** (`plugins/s/skills/workspace/SKILL.md`): `init` — when the
  resolved configuration declares the key (read via `config-show`), the
  target-root question names the declared root and offers in-root candidates,
  substituting `<root>/<repo-name>` for a natural candidate lying outside it;
  a bare-name choice passes through to the verb, which resolves it. `clone` —
  without `[dest]`, the destination is `<workspaces_root>/<derived-name>`
  (git-derived name under the declared root); an explicit dest resolving
  outside the root is refused before cloning, naming the dest, the root, and
  the key — the engine's error shape. The clone check is skill-side because
  `git clone` never passes through the engine. Undeclared key: both flows
  read exactly as today.
- **Doctor fold-in.** `check_config` in `plugins/s/bin/shipd` (line 455)
  additionally calls the accessor inside its existing try — a malformed value
  fails the `config` check with the accessor's own error line (the
  `doctor-pr-mode-check` precedent); a declared root that is not an existing
  directory returns `warn` naming `workspaces_root` and the path; valid or
  undeclared leaves the reporting untouched. No new check name.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` 0.6.187 → 0.6.188.
- **Risks.** A developer's real `~/.shipd-config.json` declaring the key could
  leak into tests — every new test isolates `$HOME` with the existing
  `home_set_to` helper (test_spec_common.py:17). macOS `/tmp` symlinking is
  neutralized by comparing `realpath` on both sides.
