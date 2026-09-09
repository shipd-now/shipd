# discover-phase

The discover phase of product engineering is captured as an artifact, not a
conversation: a **PRD** written against a template, validated by the engine,
and stored in the workspace where every project can read it. The hierarchy is
Initiative → PRD → Epic → Change, and **every link in it is optional** — the
lower artifact names the higher one in its own header (`Initiative:` on a PRD,
`PRD:` on an epic, `Epic:` on a change), or names nothing at all. A PRD is
standalone: it needs no initiative and no epic, ever; epics cite the PRD,
never the reverse. Authoring runs through the `/s:prd` interview — a
sanctioned multi-round exception to the single-batched-round house style,
still bound by the codebase-first rule (investigate via [[retrieval-surfaces]]
before asking anything).

Backed by: epic/prd-discovery (Decisions), verified/shipd-prd, docs/prd.md.
Storage and lifecycle: [[prd-storage]]. Templates: [[prd-template-tiers]].
