# context-budget
Status: ready
Theme: developer-experience

## Introduction

Every Claude Code session with shipd installed pays a context tax before the user types anything. The plugin lists 31 skills whose frontmatter descriptions total about 20 KB, plus three agents and SessionStart hook output. The harness generator's `claude-code` target also writes 30 command files to `~/.claude/commands/shipd/`, so every command is listed twice, as `s:*` and `shipd:*`. In a live session, 11 `s:*` skills currently show with no description at all, which suggests the listing hits a size budget and the duplicates crowd real descriptions out.

Nobody can say how big that tax is. A first headless probe read 26,263 input tokens for a trivial turn with the plugin on and 25,439 with it off. That 824-token gap is too small to be believable for 31 skills, so the obvious A/B method cannot be trusted yet.

This epic builds a measurement first, then cuts the tax and keeps it cut:

- A spike settles a trustworthy way to measure the context shipd adds, per contributor.
- A live meter turns that method into a repeatable, on-demand tool.
- A free static estimate, calibrated against the meter, guards the budget in CI with a ratchet.
- Three optimisations remove the duplicate listing, trim skill descriptions, and slim SessionStart output, each proven by the meter.

Success criteria: the meter reports a per-contributor breakdown that adds up to the plugin-on minus plugin-off total within a stated tolerance. Each optimisation PR shows a before/after meter reading. CI fails when the static estimate grows past the ratchet.

### Non-goals

- No measurement or optimisation for other harnesses (opencode, agy, and the rest); this epic covers Claude Code sessions only.
- No live headless sessions in CI; the live meter runs on demand.
- No fixed token budget; the ratchet only stops growth.
- No change to what any skill does; descriptions may shrink, behaviour may not.

## Decisions

- **Scope is a Claude Code session.** Installed context means what `plugins/s` loads (skill listings, agent definitions, hook output) plus the generated `~/.claude/commands/shipd/` duplicates. Other harnesses are out of scope.
- **The meter is a headless main session, never a sub-agent.** Measurements come from `claude -p --output-format json`, reading `usage.input_tokens + cache_creation_input_tokens + cache_read_input_tokens` on a fixed trivial prompt. A sub-agent's context is built differently, so it is not representative.
- **Measurement runs isolated from the user's own setup.** Each run uses a clean config so other user plugins, user skills, and MCP servers cannot leak into the number. The spike chooses the mechanism and the later members reuse it.
- **One contributor vocabulary.** The meter, the static estimate, and the ratchet name contributors with the same keys: `skills`, `agents`, `session-start`, `command-duplicates`, and `other`. A new contributor is added to all three at once.
- **Tooling lives under `evals/`.** The live meter and the static estimate are repository dev tools, stdlib-only Python 3 like the rest of `evals/`, and reuse `evals/run.py`'s headless launch where it fits. They ship nothing to users, so they need no plugin version bump.
- **Static in CI, live on demand.** CI runs only the static estimate, through `evals/tests` (already wired into `ci.yml`). The live meter is never a CI step.
- **Ratchet, not target.** The static estimate's checked-in baseline is a ceiling. CI fails when the estimate exceeds it. Each optimisation lowers the ceiling in its own PR.
- **Every optimisation proves itself.** An optimisation member runs the live meter before and after, records both readings in its PR body, and lowers the ratchet. If the meter shows no real gain, the member is dropped rather than shipped.

## Design

The pieces form a measure-then-cut pipeline:

```
context-measure-spike ──► context-meter ──► context-static-estimate (CI ratchet)
                               │
                               ├──► dedupe-claude-commands ─┐
                               ├──► skill-description-budget├─► each lowers the ratchet
                               └──► session-start-slim ─────┘
```

- **Spike.** Proves that per-contributor toggles really take effect (plugin off, generated commands off, hooks off), measures run-to-run variance, and explains the 824-token gap. It installs its findings as a `docs` report through the emit engine, recording the chosen method and the first raw baseline.
- **Meter.** Runs the contributor matrix live and prints a table plus JSON: per-contributor tokens, total, and variance. The spike's report is its contract.
- **Static estimate.** Counts what each contributor would inject (description characters, hook output bytes, generated command descriptions), converts to tokens with a factor calibrated against one meter run, and compares against a checked-in ceiling in an `evals/tests` test.
- **Optimisations.** Each targets one contributor key:
  - `dedupe-claude-commands` stops writing duplicate command files for Claude Code when the plugin is installed, and retires the stale ones through the generator's marker-owned removal.
  - `skill-description-budget` shortens descriptions to a per-skill budget while keeping each trigger phrase, enforced by a test.
  - `session-start-slim` cuts the SessionStart hook output.

The seam between measurement and optimisation is the contributor vocabulary. Optimisation members can run in any order once the meter exists. They reach CI through the static estimate's ratchet.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk | After |
| --- | --- | --- | --- | --- | --- | --- |
| context-measure-spike | Validate a trustworthy per-contributor headless measurement and record the method and first baseline as a report | low | medium | high | low | |
| context-meter | Live on-demand meter under evals/ that runs the contributor matrix and prints a per-contributor table and JSON | medium | medium | medium | low | context-measure-spike |
| context-static-estimate | Free static estimate calibrated to the meter, with a checked-in ceiling enforced by an evals/tests ratchet in CI | medium | low | medium | low | context-meter |
| dedupe-claude-commands | Stop generating duplicate ~/.claude/commands/shipd files for Claude Code when the plugin is installed, and retire stale ones | low | medium | low | medium | context-meter |
| skill-description-budget | Trim every skill description to a per-skill budget, keeping trigger phrases, with a test enforcing the budget | medium | medium | low | medium | context-meter |
| session-start-slim | Cut the SessionStart hook output that every session loads | low | low | low | low | context-meter |
