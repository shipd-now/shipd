# Queue

## q-prompt-dir-notation-enforcement-test
- Asked: 2026-09-07 shipd/.worktrees/prompt-dir-notation
- Question: Should the prompt-dir-notation change add a stdlib-only engine test (plugins/s/skills/build/tests/) that scans every skills/**/*.md line mentioning .shipd/ and fails unless the line is exempt (fixed ~/.shipd home path, $SANDBOX onboarding path, a default-annotated mention, or the file carries the canonical notation rule), or ship as prose-only edits with no enforcement?
- Options: add the enforcement test | prose-only, no test
- Recommendation: add the enforcement test
- Answer: When a convention is introduced into skill prompt prose (like the content-dir path notation), guard it with a stdlib-only test in the engine suite (plugins/s/skills/build/tests/) rather than shipping prose-only edits — unenforced prompt conventions erode as prompts evolve. Chosen for prompt-dir-notation: a line-level scan of skills/**/*.md requiring each .shipd/ mention to be exempt (~/.shipd home path, $SANDBOX, default-annotated) or covered by the file's canonical notation rule.
