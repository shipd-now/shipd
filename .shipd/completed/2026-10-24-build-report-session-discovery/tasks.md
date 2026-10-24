## 1. Session discovery

- [x] 1.1 [req: robust-source-discovery-and-degradation] In
      `plugins/s/skills/build/tests/test_build_report.py`, add failing tests
      with a temporary `CLAUDE_CONFIG_DIR`: an own slug directory holding an
      older session while `CLAUDE_CODE_SESSION_ID` names a session under an
      ancestor slug with a `subagents/agent-*.jsonl` (both counted); an
      explicit `--session` found only under an unrelated slug directory; and
      `--transcript` in an unrelated directory reading its sibling
      `subagents/`. Clear `CLAUDE_CODE_SESSION_ID` in existing tests that rely
      on newest-transcript discovery.
- [x] 1.2 [req: robust-source-discovery-and-degradation] In
      `plugins/s/skills/build/scripts/build_report.py`, default the session
      to `$CLAUDE_CODE_SESSION_ID`, make `discover_session` probe every
      candidate directory and then the transcript root for an explicit id,
      and read `--transcript` sub-agents beside the transcript, exactly per
      plan.md's Implementation, until 1.1 passes. Update the module
      docstring to describe the session-id lookup.

## 2. Version and verify

- [x] 2.1 [req: robust-source-discovery-and-degradation] Bump
      `plugins/s/.claude-plugin/plugin.json` from `0.6.345` to `0.6.346`.
- [x] 2.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and grep its output for `OK`/`FAILED`;
      rerun `build_report.py --since <window> --summary-only` from the main
      checkout and from a worktree and confirm non-zero tokens.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 46 | 2.7k |
| (no tool) | 0 | 603 |
| Agent | 2 | 32 |
| SubagentHandback | 2 | 32 |
| **Total** | 50 | 3.4k |
