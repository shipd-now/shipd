# shipd-init
Status: verified

## Idea

Add a `shipd init` verb that creates the content-directory layout safely and
reports its readiness, and route the plan skill's missing-layout scaffold
through the same engine verb.

### Motivation

Nothing in the engine initializes the `verified/`/`planned/`/`completed/`
layout on demand — it appears lazily at first merge, and `/s:plan`'s
missing-layout guard hand-scaffolds the directories ad hoc. There is no
single, safe, reportable way to make a repository ready for shipd.

### Details

- Add an `init` verb to `spec_status.py`: resolve the content directory from
  the root's layered configuration, create `verified/`, `planned/`, and
  `completed/` (parents included) without touching anything that already
  exists, print one `created`/`exists` line per directory and the summary
  `all shipd directories are ready`.
- Expose it as `shipd init` in the binary's curated verb table, delegating to
  `spec_status.py init`, with a usage-banner row.
- Point `/s:plan`'s missing-layout guard's accepted-scaffold action at the
  engine verb instead of hand-made directories.

Affected capabilities: `spec-status` (added), `shipd-cli` (modified),
`shipd-plan` (modified). Impact:
`plugins/s/skills/build/scripts/spec_status.py`, `plugins/s/bin/shipd`,
`plugins/s/skills/plan/SKILL.md`, engine tests, plugin version bump.

### Non-goals

- No seeded content files (`README.md`, `constitution.md`, `.gitkeep`) — the
  verb creates empty directories only, matching today's minimal scaffold.
- No `--json` mode on the new verb.
- No change to the lazy directory creation the emit/merge engines already do.

## Implementation

- **The logic lives in `spec_status.py`, not in the binary.** The binary is a
  curated dispatcher whose verbs replace the process with one engine-script
  invocation (shipd-cli cli-dispatch), and `spec_status.py` already hosts the
  sibling scaffolds `workspace-init` and `wiki-init`. Rejected: an in-binary
  implementation like `doctor` — it would duplicate config resolution and be
  untestable from the engine suite.
- **New handler `cmd_init(root)` + an `init` subparser** wired into the
  existing dispatch chain in `main`. Resolution goes through
  `sc.specs_dir(root)` so a configured `dir` key (shipd-config
  content-dir-key) is honored; a `sc.ConfigError` surfaces through the
  existing handler and exits `1`.
- **Clobber safety is check-then-create.** Before creating anything the
  handler checks the content directory and each of the three targets; if any
  exists as a non-directory it raises `StatusError` naming that path and
  creates nothing. Otherwise `os.makedirs(path, exist_ok=True)` per target —
  existing directories and their contents are never modified.
- **Output shape:** one line per target, `created <dir>/<name>/` or
  `exists <dir>/<name>/` with `<dir>` the resolved content-dir name relative
  to the root, then the summary line `all shipd directories are ready`. Exit
  `0` in both the fresh and the already-initialized case — the verb is
  idempotent.
- **Binary wiring:** add `"init": ("spec_status.py", ["init"])` to
  `VERB_TABLE` in `plugins/s/bin/shipd`, an `init` row in `USAGE`, and extend
  the module docstring's deliberate-exceptions list with this sixth writing
  verb (it writes only empty layout directories, never a spec artifact).
  Trailing arguments (`--root`) pass through verbatim per the dispatch
  contract, verified against the live table at `plugins/s/bin/shipd` (verbs
  such as `status` already dispatch this way).
- **Plan-skill guard:** `plugins/s/skills/plan/SKILL.md` keeps its
  stop-and-ask shape; only the accepted-scaffold action changes to run
  `spec_status.py init` — one function, two callers (`shipd init` and the
  skill).
- **Version bump** to `0.6.161` in `plugins/s/.claude-plugin/plugin.json`
  (the plugin cache snapshot is version-keyed).

Risk: a future caller passing a root with a hostile `dir` config could aim
the scaffold elsewhere — already guarded, `specs_dirname` rejects multi-
component or empty values before any path is built.
