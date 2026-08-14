## 1. Brief grammar documentation

- [x] 1.1 [req: video-brief-format] In `.shipd/README.md`, add `video/` to the
      content-directory layout listing (alongside the `research/` entry) as the
      reserved home of video intent briefs.
- [x] 1.2 [req: video-brief-format] In `.shipd/README.md`, document the brief
      grammar next to the research-report section: the `# <title>` line, the
      required `Video:` header and optional `Bundle:`/`Decider:` headers, the
      required `## Speakers`, `## Intents`, and `## Sources` sections, the
      optional `## Open questions` and `## Gaps & caveats` sections, the
      per-intent citation rule, and the timestamped source-entry rule.

## 2. Video brief lint mode

- [x] 2.1 [req: video-brief-validation, video-brief-format] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add tests calling
      `spec_lint.lint_video` covering a clean brief (no findings), a missing
      `Video:` header, an intent with no citation marker, a source entry with no
      bracketed timestamp, an unresolved `[4]` marker over three sources, a
      fenced code block containing `items[0]` (no finding), and an extra level-2
      section (no finding). Run them and observe they fail — `lint_video` does
      not exist yet.
- [x] 2.2 [req: video-brief-validation] In
      `plugins/s/skills/build/scripts/spec_lint.py`, add `lint_video(root,
      slug, errors)` beside `lint_research`, resolving the brief at
      `<content-dir>/video/<slug>/brief.md` and reusing `_section_lines`,
      `SOURCE_ENTRY_RE`, and `_citation_markers_outside_code`; every finding
      names the brief path. Confirm the 2.1 tests pass.
- [x] 2.3 [req: video-brief-validation] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add a test asserting
      `lint_library` produces no finding while an invalid `brief.md` sits under
      the content directory's `video/` folder, and that `spec_lint.py` exposes
      no command-line mode for the video checks.

## 3. Video emit verb

- [x] 3.1 [req: staged-emission] In
      `plugins/s/skills/build/tests/test_spec_emit.py`, add tests for
      `spec_emit.py video <slug> --from <file>` covering a clean brief
      (installed at `<content-dir>/video/<slug>/brief.md`, exit zero), a brief
      with an uncited intent (findings printed, non-zero, destination absent),
      and an existing destination refused without `--replace`. Run them and
      observe they fail — the verb does not exist yet.
- [x] 3.2 [req: staged-emission] In
      `plugins/s/skills/build/scripts/spec_emit.py`, add `emit_video(root,
      slug, src, replace)` mirroring `emit_research`, using `_install_dir` and
      validating with `spec_lint.lint_video`. Confirm the 3.1 tests pass.
- [x] 3.3 [req: staged-emission] In
      `plugins/s/skills/build/scripts/spec_emit.py`, register the `video`
      subparser (positional `slug`, required `--from`, `--replace`), dispatch it
      to `emit_video`, and add the verb to the module docstring's verb list.

## 4. Mediated read verb

- [x] 4.1 [req: mediated-read-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add tests for `cat
      video <slug>` asserting one `--- <relpath>` separator followed by the
      brief's content, and a non-zero exit naming a missing brief. Run them and
      observe they fail.
- [x] 4.2 [req: mediated-read-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, extend the `cat` kind
      handling beside the `research` branch (around line 929) with a `video`
      branch resolving `<content-dir>/video/<slug>/brief.md`, and add `video` to
      the `cat` kind choices (around line 1665). Confirm the 4.1 tests pass.

## 5. Ship

- [x] 5.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.75` to `0.6.76`.
- [x] 5.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the whole suite passes.
