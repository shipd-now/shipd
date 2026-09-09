# 2026-09-09 — drained queue answers (verbatim)

## q-prompt-dir-notation-enforcement-test
Answer: When a convention is introduced into skill prompt prose (like the content-dir path notation), guard it with a stdlib-only test in the engine suite (plugins/s/skills/build/tests/) rather than shipping prose-only edits — unenforced prompt conventions erode as prompts evolve. Chosen for prompt-dir-notation: a line-level scan of skills/**/*.md requiring each .shipd/ mention to be exempt (~/.shipd home path, $SANDBOX, default-annotated) or covered by the file's canonical notation rule.

## q-prd-tier-section-registry
Answer: The PRD template tiers are additive supersets with house-style names: basic requires Problem, Solution, Success criteria; standard adds Users, Requirements, Non-goals; comprehensive adds Risks, Rollout, Open questions. Nesting keeps mid-interview tier escalation monotone and the names match the why-first house style (chosen by the user during prd-store planning).
