# transcript-ancestor-discovery
Status: verified

## Idea

Teach the build-telemetry transcript discovery to find sessions launched from
an ancestor directory of the project, so builds stop reporting
`Tokens: unavailable (transcripts not found)`.

### Motivation

A Claude Code session launched from a parent directory (e.g. `~/projects`)
writes its transcripts under the *launch* directory's path slug, but
`build_report.py` only probes the project directory's own slug and its
linked-worktree main checkout's slug — so a build run in a repo the session
`cd`-ed into reports `Tokens: unavailable (transcripts not found)` even though
the transcript exists (reproduced against `~/projects/fresh-careers`).

### Details

- Extend transcript discovery in
  `plugins/s/skills/build/scripts/build_report.py` with an ancestor-directory
  fallback: when neither the project dir's own slug directory nor the main
  checkout's exists, walk the resolved root's ancestors nearest-first, probing
  each ancestor's slug directory.
- Validate ancestor-directory candidates by transcript content: select the
  newest session whose trailing records carry a `cwd` at or under the resolved
  project root, so a foreign project's session sharing the ancestor directory
  is never counted.
- Route `dashboard.py`'s live-sampling transcript resolver through the same
  discovery.

Affected capabilities: `build-telemetry` (modified). Impact:
`plugins/s/skills/build/scripts/build_report.py`,
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests/test_build_report.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No change to the own-slug and main-checkout preference order — a session
  launched inside the project (or its main checkout) resolves exactly as
  before, with no new cwd validation on those rungs.
- No environment-variable or harness-provided transcript-path plumbing — the
  harness exposes the transcript path to hooks and the statusline, not to the
  Bash calls that run the report.
- No change to token aggregation, timing, rendering, or logging.

## Implementation

- **Ancestor slug walk as a third fallback.** A new
  `discover_session(project_dir, session=None)` returns
  `(session_id, main_path, tdir)`: (1) the own slug directory when it exists,
  via the existing `find_active_session` semantics, unchanged; (2) else the
  resolved main checkout's slug directory, unchanged; (3) else walk
  `os.path.dirname` ancestors of `resolve_project_root(project_dir)` up to the
  filesystem root, nearest first, probing each ancestor's slug directory; (4)
  nothing found → `(None, None, <own-slug sentinel>)` so degradation is
  unchanged. Rejected: env-var plumbing of the transcript path — nothing
  reliable is available in the report's execution environment.
- **Content validation only on the ancestor rung.** An ancestor slug directory
  aggregates sessions from many projects, so newest-mtime alone is unsafe
  there: candidates are ordered newest-first and the first transcript whose
  tail carries a `cwd` at or under the resolved project root wins. Implemented
  by a tail reader `_tail_cwd_within(path, root, tail_bytes=65536)` that reads
  the last `tail_bytes` of the file, scans complete lines backwards, and
  returns the containment verdict of the first parseable record carrying a
  `cwd`; an unreadable file or absent `cwd` is no match. Rejected: validating
  the own/main rungs too — that would change verified behavior for the common
  case and is out of scope for this bug.
- **Explicit session id honored on the ancestor rung**: when `session` is
  given, each candidate directory is probed for `<session>.jsonl` directly —
  the explicit id is itself the validation, so no cwd check runs.
- **Wiring.** `build_report.main()`'s no-`--transcript` branch calls
  `discover_session` in place of the `transcript_dir` + `find_active_session`
  pair, keeping the `subagent_transcripts(tdir, session_id)` call on the
  returned directory (the subagents live beside the main transcript, so the
  ancestor directory resolves them too). `dashboard.py`'s
  `_resolve_member_transcript` switches to the same call.
  `transcript_dir`/`find_active_session` remain exported for the sampling
  layer's tail keys and compatibility.
- **Runnable premise (verified).** `build_report.py --since
  2026-09-01T00:00:00Z --summary-only` run from `~/projects/fresh-careers`
  prints `Tokens: unavailable (transcripts not found)` and exits 0, while that
  repo's live session transcript exists at
  `~/.claude/projects/-Users-mikkelbergmann-projects/26b50245-….jsonl` with a
  trailing `cwd` of `/Users/mikkelbergmann/projects/fresh-careers` — the own
  and main slug directories for that repo do not exist.
- **Risk:** two concurrent sessions on the same repo launched from the same
  ancestor both validate; the newest-mtime tiebreak picks the actively-writing
  one, matching the existing active-session heuristic, and `--since` scoping
  bounds any residual miscount.
