<!-- doc-type: reference -->

# Customising shipd

shipd offers many customisation surfaces. The delivery steps are a config
key. The guardrail rulebook, the constitution, and the post-worktree
scripts are files. The oracle's knowledge is a wiki. This page maps every
surface, and links to the authority that defines each one's grammar in
full.

## The configuration file and its layering

`.shipd-config.json` is the only file the engine reads for configuration.
Layers resolve by **upward search** — from the working directory
parent-by-parent to the filesystem root, then `~/.shipd-config.json`, then
the built-in defaults. Layers merge **nearest-wins-wholesale**: the closest
layer declaring a key supplies that key's whole value, never a per-field
blend with a farther layer.

```bash
shipd config              # resolved keys, values, and which layer supplied each
```

`shipd config` is `spec_status.py config-show` under the hood. A workspace
root's config governs every member repo beneath it for a key that repo
leaves undeclared.

## The recognized keys

One row per key the engine recognizes.
`plugins/s/skills/build/references/shipd.config.example.json` is the
canonical, copyable reference — copy it to `.shipd-config.json` and edit; a
repo's own `.shipd/` copy may be behind it.

| Key | Governs |
| --- | --- |
| `dir` | The content directory name holding the spec library. Default `.shipd`. |
| `completed_retention_days` | How many days a completed change stays visible. Default 30; `0` or `null` disables retention. |
| `store_root` | Relocates the content directory into an external store, one folder per repo. |
| `wiki_base` | A durable base wiki store searched alongside the workspace's own `wiki/`. |
| `memory_dir` | Root of the personal memory store. Default `~/.shipd-memory`. |
| `valid_themes` | The theme vocabulary the linter accepts in an artifact's `Theme:` header. |
| `autonomous-pipeline` | Which steps a delivery runs. See "The delivery steps" below. |
| `pr-mode` | How a change's PR ships: `auto` (default) or `draft`. See the content directory's `README.md`. |
| `guardrails` | The guardrail hook's kill-switches. See [docs/guardrails.md](guardrails.md). |
| `voice` | Gates the session-start voice digest hook. Default `true`. |
| `workspace` | Marks the declaring directory as a workspace root; holds its `projects` and `focus` registry. |
| `workspaces_root` | The mandated parent directory job workspaces are created and cloned under. |
| `post-worktree-scripts` | Shell command lines run in a freshly created worktree. Register through `shipd worktree hooks add`. |
| `clone_sources` | Local directories the workspace sync planner probes for an existing clone before cloning fresh. |
| `lint` | Configures `semdiff lint`: `run_scripts` and `disable`. |
| `worktree_sweep` | Gates whether worktree creation runs `worktree.sh sweep` afterward. Default `true`. |
| `worktree_idle_minutes` | The idle window, in minutes, before the `remove` verb's activity guard stops treating a dirty worktree as fresh. Default 30. |
| `worktree_stale_days` | The window, in days, beyond which a sweep reports an unmerged branch stale. Default 7. |
| `store_autocommit` | Gates whether an engine write into a workspace or external store auto-commits locally. Default `true`. |
| `store_sync` | Gates whether the session-boundary hook runs its networked git (fetch, fast-forward merge, push). Default `true`. |
| `build` | Settings for a `/s:build` run: `logging_enabled`, `log_dir`, `number_format`, `parallelism`, and the design/video roots (`design_dir`, `video_dir`, `video_asr`, `video_vocabulary`, `video_max_frames`, `video_scene_floor`, `video_cursor`). |

## The delivery steps

`autonomous-pipeline` is the key that chooses which steps a delivery runs.
The stage registry, in canonical relative order, is `research → epic → plan →
gate → build → review`.

The key holds either an ordered list or a preset name, never both. A list
entry takes one of five forms:

- run a registry stage as built in
- skip it explicitly
- bind extra tools to it
- replace its implementation
- insert a `custom` step at that position

Three presets ship: `default` (every stage, bare), `eco` (the cheap
delivery), and `basic` (cheaper still).

```
/s:status pipeline                # the effective pipeline and its provenance
/s:status pipeline eco            # a preset's entry list, to start a custom one
```

The content directory's `README.md` ("The autonomous pipeline" section)
carries the full entry grammar, the per-stage options, and each preset's
exact shape.

## The file-authored surfaces

Some surfaces are files, not config keys:

- **`<content-dir>/constitution.md`** — optional, repo-wide engineering
  rules. When present, the planning and build flows load it as a binding
  constraint on every design and implementation.
- **Guardrail rule files** — markdown files matched against every `Edit`
  and `Write` call. Three sources merge, first source winning a rule name:
  the repo's `<content-dir>/rules/*.md`, the user's `~/.shipd/rules/*.md`,
  and the plugin's own built-ins. See [docs/guardrails.md](guardrails.md)
  for the file format and both modes.
- **`post-worktree-scripts`** — registered through `shipd worktree hooks
  add` (or `/s:worktree-hooks`), never by hand-editing the config.
- **The wiki and personal memory pages** — the oracle's durable knowledge:
  the workspace `wiki/` store, and each user's own pages under
  `memory_dir`.

## The harness

A **harness registry** decides which agent surfaces receive the `/s:`
commands — Claude Code, Cursor, GitHub Copilot, Windsurf, Codex, and the
rest. `shipd harness` lists the registry and inspects one entry; `shipd
install` and `shipd harness add <name>` generate a harness's command
surface into a repository.

## The environment overrides

Three environment variables override a config value for one session,
without editing a file:

| Variable | Overrides |
| --- | --- |
| `SHIPD_GUARDRAILS` | Set to `off` to bypass the guardrail hook entirely, for that session only. |
| `SHIPD_WORKTREE_IDLE_MINUTES` | Overrides `worktree_idle_minutes`, the `remove` verb's activity-guard window. |
| `SHIPD_WORKTREE_STALE_DAYS` | Overrides `worktree_stale_days`, the sweep's staleness window. |

## The limits

Three things stay fixed today, regardless of configuration:

- **The `/s:` command bodies stay fixed.** The harness generates every
  command's body from the plugin's own `harness/bodies/` templates. A repo
  cannot override the steps a skill follows.
- **The stage registry stays fixed.** A declared pipeline chooses stages
  from the registry and inserts custom steps around them. It never adds to
  the registry, and never reorders its stages.
- **The guardrail modes stay fixed.** A rule picks one of exactly two
  built-in modes, `deny` or `remind`; there is no third mode.

## See also

- [The content directory's `README.md`](../.shipd/README.md) — the format
  authority for the pipeline entry grammar, the `pr-mode` key, and the
  `guardrails` key.
- [Guardrails](guardrails.md) — the rule file format and both hook modes.
- [Cheatsheet](cheatsheet.md) — every `/s:` command and `shipd` verb.
- [Getting started](getting-started.md) — the first-run walkthrough.
