# Tasks — transcript-ancestor-discovery

## 1. Ancestor-slug transcript discovery

- [x] 1.1 [req: robust-source-discovery-and-degradation] Add a new test class
      to `plugins/s/skills/build/tests/test_build_report.py`, mirroring
      `TranscriptDiscoveryFallbackTest`'s `CLAUDE_CONFIG_DIR` isolation and
      `_make_worktree`/`_slug_dir` helpers, covering `br.discover_session`:
      (a) with neither own nor main slug dir present, the newest ancestor-slug
      transcript whose trailing JSONL record carries a `cwd` inside the
      project root is returned as `(sid, path, ancestor_tdir)`; (b) a
      newer transcript in the ancestor dir whose trailing `cwd` is a different
      project is skipped in favor of an older matching one; (c) when the own
      slug dir exists it still wins and no ancestor probe happens; (d) an
      explicit `session=` id resolves to `<session>.jsonl` in the ancestor dir
      even without any `cwd` record; (e) with no candidate anywhere the result
      is `(None, None, <own-slug path>)`. Run the class and observe it fail —
      `discover_session` does not exist yet.
- [x] 1.2 [req: robust-source-discovery-and-degradation] Implement
      `_tail_cwd_within(path, root, tail_bytes=65536)` in
      `plugins/s/skills/build/scripts/build_report.py`: read the last
      `tail_bytes` bytes of `path`, split into lines, scan complete lines
      backwards, JSON-parse each until one carries a `"cwd"` key, and return
      whether `os.path.abspath(cwd)` equals `root` or sits under `root + os.sep`;
      return `False` on an unreadable file, no parseable line, or no `cwd`.
- [x] 1.3 [req: robust-source-discovery-and-degradation] Implement
      `discover_session(project_dir, session=None)` in
      `plugins/s/skills/build/scripts/build_report.py` returning
      `(session_id, main_path, tdir)`: (1) when the own slug dir
      (`config_dir()/projects/project_slug(project_dir)`) is a directory,
      return `find_active_session(own, session)` plus that dir; (2) else when
      the resolved root (`resolve_project_root(project_dir)`) differs and its
      slug dir exists, same with that dir; (3) else walk
      `os.path.dirname` ancestors of the resolved root up to the filesystem
      root, nearest first, and in each existing slug dir: with `session` given
      return it when `<session>.jsonl` is a file there; otherwise scan that
      dir's `*.jsonl` newest-mtime-first and return the first passing
      `_tail_cwd_within(candidate, resolved_root)`; (4) no match →
      `(None, None, <own slug path>)`. Also update the module docstring's
      "Transcript layout" note to mention the ancestor-launch fallback.
- [x] 1.4 [req: robust-source-discovery-and-degradation] In
      `build_report.py`'s `main()`, replace the no-`--transcript` branch's
      `transcript_dir` + `find_active_session` pair with
      `session_id, main_path, tdir = discover_session(args.project_dir,
      args.session)`, keeping the existing `paths` assembly and
      `subagent_transcripts(tdir, session_id)` call unchanged. Confirm the
      tests from 1.1 now pass.
- [x] 1.5 [req: robust-source-discovery-and-degradation] In
      `plugins/s/skills/build/scripts/dashboard.py`, switch
      `_resolve_member_transcript` to
      `sid, path, tdir = br.discover_session(location, session_id or None)`
      inside the existing `try/except OSError`, preserving its
      `(tdir, sid, path)` return shape and `None` fallback.
- [x] 1.6 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      `0.6.168`, then run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v` and
      confirm the whole suite passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 57 | 9.7k |
| Write | 2 | 4.2k |
| Edit | 7 | 2.3k |
| Agent | 2 | 1.2k |
| (no tool) | 0 | 354 |
| Read | 11 | 338 |
| ToolSearch | 1 | 25 |
| **Total** | 80 | 18.1k |
