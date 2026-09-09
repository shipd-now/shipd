# binary-noun-verbs

The `shipd` binary's curated surface uses **noun verbs**, not command words:
`shipd epic <slug>`, `shipd prd [slug]`, `shipd workspace`, `shipd wiki` each
print their artifact's report through pure process-replacement delegation to
one engine script. Internal engine verbs (`cat`, `spec_emit.py` modes) are
not user surfaces. Two consequences are standing: the `cli-dispatch`
requirement enumerates the verbs **exhaustively** ("SHALL expose exactly"),
so adding any verb is a full MODIFIED restatement of that requirement (a
known, accepted token-budget warning); and new artifact kinds default to
**initiative parity** — no `list` kind, no bespoke viewer — until a noun verb
earns its place, with display composing through `shipd render`.

Backed by: verified/shipd-cli (cli-dispatch), completed/prd-emit (parity
decision), completed/prd-verb.
