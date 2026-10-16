# Tasks — statusline-context-colour

- [x] 1 [req: statusline-rendering] In `plugins/s/skills/build/tests/test_statusline.py`, add tests on the raw, ANSI-preserving output: `used_percentage` 50, 51, 76, 91, 96 wrap the context segment in `\033[94m`, `\033[38;5;208m`, `\033[38;5;196m`, `\033[38;5;160m`, `\033[38;5;124m` respectively, each followed by `\033[0m`; 75 stays orange and 95 stays darker red; no `used_percentage` emits none of those codes. Then implement the color chain in `plugins/s/integrations/statusline.sh` per `plan.md` `## Implementation`. The whole file passes.
- [x] 2 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` from `0.6.308` to `0.6.309`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 12 | 3.8k |
| Agent | 2 | 631 |
| (no tool) | 0 | 256 |
| SubagentHandback | 2 | 32 |
| **Total** | 16 | 4.7k |
