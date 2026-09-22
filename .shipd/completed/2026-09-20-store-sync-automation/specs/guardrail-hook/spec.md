## MODIFIED Requirements

### Requirement: Hook registration in the plugin
id: guardrail-hook-registration
base: 8dc369fb7ad6
Dropped: hooks.json declares the three events

The plugin SHALL ship a `hooks/hooks.json` at the plugin root that registers
exactly four events: a `PreToolUse` hook and a `PostToolUse` hook, each with
matcher `Edit|Write` and each with the single command entry
`{"type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py\""}`,
a `SessionStart` hook with two command entries — one invoking
`${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/voice_digest.py` and one
invoking `${CLAUDE_PLUGIN_ROOT}/skills/workspace/scripts/store_sync.py`, each
via `python3` — and a `SessionEnd` hook with the single command entry
invoking `${CLAUDE_PLUGIN_ROOT}/skills/workspace/scripts/store_sync.py` via
`python3`.

#### Scenario: hooks.json declares the four events
- **WHEN** `plugins/s/hooks/hooks.json` is parsed as JSON
- **THEN** it declares exactly the events `PreToolUse`, `PostToolUse`,
  `SessionStart`, and `SessionEnd` — the tool events each with matcher
  `Edit|Write` and a command invoking
  `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py` via `python3`,
  `SessionStart` with commands invoking
  `${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/voice_digest.py` and
  `${CLAUDE_PLUGIN_ROOT}/skills/workspace/scripts/store_sync.py` via
  `python3`, and `SessionEnd` with a command invoking
  `${CLAUDE_PLUGIN_ROOT}/skills/workspace/scripts/store_sync.py` via
  `python3`
