# build-report-session-discovery
Status: verified
Theme: reliability
Planned-at: 0932716f7dec1e6345c98db0cf5dcb876a1e4038
Gated-hash: d9a2a984e369

## Idea

Make `build_report.py` read the transcript of the session that is running the
build, found by its session id, instead of the newest transcript in the first
slug directory that exists.

### Motivation

Every `/s:build` for about ten days reported `Tokens: 0↑ 0↓` with an empty
per-model table, so nobody can see what a build cost. Builds run from
`.worktrees/<change>` and from sub-agents, and the report picked a stale,
unrelated session transcript every time.

### Details

Reproduced on 2026-10-24 from the main checkout, in a session launched from
`/Users/mikkelbergmann/projects/workspaces/shipd` (session `cef3e875…`, 200 MB
transcript, live):

- `build_report.py --since 2026-10-24T05:31:15Z --json` printed
  `"session": "f072743d…"` with all-zero totals. That transcript lives in
  `~/.claude/projects/-Users-mikkelbergmann-projects-workspaces-shipd-shipd/`
  and was last written 2026-10-23 12:10, before the window.
- `--project-dir .worktrees/readme-update` picked the same stale session
  through the main-checkout rung.
- `--session cef3e875…` printed `Tokens: unavailable (transcripts not
  found)`: an explicit id is only looked up in the first existing directory.

Root cause: discovery stops at the first slug directory that exists (the
project's own, then the main checkout's) and takes its newest transcript,
even when the live session is elsewhere. A session launched from a parent
directory writes under the parent's slug, and old sessions keep the project's
own slug directory alive, so the ancestor rung is never reached. The session
id is ignored even though Claude Code exports it as `$CLAUDE_CODE_SESSION_ID`
to the session and its sub-agents.

Changes:

- `build_report.py` uses `$CLAUDE_CODE_SESSION_ID` as the session id when
  `--session` is not given.
- An explicit session id is looked up in every candidate directory (own slug,
  main checkout slug, ancestor slugs), then in every directory under
  `projects/`, instead of only the first existing directory.
- `--transcript` reads sub-agent transcripts beside the given transcript.
- `plugin.json` goes from `0.6.345` to `0.6.346`.

Affected capabilities: `build-telemetry` (modified
`robust-source-discovery-and-degradation`). Impact:
`plugins/s/skills/build/scripts/build_report.py`,
`plugins/s/skills/build/tests/test_build_report.py`,
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to discovery when no session id is known: the newest transcript
  in the first existing directory is still chosen.
- No change to aggregation, the `--since` window, or report formats.

## Implementation

- In `main()`, when `args.session` is empty, set it from
  `os.environ.get("CLAUDE_CODE_SESSION_ID")` (empty string counts as unset).
  Rejected: a new flag; the environment already carries the id, and the
  skill's commands need no edit.
- In `discover_session(project_dir, session)`, when `session` is given: walk
  the candidate directories in order (own slug, the main checkout slug when
  `project_dir` is a linked worktree, then each ancestor slug of the resolved
  root, nearest first) and return the first that holds
  `<session>.jsonl`. When none holds it, scan every directory in
  `<config_dir>/projects/` (sorted by name) for `<session>.jsonl` and return
  the first hit. When nothing holds it, return `(None, None, own)` as today.
  The id is the validation, so no working-directory check applies.
- When `session` is not given, discovery is unchanged.
- In `main()`'s `--transcript` branch, read sub-agents from
  `os.path.dirname(os.path.abspath(main_path))` instead of
  `transcript_dir(project_dir)`.
- `dashboard.py` calls `discover_session(location, session_id or None)` and
  gets the wider lookup for free; it needs no edit.

Risk: a full `projects/` scan costs one `isfile` per project directory, about
100 on this machine; it runs only when the id is not in a candidate
directory. Tests must clear `CLAUDE_CODE_SESSION_ID` where they rely on
newest-transcript discovery, since the suite itself may run inside a session.
