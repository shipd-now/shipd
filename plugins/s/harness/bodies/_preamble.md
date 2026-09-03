Work from the repository root and run the numbered workflow below in order.

Resolve the shipd engine once, before any step needs it — the newest installed
plugin snapshot carries both the engine scripts and the `shipd` binary:

```sh
S="$HOME/.claude/plugins/cache/shipd/s/$(ls "$HOME/.claude/plugins/cache/shipd/s" | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)/skills/build/scripts"
```

Read-only reports come from `shipd <verb>` — `status`, `list`, `lint`, `epic`,
`workspace`, `doctor` — using the binary on PATH, or `"$S/../../../bin/shipd"`
when it is not installed there. Every spec-library mutation runs a script
directly, `python3 "$S/<script>.py" …` — the binary's verbs stay read/inspect
plus a few deliberate user-domain exceptions (`worktree` among them).
