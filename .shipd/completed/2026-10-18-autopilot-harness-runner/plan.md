# autopilot-harness-runner
Status: verified
Theme: developer-experience
Planned-at: 2af8df9890f37c1d2bf226406ec35634388bc0ae
Gated-hash: c80eebf8547b

## Idea

Make the detached autopilot harness-agnostic: a runner registry that drives a
headless session in any supported harness, with OpenCode as the second runner
beside Claude Code.

### Motivation

`shipd autopilot` drives headless sessions by invoking `claude -p`, so an epic
can only be delivered on a machine with Claude Code and its quota. A user who
works in OpenCode — which ships a headless `opencode run` — cannot use the
autopilot at all, and the driver's argv, transcript parsing, and `/s:` prompt
vocabulary are all hard-coded to Claude.

### Details

- `session_driver.py`: a `RUNNERS` registry mapping a harness id to a runner
  that builds the argv, parses the transcript for the session id and result
  text, and maps the `/s:` command vocabulary to the harness's command form.
  `claude` (default) and `opencode` ship.
- `run_turn`/`run_turn_result` gain `harness="claude"`; `claude_bin` becomes
  `binary`, defaulting to the runner's own binary.
- `autopilot.py`: `--harness <id>` selects the runner (default `claude`), and
  the report names it.
- `evals/run.py`: unchanged — it keeps the default runner.
- `plugins/s/.claude-plugin/plugin.json`: the version bump this change owes.

Affected capabilities: `epic-autopilot` (modified). Impact: no new dependency;
a run without `--harness` behaves exactly as today.

### Non-goals

- No second runner beyond `opencode`; the registry makes a third a data edit.
- No harness-specific model ladder: the symbolic tier anchor stays as it is,
  and a runner passes whatever concrete model it is given through its own flag.
- No change to the in-session drive, the pipeline, the report shape, or the
  board.
- No change to the `/s:` skill surfaces themselves.

## Implementation

- **A runner is data plus three functions.** `session_driver.RUNNERS` maps an
  id to a record carrying `binary` (its default executable), `argv(...)` (the
  command line), `parse(stdout)` (session id and result text), and
  `rewrite(prompt)` (the `/s:` vocabulary). `runner_for(id)` returns it and
  raises a named error for an unknown id. Adding a harness is one record.
- **The Claude runner is today's behavior, lifted.** `argv` returns
  `[binary, "-p", prompt, "--output-format", "json", "--plugin-dir", <plugin>,
  "--permission-mode", "bypassPermissions"]` plus `--model` and `--resume`;
  `parse` reads the JSON object's `session_id` and `result`; `rewrite` returns
  the prompt unchanged (the plugin's `/s:` skills are the vocabulary).
- **The OpenCode runner is verified, not guessed.** `argv` returns
  `[binary, "run", "--format", "json", "--auto"]` plus `--model` and
  `--session`, with the prompt as the trailing positional. `parse` reads the
  JSONL stream: the last top-level `sessionID`, and the concatenated
  `part.text` of every `type == "text"` line. `rewrite` maps `/s:<command>` to
  `/shipd-<command>`, the OpenCode command name the harness installer writes.
  Observed live: `opencode run --format json "…"` emits one JSON object per
  line with a top-level `sessionID`, and `--session <id>` continues the
  conversation.
- **`--harness` is the only new control.** `autopilot.py`'s `--harness` picks
  the runner; `--claude-bin` becomes the binary override for whichever runner
  is selected, and `_session_extra_args` moves into the Claude runner (the
  plugin-dir and permission flags are Claude's). The run report names the
  harness so a driven session's provenance is unambiguous.
- **The grade-gated loop is unchanged.** `drive` still takes an injectable
  runner seam; only the turn function behind it changes harness. This keeps
  the loop's unit tests harness-free.
- **The version bump rides here.** `plugin.json` moves `0.6.324` → `0.6.325`.

Risk: an OpenCode session's permission prompts could stall an unattended turn;
`--auto` auto-approves what the harness does not explicitly deny, which the
plan relies on and the smoke test exercises.

## Readiness attestation

### Problem and motivation

The autopilot can only drive Claude Code, so a user whose work runs in OpenCode
cannot deliver an epic unattended at all.

Evidence:

- Epic `harness-agents`' sibling goal: shipd targets many harnesses, and
  `harness_registry` already names `opencode`.
- `session_driver.py`: `run_turn_result` builds `[claude_bin, "-p", …]` and
  parses Claude's JSON transcript.

### Scope and non-goals

A runner registry with `claude` and `opencode`, `--harness`, and the tests; the
in-session drive, the pipeline, and the model ladder stay out.

Evidence:

- In scope: `session_driver.py`, `autopilot.py`, `test_session_driver.py`,
  `test_autopilot.py`, `plugins/s/.claude-plugin/plugin.json`.
- Out of scope: the model ladder stays Claude-shaped; a harness-specific ladder
  is future work.

### Affected capabilities and files

One capability, `epic-autopilot`, modified; two engine modules, two test files,
and the version bump.

Evidence:

- Capability `epic-autopilot`: `shared-session-driver` (base 960a71884bad) and
  `session-turn-result-text` (base b53ee8e8158a) modified; `harness-runners`
  added.
- Edited: `session_driver.py`, `autopilot.py`, `test_session_driver.py`,
  `test_autopilot.py`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `opencode run --format json "…"` printed one JSON object per
  line with a top-level `sessionID`, and `opencode run --session <id> "…"`
  answered from the prior turn's context (the number 42).

### No open task-shaping decision

Every task-shaping decision is settled by the live OpenCode observation and the
existing driver.

Evidence:

- OpenCode's invocation, output shape, and resume: observed live.
- The Claude runner's flags and parsing: the existing `session_driver.py`.
- The prompt vocabulary: `harness_registry.command_id` names generated commands
  `shipd-<command>`, which is the OpenCode command form.
