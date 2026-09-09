# retrieval-surfaces

shipd retrieval is ranked, case-insensitive term-hit search over markdown and
code — no embeddings, no search service. `shipd related` is the tuned
`/s:fix` surface (spec artifacts + wiki pages only; its contract is frozen).
`shipd search` is the superset: the related corpus plus workspace initiative
briefs, workspace PRDs, and the invoking repo's git-tracked files (NUL-sniffed
for binary, 1 MiB cap, content-directory files excluded to avoid
double-counting the spec library). Both print ranked keyed blocks capped at
ten with a remainder line, and take `--json`. Workspace surfaces degrade
silently when no anchor resolves; a non-git root loses only the code surface.
Search-first investigation is the standing expectation for interviewing
skills — nothing discoverable is ever asked.

Backed by: verified/spec-status (related-verb, search-verb),
epic/prd-discovery (Decisions).
