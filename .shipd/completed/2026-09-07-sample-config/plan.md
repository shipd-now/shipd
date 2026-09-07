# sample-config
Status: verified

## Idea

Ship a fully commented sample of `.shipd-config.json` — covering every
recognized configuration key — and install it into the content directory by
default through the engine's `init` verb, with a drift test tying the sample
to a new recognized-key registry.

### Motivation

shipd installs no commented reference config today: the recognized keys are
documented piecemeal across the `shipd-config` capability spec, `README.md`'s
build-telemetry table, and a build-scoped example file, so a user setting up a
repo has no single copyable reference. The user asked for a commented sample
covering the whole recognized surface, installed by default.

### Details

- Extend the existing copyable example,
  `plugins/s/skills/build/references/shipd.config.example.json`, from its
  build-telemetry scope to the full recognized surface: all 13 top-level keys,
  each with a one-or-two-line comment stating what it does and its default.
- Teach `spec_status.py init` to install a copy of that file as
  `<content-dir>/shipd.config.example.json` when nothing exists at that path,
  reporting it in the verb's existing `created`/`exists` line grammar.
- Add a `RECOGNIZED_CONFIG_KEYS` registry constant to `spec_common.py` and a
  test asserting the sample documents exactly those keys, so the sample cannot
  drift silently from the recognized surface.
- Bump the plugin version (0.6.185 → 0.6.186) in the same PR, per repo
  convention.

Affected capabilities: `spec-status` (modified `layout-init-verb`),
`shipd-config` (added `config-sample-coverage`). Impact:
`plugins/s/skills/build/scripts/spec_status.py` (`cmd_init`),
`plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/references/shipd.config.example.json`, tests under
`plugins/s/skills/build/tests/`, `plugins/s/.claude-plugin/plugin.json`. No
new dependencies; the engine stays stdlib-only.

### Non-goals

- No change to config resolution, precedence, or the `config-show` verb.
- No `.jsonc` format, comment-stripping tooling, or second sample file — one
  strict-JSON reference serves both the plugin docs and the installed copy.
- No auto-refresh of an installed copy on later `init` re-runs or plugin
  upgrades — presence means it is the user's copy, permanently.
- No docs restructuring beyond the reference file itself (the piecemeal docs
  stay where they are; the sample links the reader to them).

## Implementation

- **Form: strict JSON with the comment-key convention.** The sample stays
  parseable by stdlib `json.load` and uses the repo's established convention —
  a `"//"` header entry plus one `"// <key>"` entry per documented-but-
  undeclared key (as `shipd.config.example.json` already does). The
  layered-key-merge contract preserves unknown keys, so the file is copyable
  verbatim to `.shipd-config.json`. Rejected: a `.jsonc` file — not readable
  by the stdlib-only engine or its tests, and not copyable as-is.
- **One source of truth.** Extend the existing
  `plugins/s/skills/build/references/shipd.config.example.json` in place; the
  `shipd-config` requirements `pipeline-grammar-docs`, `pr-mode-docs`, and
  `guardrails-key-docs` already bind that file, and `init` copies the same
  file. Its header comment is reworked from "for /s:build" to a general
  reference; the `build` object keeps its four declared defaults (copying them
  declares values equal to the defaults — harmless) and gains `// `-comment
  entries for `design_dir` and the `video_*` subkeys. Rejected: a second
  sample or a Python-embedded string — duplicated content that drifts.
- **The 13 recognized top-level keys** (from `spec_common.py` resolution, the
  `shipd-config` spec, and a sweep of every engine script):
  `autonomous-pipeline`, `build`, `clone_sources`, `completed_retention_days`,
  `dir`, `guardrails`, `memory_dir`, `post-worktree-scripts`, `pr-mode`,
  `store_root`, `valid_themes`, `wiki_base`, `workspace`. Each gets its
  purpose and default in at most two comment lines; keys with richer grammar
  (pipeline, guardrails, workspace) point at the content directory's
  `README.md` sections as the existing comments do.
- **Install destination and never-clobber.** `cmd_init` installs the copy at
  `<content-dir>/shipd.config.example.json` only when nothing exists at that
  path; any existing filesystem object there counts as the user's copy and is
  never overwritten or refreshed. A user wanting the current sample deletes
  the file and re-runs `shipd init`. The verb prints one line in its existing
  grammar — `created <relpath>` / `exists <relpath>` (no trailing separator;
  it is a file) — after the four directory lines and before the
  `all shipd directories are ready` summary. Observed baseline: fresh
  `spec_status.py init --root <dir>` prints four `created .shipd/<name>/`
  lines then the summary and exits 0; the re-run prints `exists` lines.
- **Source resolution and the missing-source path.** The reference is located
  `__file__`-relative from `spec_status.py`
  (`../references/shipd.config.example.json`), which holds in both the repo
  checkout and the plugin cache snapshot. If the source file is missing, the
  verb prints one warning line to stderr naming the probed path and continues
  with exit code unchanged — the layout, not the sample, is init's contract,
  and a broken snapshot must not block scaffolding.
- **Drift guard.** `spec_common.py` gains `RECOGNIZED_CONFIG_KEYS`, a sorted
  tuple of the 13 key names, commented as the authoritative registry that must
  be extended (together with the sample) whenever a new top-level key is
  recognized. A new test module asserts: (a) the set of keys the sample
  documents — declared keys plus the `<key>` parsed from each `"// <key>"`
  entry, the bare `"//"` header excluded — equals the registry exactly, both
  directions; (b) the sample parses with strict `json.load`; (c) every
  module-level `*_KEY` string constant in `spec_common` is a registry member.
  Beyond the `*_KEY` check, constant-to-code linkage stays conventional — a
  stdlib-only engine has no key registry today, so full mechanical extraction
  of nested `config.get` literals would be noise-prone. Rejected: hardcoding
  the key list in the test — the registry belongs in the engine, where new-key
  authors already work.
- **Test seams.** `TestInitVerb` (`test_spec_status.py`) asserts
  `lines[:len(NAMES)]` are the directory lines and `lines[-1]` is the
  summary; the sample line lands between them, so existing assertions stay
  valid and new assertions cover the three behaviors (fresh install, existing
  copy untouched, missing source warns). CI runs
  `python3 -m unittest discover -s plugins/s/skills/build/tests`.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` moves to 0.6.186
  in the same PR, so the cache snapshot refreshes.

Risk: a future key added to resolution without touching the registry escapes
the equality test; the `*_KEY`-subset assertion and the registry's placement
beside the resolution code mitigate it. Risk: consumers scanning the content
directory root — the root already carries files (`constitution.md`,
`README.md`, `schema`) in this repo, so one more root file changes nothing.
