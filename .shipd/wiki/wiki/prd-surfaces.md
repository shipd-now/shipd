# prd-surfaces

The PRD's user surfaces deliberately mirror initiative parity plus one
noun verb: `shipd search <terms>` finds PRDs by content (kind `prd` records
in the ranked corpus); `shipd prd <slug>` prints the report — status, tier,
`Initiative:` link, chain-resolved path, and `cited-by:` lines for every epic
in the repo universe carrying `PRD: <slug>` (explicitly `cited-by: none` when
uncited); bare `shipd prd` lists the workspace roster with chain shadowing;
both take `--json`. Content display composes with `shipd render <path>` on
the report's path line — no bespoke viewer. The write path is `/s:prd` (and
the engine's `spec_emit.py prd` beneath it); `workspace-show` lists
initiatives but never PRDs.

Backed by: verified/shipd-prd (prd-show-verb), verified/spec-status
(search-verb), verified/shipd-cli (cli-dispatch), docs/prd.md.
Convention context: [[binary-noun-verbs]], [[retrieval-surfaces]].
