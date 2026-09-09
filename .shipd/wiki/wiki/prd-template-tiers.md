# prd-template-tiers

The PRD template tiers are **additive supersets with house-style names**:
`basic` requires Problem, Solution, Success criteria; `standard` (the default)
adds Users, Requirements, Non-goals; `comprehensive` adds Risks, Rollout,
Open questions. Nesting keeps a mid-interview tier escalation monotone —
answered sections stay valid — and the names match the why-first house style
(Problem before Solution, explicit Non-goals mirroring plan.md and epics).
Chosen by the user during prd-store planning (drained from
q-prd-tier-section-registry). The registry is engine-side
(`spec_common.PRD_TIER_SECTIONS`) so the linter never parses template prose;
the tier lists are a floor, not a ceiling — extra sections are allowed. The
three skeletons ship in the plugin, drift-guarded against the registry.

Backed by: epic/prd-discovery (Decisions), verified/shipd-prd
(prd-tier-registry, prd-template-files).
