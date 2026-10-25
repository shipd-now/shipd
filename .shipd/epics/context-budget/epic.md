# context-budget
Status: complete
Theme: developer-experience

## Introduction

Claude Code fits every skill's listing into 1% of the context window and trims descriptions that overflow. A headless `/context` reading on a 1M-token window shows the Skills category at 10.0k tokens, exactly that cap. shipd's share is about 7k tokens: roughly 5.5k for the 31 `s:*` skills, 1.3k for 30 duplicate `shipd:*` commands the harness generator writes to `~/.claude/commands/shipd/`, plus agents and SessionStart text.

The token cost is small, but the overflow is a real problem. Skills such as `s:initiative`, `s:memory`, and `s:onboard` already list at under 20 tokens, meaning their descriptions were dropped, so Claude rarely picks them on its own. On a 200k-token window the cap is about 2k tokens, and most shipd skills would lose their descriptions.

This epic frees the listing with two fixes:

- Stop writing the duplicate `shipd:*` command and agent files when the `s@shipd` plugin is installed.
- Trim every skill description to a short budget, keeping each trigger phrase.

Success criteria: a before and after `/context` reading on the build machine shows no `shipd:*` rows, and every `s:*` skill listed with a description (none at under 20 tokens) or a lower Skills total.

### Non-goals

- No custom measurement tooling, live meter, static estimate, or CI ratchet; `/context` is the measurement.
- No measurement or optimisation for other harnesses (opencode, agy, and the rest).
- No change to SessionStart output; it costs about 120 tokens.
- No change to what any skill does; descriptions shrink, behaviour does not.

## Decisions

- **Scope is a Claude Code session.** The fixes target what loads into a Claude Code session: the plugin's skill listing and the generated `~/.claude/commands/shipd/` duplicates.
- **`/context` is the proof.** Each member records a before and after reading of `claude -p "/context" --output-format json --max-turns 1`, run from an empty scratch directory, in its PR body: the Skills category total and the per-skill rows it changes.
- **A member proves the contributor it removes or shrinks.** A removal shows its rows gone; a trim shows descriptions restored or the Skills total lower. A member that shows neither is dropped rather than shipped.
- **Trigger phrases survive.** No change may drop or reword a skill's trigger phrases.

## Design

The two members are independent and can ship in either order:

- `dedupe-claude-commands` changes the harness generator: in user mode, with the plugin installed and enabled, it writes no claude-code command or agent files and retires the marker-owned ones already there.
- `skill-description-budget` rewrites each `SKILL.md` description to the skill's harness-body one-liner plus its trigger phrases, under a per-skill character budget a test enforces.

Together they shrink shipd's share of the listing until every skill keeps its description.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk | After |
| --- | --- | --- | --- | --- | --- | --- |
| dedupe-claude-commands | Stop generating duplicate ~/.claude/commands/shipd files for Claude Code when the plugin is installed, and retire stale ones | low | medium | low | medium | |
| skill-description-budget | Trim every skill description to a per-skill budget, keeping trigger phrases, with a test enforcing the budget | medium | medium | low | medium | |

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 177 | 78.0k |
| SubagentHandback | 7 | 7.4k |
| Agent | 10 | 5.0k |
| Monitor | 6 | 1.5k |
| Skill | 5 | 1.4k |
| (no tool) | 0 | 1.4k |
| ToolSearch | 3 | 577 |
| SendMessage | 1 | 274 |
| ListAgents | 1 | 110 |
| **Total** | 210 | 95.7k |
