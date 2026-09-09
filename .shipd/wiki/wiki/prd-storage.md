# prd-storage

A PRD lives at `<workspace-root>/<content-dir>/prds/<slug>/prd.md`, beside
`initiatives/` — resolved and written exclusively by the engine, never by a
hand-built path. Resolution walks the workspace chain: a nested workspace
inherits the outer chain's PRDs, and the nearest member hosting a slug
shadows the outer copy. The lifecycle is `draft` → `approved`, or
`superseded`; every status change is a staged re-install through
`spec_emit.py prd --replace` (validate, restore byte-for-byte on failure),
never a hand edit of the store. No discoverable workspace means no PRD — the
write path refuses rather than falling back to a repo-local location.

Backed by: verified/shipd-prd (prd-store-format), verified/spec-io
(staged-emission, mediated-read-verb), epic/prd-discovery (Decisions).
See [[discover-phase]] for the hierarchy and [[prd-surfaces]] for the verbs.
