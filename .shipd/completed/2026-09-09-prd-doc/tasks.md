## 1. The guide

- [x] 1.1 [req: prd-user-docs] Under the existing `docs/` directory create
      the new `prd.md` guide implementing the plan's seven-part outline
      (concept + hierarchy diagram, workspace storage and chain resolution,
      lifecycle with staged approval, the three tiers' exact section lists
      with the standard default and additive nesting, the `/s:prd`
      walkthrough, the `shipd search` example with a trimmed output block,
      and the closing FAQ), honoring the accuracy floor and the
      binary-or-skill command convention in plan.md's Implementation. Match
      the register of `docs/oracle.md` and `docs/workspaces.md`; mermaid
      diagram emoji-free with no hard-coded colors.
- [x] 1.2 [req: prd-user-docs] Verify the guide: confirm every relative link
      and anchor in `docs/prd.md` resolves; grep the file to confirm no
      `spec_status.py`/`spec_emit.py` invocation appears; and compare its
      tier section lists against `PRD_TIER_SECTIONS` in
      `plugins/s/skills/build/scripts/spec_common.py`, fixing any mismatch.
- [x] 1.3 [req: *] Run the full engine suite
      (`python3 -m unittest discover plugins/s/skills/build/tests`) and
      confirm it passes (regression only — this change adds no code).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 86 | 25.7k |
| Write | 1 | 4.7k |
| Agent | 2 | 651 |
| Read | 11 | 363 |
| (no tool) | 0 | 146 |
| **Total** | 100 | 31.6k |
