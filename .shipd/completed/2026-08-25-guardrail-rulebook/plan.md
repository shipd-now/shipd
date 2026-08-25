# guardrail-rulebook
Status: verified

## Idea

Adopt the transferable parts of oh-my-pi's stream-rule design into the
guardrail hook: rules become user-maintainable markdown files with frontmatter,
and a new `remind` mode delivers non-blocking guidance through PostToolUse
instead of denying.

### Motivation

Custom guardrail rules currently live as JSON in `.shipd-config.json`, which
forces regex double-escaping and squeezes prose messages into string fields,
and the hook can only hard-deny — there is no channel for guidance too fuzzy to
block on. oh-my-pi's rulebook (markdown rules) and non-interrupting reminder
injection both have documented Claude Code equivalents we can adopt.

### Details

- Rule definitions move to markdown files (`<name>.md`, flat frontmatter +
  message body) discovered from three sources: the repo's
  `<content-dir>/rules/`, the user's `~/.shipd/rules/`, and the plugin's own
  `hooks/rules/` — where the three built-ins now live as ordinary rule files.
- New `mode: remind` rules fire on a PostToolUse hook as
  `additionalContext` — the edit lands, the guidance reaches the model — with
  once-per-session default dedup and an optional `cooldown: <seconds>`.
- The config `guardrails` key keeps `false` and `disable`; its `rules` member
  is removed (the markdown rulebook supersedes it).

Affected capabilities: `guardrail-hook` (modified), `shipd-config` (modified).
Impact: `plugins/s/skills/build/scripts/guardrails.py`,
`plugins/s/hooks/hooks.json`, new `plugins/s/hooks/rules/*.md` (3),
`tests/test_guardrails.py`, `.shipd/README.md`,
`references/shipd.config.example.json`, `plugin.json` (version 0.6.153); no
new dependencies.

### Non-goals

- No mid-stream abort/retry (true TTSR) — the Claude Code hook API exposes no
  stream events; PreToolUse/PostToolUse remain the interception points.
- No structural/AST matching — regex only, stdlib-only per the constitution.
- No ingestion of other tools' rule locations (Cursor, Windsurf, Cline).
- No CLI verb for managing rules — files are edited directly.

## Implementation

- **Remind channel: PostToolUse `additionalContext`.** Verified against the
  hooks reference this session (docs agent, code.claude.com/docs/en/hooks.md):
  PostToolUse supports
  `{"hookSpecificOutput": {"hookEventName": "PostToolUse",
  "additionalContext": <text>}}`, delivered to the model non-blockingly; the
  payload carries `session_id`, `cwd`, `tool_input`, and
  `hook_event_name`, and one script may serve both events registered in one
  `hooks.json`. Rejected: PostToolUse `decision: "block"` — it signals a
  concern and still undoes nothing; `additionalContext` is the neutral
  reminder channel.
- **One script, branched on `hook_event_name`.** PreToolUse evaluates only
  `deny` rules; PostToolUse evaluates only `remind` rules. Same added-line
  extraction both sides.
- **Rule file format** — markdown, name from the filename stem, frontmatter
  between `---` lines parsed by a new tiny stdlib parser (flat `key: value`
  per line, first-colon split; no YAML library exists in the engine and none
  may be added). Keys: `pattern` (required), `mode` (`deny` default,
  `remind`), `files` (comma-separated globs), `cooldown` (positive integer
  seconds, remind only). The body after the frontmatter is the corrective
  message. Malformed files are skipped, never fatal.
- **Built-ins become plugin rule files** under `plugins/s/hooks/rules/` with
  the same three patterns and messages — one format everywhere, readable and
  copyable by users; `guardrails.py` carries no in-code rule content and
  resolves the plugin rules directory relative to its own file location.
- **Discovery and precedence**: walk from the payload `cwd` (fallback:
  process cwd) parent-by-parent collecting `<content-dir>/rules/*.md` (the
  content-dir name from the resolved config `dir`), then `~/.shipd/rules/`,
  then the plugin's `hooks/rules/`; deduplicate by rule name, first source
  wins — so a repo rule overrides a user rule overrides a built-in. Verified
  premise: `spec_common.load_layered_config(start)` walks exactly this chain
  and `resolve_config(start)` returns a `(merged, provenance)` tuple (both
  run and observed this session).
- **Config keeps the kill-switches only.** `guardrails: false` and `disable`
  stay in config — a kill-switch must beat every file source. The `rules`
  member is removed per the user's "swap" instruction; an object still
  carrying one has that member ignored (fail-open, no error), and the README
  documents the swap. Rejected: supporting both authoring surfaces — two
  sources of truth for the same rule set.
- **Cooldown state** at `~/.shipd/guardrails/<session_id>.json` (rule name →
  last-fire epoch seconds). Default: a remind rule fires once per session.
  `cooldown: N` re-arms N seconds after the last fire. No `session_id` in the
  payload → fire without recording. All state I/O failures fail open.
- **Snapshot caveat**: live only after the version bump (0.6.153) merges and
  `claude plugin update s@shipd` runs.

Risk: remind rules becoming noise — guarded by once-per-session default and
per-rule cooldown. Risk: a user's existing config `rules` silently stops
applying — accepted: the member shipped in 0.6.152 hours before this change
with no adopters, and the README states the replacement.
