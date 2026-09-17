# customise-doc
Status: verified
Theme: developer-experience

## Idea

Ship `docs/customise.md`, one reference page mapping every customisation
surface shipd already offers.

### Motivation

shipd is already broadly customisable, and no page says so. The delivery steps
are a config key. The guardrail rulebook, the constitution, and the
post-worktree scripts are files. The oracle's knowledge is a wiki. A reader
searching `docs/` for `.shipd-config.json` finds four incidental mentions
across three pages and no map.

That gap costs twice. A user never discovers a surface that already exists, and
the team cannot judge which gaps are real before extending the surface. This
change writes the inventory the customisability work builds on.

### Details

- One new page, `docs/customise.md`, typed `reference` and within its cap.
- The page maps each surface and defers its grammar to the existing authority:
  the content directory's `README.md` for the pipeline, PR mode, and the
  `guardrails` key, and `docs/guardrails.md` for the rulebook.
- The page answers the delivery-steps question directly. `autonomous-pipeline`
  is the key, the registry runs `research → epic → plan → gate → build →
  review`, and three presets ship.
- The page closes with what is fixed today: the generated command bodies, the
  registry's membership and canonical order, and the two guardrail modes.
- A drift guard asserts every recognized config key appears in the page.
- `README.md`, `docs/cheatsheet.md`, and `docs/getting-started.md` link it.

### Non-goals

- No engine change. This change documents the surface. Extending it is a
  separate epic, decided once the inventory is readable.
- No refresh of this repo's `.shipd/shipd.config.example.json`. The `init` verb
  never rewrites an existing file, so the behind copy is specified behavior,
  and the plugin's reference copy is the governed source.
- No rewrite of `docs/guardrails.md`, `.shipd/README.md`, or any other page
  beyond adding a link.
- No new capability. The requirement joins `shipd-config`, beside the
  `guardrails-key-docs` requirement whose standalone-guide pattern it follows.

## Implementation

**The page's shape.** Follow `docs/guardrails.md`. Put
`<!-- doc-type: reference -->` on line 1, open with the problem the page
solves, give one section per surface, and close with `## See also`. Tables
carry the inventory, and prose carries only what a table cannot.

**Section order.** The config file and its layering; the key table; the
delivery steps; the file-authored surfaces; the harness; the environment
overrides; the limits; see also.

**The key table.** One row per member of `RECOGNIZED_CONFIG_KEYS`, naming what
the key governs and where its grammar lives. Source the rows from
`plugins/s/skills/build/references/shipd.config.example.json`, the governed
copy — never from this repo's `.shipd/` copy, which is behind it. Name the
`build` sub-block's members in one row rather than a row each.

**The read verbs.** Cite `shipd config` for the resolved configuration, and
`/s:status pipeline` for the effective pipeline. Show
`pipeline-show --expand eco` as the way to start from a preset, because the key
holds a preset name or a list and never both.

**The limits section.** State three things, each already true in the code. The
harness generates every `/s:` command body from the plugin's `harness/bodies/`
tree, so a repo cannot override the steps a skill follows. A declared pipeline
chooses and configures registry stages and inserts custom steps, but cannot add
to the registry or reorder its stages. A guardrail rule picks one of the two
built-in modes.

**The drift guard.** Extend
`plugins/s/skills/build/tests/test_config_sample.py` with one test asserting
every `RECOGNIZED_CONFIG_KEYS` member appears in `docs/customise.md`. Resolve
the repository root five directories above the test file, the way
`plugins/s/skills/document/tests/test_docs_ci_gate.py` resolves it.

**The links.** `README.md` gains the guide beside its getting-started link.
`docs/cheatsheet.md` gains it in the opening paragraph that already points at
the getting-started guide. `docs/getting-started.md` gains an inline link on
the existing sentence about the `eco` preset, rewrapped so the file stays
within its 150-line cap.

**The gate.** `.github/workflows/ci.yml` already lints every `docs/*.md`, so
the page needs no workflow change. Run
`python3 plugins/s/skills/document/scripts/docs_lint.py docs/customise.md`
until it exits 0.
