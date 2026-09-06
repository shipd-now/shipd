# docs-artifact-kind
Status: verified
Epic: epic-knowledge

## Idea

Add a general `docs` artifact kind to the spec engine so an arbitrary
supplied document — strategy notes, meeting minutes, API excerpts — installs
under `<content-dir>/docs/<slug>/doc.md` through the same staged, validated
seam as research reports, and is readable, searchable, and listable through
the engine's read verbs.

### Motivation

The epic layer admits exactly two reference kinds — research reports and
video briefs — so every other document either masquerades as a "research
report" or lands only in a conversation transcript (epic `epic-knowledge`,
Introduction). This member adds the storage kind the coming `## References`
shelf and capture rubric will route to.

### Details

- `spec_emit.py docs <slug> --from <file>` installs a document at
  `<content-dir>/docs/<slug>/doc.md`, validate-then-install with `--replace`
  semantics and schema-marker stamping, mirroring `emit_research`.
- `lint_docs(root, slug, errors)` validates a non-empty `# <title>` on
  line 1 only — no citation skeleton, ever; library lint never walks `docs/`.
- `cat docs <slug>` resolves cross-universe like research/video.
- `related` gains the `docs/<slug>/doc.md` surface (kind `docs`).
- `shipd list docs` lists slug directories root-first, status-less.

Affected capabilities: `spec-io`, `shipd-cli`, `spec-status` (modified);
`shipd-spec-lint`, `shipd-spec-format` (one added requirement each). Impact:
`plugins/s/skills/build/scripts/spec_emit.py`, `spec_lint.py`,
`spec_status.py`, `plugins/s/bin/shipd`, tests under
`plugins/s/skills/build/tests/`, plugin version bump.

### Non-goals

- No `## References` epic section, no skill wiring, no capture rubric —
  those are the sibling members `epic-references-shelf` and
  `epic-capture-rubric`.
- No per-flavor kinds (notes, strategy, excerpt) — taxonomy lives in the
  document, not the storage (epic Decision).
- No `related` coverage for the `video` kind — its absence there predates
  this change and stays as-is.
- No schema-version bump and no `docs/` entry in the init scaffold's
  `LAYOUT_DIRS` — following the `video` kind's precedent; emission creates
  the directory on demand.

## Implementation

- **Mirror the research kind end to end.** `emit_docs` copies
  `emit_research` (`spec_emit.py:196-217`): single-file staged install
  through `_install_dir` (refuse existing without `--replace`,
  remove-on-finding, restore backup), then `sc.stamp_schema_marker(root)`
  and `installed docs <slug> at <path>`. Rejected: a directory-shaped
  staging like `change` — the kind installs one markdown file, exactly like
  research/video/epic.
- **Title-only lint, unconditional.** `lint_docs` checks the file exists and
  line 1 is a non-empty `# <title>`, nothing else — even a document carrying
  `[n]`-looking markers installs, because supplied documents (API excerpts,
  pasted notes) must never be forced into a citation grammar the epic
  explicitly rejects ("no citation skeleton demanded"). Rejected: reusing
  `lint_research`'s conditional citation skeleton — a footnoted excerpt
  would then fail on a provenance grammar it never claimed.
- **In-process checks only.** Like research and video, `lint_docs` gets no
  `spec_lint.py` command-line mode and `lint_library` never walks `docs/`;
  the checks run only at emit time.
- **Read seam.** Add a `docs` entry to `_CAT_PROBES`
  (`spec_status.py:2361`) probing `docs/<slug>/doc.md`, extend `cmd_cat`'s
  single-file kind tuple, its unknown-kind error text, and the `cat`
  subparser `choices` (`spec_status.py:3529`) plus the docstrings. Noun in
  the not-found error: `docs`.
- **Search seam.** `_related_candidate_artifacts` (`spec_status.py:845`)
  gains a `docs` walk over `docs/<slug>/doc.md` records (kind `docs`),
  placed with the other single-file kinds; dedup/ordering machinery is
  untouched.
- **List seam.** Add `docs` to `LIST_KINDS` and `_LIST_KIND_DIRS`
  (`spec_status.py:1321-1329`) — `_list_directory_rows` already handles any
  status-less directory kind. In `plugins/s/bin/shipd`: `LIST_EMPTY_TEXT`
  gains `"docs": "no docs"`, and the `USAGE` banner's kind roster
  (`bin/shipd:115`) adds `docs`. `--all` keeps refusing non-`changes` kinds
  with no code change.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` 0.6.179 →
  0.6.180, per AGENTS.md, in this change.
- Observed premises: `shipd list research --root .` prints rows with status
  `-` and exits 0; `cat epic epic-knowledge` prints with a `---` separator;
  CI runs `python3 -m unittest discover -s plugins/s/skills/build/tests`.
- Risk: the kind word `docs` is plural where others are singular
  (`research` is uncountable, `video` singular); the epic fixes `docs` in
  every verb (`spec_emit.py docs`, `cat docs`, `shipd list docs`), so all
  surfaces use the one word and no singular alias is added.
