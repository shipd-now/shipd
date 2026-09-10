# guardrail-hook

## MODIFIED Requirements

### Requirement: Hook registration in the plugin
id: guardrail-hook-registration
base: 1a42c5fe8377

The plugin SHALL ship a `hooks/hooks.json` at the plugin root that registers
exactly three events: a `PreToolUse` hook and a `PostToolUse` hook, each with
matcher `Edit|Write` and each with the single command entry
`{"type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py\""}`,
and a `SessionStart` hook with the single command entry
`{"type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/voice_digest.py\""}`.

#### Scenario: hooks.json declares the three events
- **WHEN** `plugins/s/hooks/hooks.json` is parsed as JSON
- **THEN** it declares exactly the events `PreToolUse`, `PostToolUse`, and
  `SessionStart` — the tool events each with matcher `Edit|Write` and a
  command invoking `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py`
  via `python3`, and `SessionStart` with a command invoking
  `${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/voice_digest.py` via
  `python3`
