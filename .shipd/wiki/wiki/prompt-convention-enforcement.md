# prompt-convention-enforcement

Standing rule: when a convention is introduced into skill prompt prose (like
the content-dir path notation), guard it with a stdlib-only test in the
engine suite (`plugins/s/skills/build/tests/`) rather than shipping
prose-only edits — unenforced prompt conventions erode as prompts evolve.
Chosen for prompt-dir-notation: a line-level scan of `skills/**/*.md`
requiring each `.shipd/` mention to be exempt (`~/.shipd` home path,
`$SANDBOX`, default-annotated) or covered by the file's canonical notation
rule. The same pattern recurs across the plugin: the harness bodies 1:1
guard, the PRD template drift guard — a doc-or-prompt convention is real
only when a test can refuse its violation. Drained from
q-prompt-dir-notation-enforcement-test.

Backed by: completed/prompt-dir-notation, verified/harness-command-bodies,
verified/shipd-prd (prd-template-files).
