## 1. Report lint checks

- [x] 1.1 [req: research-report-validation] Add research-check tests to
      `plugins/s/skills/build/tests/test_spec_lint.py`: a conforming report
      (title, `[1]` marker, `## Sources` with `1. …`) yields no findings; a
      report with markers but no `## Sources` section errors; a report citing
      `[4]` over three sources errors naming `[4]`; a report with zero
      citation markers errors; `items[0]` inside a fenced code block trips
      nothing; `lint_library` produces no finding for an invalid file under
      `.shipd/research/`. Run them and observe them fail — `lint_research` does
      not exist yet.
- [x] 1.2 [req: research-report-validation] Implement
      `lint_research(root, slug, errors)` in
      `plugins/s/skills/build/scripts/spec_lint.py`: resolve the report via
      `sc.specs_dir(root)` + `research/<slug>/report.md`; check line 1 is a
      non-empty `# <title>`; collect numbered entries (`^N. `) under
      `## Sources` (at least one required); collect inline `[n]` markers
      outside fenced code blocks and not followed by `(`; require at least
      one marker and that every marker's number appears in the sources list;
      every finding names the report path. Do not call it from
      `lint_library`. Confirm the 1.1 tests pass.

## 2. Emit engine research mode

- [x] 2.1 [req: staged-emission] Add research-mode tests to
      `plugins/s/skills/build/tests/test_spec_emit.py`: a clean staged
      report installs to `.shipd/research/<slug>/report.md` with exit 0; a
      staged report with an unresolved marker prints findings, exits
      non-zero, and leaves no `.shipd/research/<slug>/`; an existing
      destination is refused without `--replace` and replaced with it. Run
      them and observe them fail.
- [x] 2.2 [req: staged-emission] Implement `emit_research(root, slug, src,
      replace)` in `plugins/s/skills/build/scripts/spec_emit.py`, modeled
      exactly on `emit_epic` (single-file copy into
      `<content-dir>/research/<slug>/report.md`, validate via
      `sl.lint_research`); add the `research` subparser (`slug`, `--from`,
      `--replace`), dispatch it in `main`, and add the mode to the module
      docstring. Confirm the 2.1 tests pass.

## 3. Mediated research reads

- [x] 3.1 [req: mediated-read-verb] Add cat-research tests to
      `plugins/s/skills/build/tests/test_spec_status.py`: `cat research
      <slug>` on an installed report prints one `--- <relpath>` separator
      followed by the content; an unknown slug exits non-zero naming it. Run
      them and observe them fail.
- [x] 3.2 [req: mediated-read-verb] Extend `cmd_cat` in
      `plugins/s/skills/build/scripts/spec_status.py` with the `research`
      kind resolving `<content-dir>/research/<slug>/report.md`, add
      `research` to the cat subparser `choices`, and update the unknown-kind
      error message. Confirm the 3.1 tests pass.

## 4. The /s:research skill

- [x] 4.1 [req: research-skill-pipeline, research-report-content] Author
      `plugins/s/skills/research/SKILL.md`: frontmatter (`name: research`,
      description with trigger phrases "research", "deep research",
      "research report", "/s:research"); announce the plugin version from
      `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` in the first status
      sentence; require the resolved content-dir layout via
      `spec_status.py config-show`; run in its own worktree via
      `worktree.sh research-<slug>`; one batched typed clarification round
      only when the question is underspecified; the staged pipeline
      (decompose into bounded sub-questions → WebSearch per sub-question →
      select strongest sources → WebFetch and extract anchored findings →
      compose Summary, themed Findings, Gaps & caveats, numbered
      `## Sources` with `[n]` markers on every load-bearing claim,
      unanchored claims downgraded to Gaps & caveats); stop with a report of
      unavailability when WebSearch/WebFetch cannot be reached; end by
      pointing at `/s:epic` consumption of the installed report.
- [x] 4.2 [req: research-report-emission] In the same SKILL.md, mandate
      engine-mediated emission: author the report in a staging file, install
      with `spec_emit.py research <slug> --from <file>` (kebab-case slug
      derived from the question), never construct a `research/` path, and on
      findings fix the staged file and re-run until exit 0; read-back is
      `spec_status.py cat research <slug>`.
- [x] 4.3 [req: question-rejection-recovery] Add the question rejection
      recovery rule and the dialog/prose separation rule to
      `plugins/s/skills/research/SKILL.md`, phrased as in the other
      interactive skills' SKILL.md files.

## 5. Docs and version

- [x] 5.1 [req: research-report-format] Update `.shipd/README.md`: extend the
      `research/` layout comment and the epic Research bullet with the
      report grammar (title line, numbered `## Sources`, resolving `[n]`
      markers, code blocks skipped), the `/s:research` producer, and the
      `spec_emit.py research` / `cat research` engine verbs.
- [x] 5.2 [req: research-skill-pipeline] Add `/s:research` to the skill
      roster sentence in `AGENTS.md` (the "Use `/s:plan` to spec work…"
      paragraph).
- [x] 5.3 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version to
      `0.6.0`.

## 6. Verification

- [x] 6.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` from the repo root and confirm the full
      suite is green.
