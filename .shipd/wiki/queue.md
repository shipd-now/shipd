# Queue

## q-prompt-dir-notation-enforcement-test
- Asked: 2026-09-07 shipd/.worktrees/prompt-dir-notation
- Question: Should the prompt-dir-notation change add a stdlib-only engine test (plugins/s/skills/build/tests/) that scans every skills/**/*.md line mentioning .shipd/ and fails unless the line is exempt (fixed ~/.shipd home path, $SANDBOX onboarding path, a default-annotated mention, or the file carries the canonical notation rule), or ship as prose-only edits with no enforcement?
- Options: add the enforcement test | prose-only, no test
- Recommendation: add the enforcement test
- Answer: When a convention is introduced into skill prompt prose (like the content-dir path notation), guard it with a stdlib-only test in the engine suite (plugins/s/skills/build/tests/) rather than shipping prose-only edits — unenforced prompt conventions erode as prompts evolve. Chosen for prompt-dir-notation: a line-level scan of skills/**/*.md requiring each .shipd/ mention to be exempt (~/.shipd home path, $SANDBOX, default-annotated) or covered by the file's canonical notation rule.

## q-prd-tier-section-registry
- Asked: 2026-09-08 shipd/.worktrees/prd-store/epic prd-discovery
- Question: Which concrete level-2 section lists should the PRD tier registry pin for basic/standard/comprehensive?
- Options: (a) additive supersets: basic Problem/Solution/Success criteria; standard adds Users/Requirements/Non-goals; comprehensive adds Risks/Rollout/Open questions | (b) additive supersets with different names (Background/Objectives/KPIs style) | (c) independent per-tier lists that need not nest
- Recommendation: (a) — additive nesting keeps mid-interview tier escalation monotone, and the names match the why-first house style (Problem before Solution, explicit Non-goals mirroring plan.md and epics)
- Answer: The PRD template tiers are additive supersets with house-style names: basic requires Problem, Solution, Success criteria; standard adds Users, Requirements, Non-goals; comprehensive adds Risks, Rollout, Open questions. Nesting keeps mid-interview tier escalation monotone and the names match the why-first house style (chosen by the user during prd-store planning).
