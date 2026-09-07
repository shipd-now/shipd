# shipd-search
Status: verified
Epic: prd-discovery

## Idea

Add a `search` verb to the status CLI and the `shipd` binary that ranks a
superset corpus — every surface `related` already searches, plus workspace
initiative briefs and the invoking repo's git-tracked code files — by
case-insensitive term-hit count.

### Motivation

`related` deliberately ranks only spec artifacts and wiki pages, so the
codebase itself and workspace-level surfaces are invisible to retrieval; the
`prd-discovery` epic needs a search the `/s:prd` skill can ground its
investigation on before interrogating the user.

### Details

- New `search <term> [term...]` verb in `spec_status.py`, reusing `related`'s
  corpus builders, scorer, and output contract unchanged.
- Two new surfaces: workspace initiative briefs (kind `initiative`) and the
  invocation root's git-tracked files (kind `code`).
- New curated `search` verb in `bin/shipd` delegating to
  `spec_status.py search`, listed in the banner and the `--json` read-verbs
  sentence.

Affected capabilities: `spec-status` (added requirement), `shipd-cli`
(modified `cli-dispatch`). Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/build/tests/test_shipd_cli.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No PRD surface — the PRD store does not exist yet; a later `prd-discovery`
  member adds it to this corpus.
- No change to `related` — its contract (`spec-status/related-verb`) stays
  byte-for-byte as it is.
- No cross-repo code search: the code surface is the invocation root's own
  tracked files only, never other workspace project repos or worktrees.
- No semantic/embedding search, no index files, no third-party dependencies.

## Implementation

- **Reuse, don't fork.** `cmd_search(root, terms, as_json)` composes the
  existing pieces: `_related_corpus(root)` (which already spans root +
  worktrees + wiki) extended with `_search_initiative_artifacts(root)` and
  `_search_code_artifacts(root)`; scoring via `_related_score`, paths via
  `_related_path`, the same 10-block cap (`RELATED_MAX_BLOCKS`), the same
  keyed-block/`--json`/`Error:`-on-no-match rendering as `cmd_related` —
  extract the shared render/rank tail into a helper both verbs call rather
  than duplicating it. Rejected: a standalone corpus walk — two walkers would
  drift.
- **Initiative surface.** Resolve the workspace anchor through
  `sc.resolve_wiki_root(root)` — the same one-seam resolution the wiki
  surface uses — and yield `("initiative", <slug>, <brief-path>, [brief-path])`
  for every `initiatives/<slug>/brief.md` under `sc.initiatives_dir(anchor)`.
  Any resolution failure (`StatusError`, `ConfigError`, `OSError`) yields no
  records, mirroring `_related_wiki_artifacts`' silent degradation.
- **Code surface.** Enumerate with `subprocess.run(["git", "ls-files", "-z"],
  cwd=root)`; on non-zero exit or missing git, yield nothing (silent
  degradation). Skip: paths under the invocation root's resolved content
  directory (`sc.specs_dir(root)`) — those files are already the artifact
  corpus; files whose first 8192 bytes contain a NUL byte (binary sniff);
  files larger than 1 MiB (`os.path.getsize` guard, bounded runtime);
  unreadable files. Record shape `("code", <repo-relative path>, <path>,
  [<path>])` — the slug is the relative path, so blocks read naturally.
  Rejected: an extension allowlist — brittle versus the NUL sniff.
- **Ordering and dedup.** Code and initiative records append after the
  related corpus; the existing sort (score desc, then kind, then slug) keeps
  output deterministic. No cross-surface dedup is needed: `(kind, slug)`
  pairs cannot collide across the new kinds, and content-dir exclusion
  prevents artifact/code double counting.
- **CLI wiring.** Argparse: `p_search` mirroring `p_related` (`terms`
  nargs="+", `_add_json_flag`); dispatch `args.verb == "search"` →
  `cmd_search`. Binary: `"search": ("spec_status.py", ["search"])` in
  `VERB_TABLE`, a banner line `search <term> [term...]` under `related`'s,
  and `search` added to the trailing "read verbs … accept --json" sentence.
- **Tests.** `SearchTest` in `test_spec_status.py` modeled on `RelatedTest`
  (`:4759`): real temp repos with `git init` + committed files for the code
  surface. Delegation test in `test_shipd_cli.py` mirroring the `related`
  delegation scenario.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` `0.6.188` →
  `0.6.189` in this change, per the repo rule for `plugins/s/` edits.
- **Risk:** reading many tracked files per invocation is O(repo) — bounded by
  the 1 MiB/NUL guards; acceptable for an interactive read verb (1,409 files
  in this repo today). A repo that is not a git checkout simply loses the
  code surface, never errors.
