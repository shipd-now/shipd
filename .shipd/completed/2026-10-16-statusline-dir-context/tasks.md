# Tasks — statusline-dir-context

- [x] 1 [req: statusline-rendering] In `plugins/s/skills/build/tests/test_statusline.py`, extend `run_line`/`rendered` with optional `home` (sets `HOME` in the child env) and `context` (adds `context_window.used_percentage` to the payload) parameters, then add a `TrailingSegmentsTest` class covering each new scenario in the change's delta: directory under home renders as `~/...`, bare home renders `~`, directory outside home renders unchanged, percentages 0/25/50/100 render `░░░░ 0%`/`█░░░ 25%`/`██░░ 50%`/`████ 100%`, a fractional `37.9` renders `█░░░ 37%`, a value above 100 clamps to `████ 100%`, a missing `context_window` and a `null` `used_percentage` omit the context segment, and the segments trail the `no active specs` and `none selected` lines. Run the file and observe the new tests fail.
- [x] 2 [req: statusline-rendering] In `plugins/s/integrations/statusline.sh`, implement the trailing directory and context segments per `plan.md` `## Implementation`, append the suffix to all three print sites, and update the header comment's Output description. The whole `test_statusline.py` passes.
- [x] 3 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` from `0.6.303` to `0.6.304`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 20 | 5.8k |
| Agent | 2 | 677 |
| AskUserQuestion | 1 | 609 |
| (no tool) | 0 | 88 |
| SubagentHandback | 2 | 31 |
| **Total** | 25 | 7.2k |
