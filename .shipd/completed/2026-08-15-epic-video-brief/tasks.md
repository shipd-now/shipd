## 1. Lint: the `## Video` epic section

- [x] 1.1 [req: epic-video-section, epic-video-link-validation] Port the
      Video-section test additions into
      `plugins/s/skills/build/tests/test_spec_lint.py`: read
      `git -C /Users/mikkelbergmann/projects/automikk diff 48648a8..dbe12a4 -- plugins/am/skills/build/tests/test_spec_lint.py`
      and apply its added test methods under the token map (`.am/` →
      `.shipd/`, `/am:` → `/s:`, anchored `am` forms → `s`/`shipd`), leaving
      the file's existing oracle-qa-ledger tests untouched. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -q` and
      observe the new cases fail.
- [x] 1.2 [req: epic-video-section, epic-video-link-validation] In
      `plugins/s/skills/build/scripts/spec_lint.py`, apply the upstream
      refactor from
      `git -C /Users/mikkelbergmann/projects/automikk diff 48648a8..dbe12a4 -- plugins/am/skills/build/scripts/spec_lint.py`:
      rename `RESEARCH_LINK_RE` to `EPIC_LINK_RE` with the generalized
      comment, replace `_check_epic_research` with
      `_check_epic_link_section(root, path, text, errors, header, folder, noun)`,
      and update the epic-lint call site to invoke it for
      `("## Research", "research", "research file")` and
      `("## Video", "video", "video intent brief")`. Leave
      oracle-qa-ledger's `check_plan_qa_section` and its regex untouched. Run
      the suite from task 1.1; all tests pass.

## 2. Skills and grammar

- [x] 2.1 [req: video-fed-epic-authoring, epic-no-recording-ingest] Overwrite
      `plugins/s/skills/epic/SKILL.md` with automikk's version at the pinned
      ref:
      `python3 tools/port.py apply --source /Users/mikkelbergmann/projects/automikk --ref dbe12a4 --include plugins/am/skills/epic/SKILL.md --dest .`
      run from the worktree root. Review `git diff` afterward: the change adds
      the `## Video` consumption flow (brief reading via
      `spec_status.py cat video <slug>`) and touches nothing else. Where the
      apply run reports a residual on a line the port did not touch (a bare
      pre-existing old-namespace form such as `` `am:epic` `` with no leading
      slash, inherited from the engine-port snapshot), correct that line to
      the matching `s:`/`shipd` form in the same edit so the verb exits 0 —
      pre-existing residuals are in scope as one-line brand fixes; new
      residuals introduced by the ported text itself are not expected and stay
      question-worthy.
- [x] 2.2 [req: video-fed-epic-authoring] Overwrite
      `plugins/s/skills/video-ingest/SKILL.md` the same way:
      `python3 tools/port.py apply --source /Users/mikkelbergmann/projects/automikk --ref dbe12a4 --include plugins/am/skills/video-ingest/SKILL.md --dest .`
      from the worktree root. Review `git diff`: only the #210
      cross-reference edits appear — no cursor-grounding content (that is
      #211, excluded by the ref pin). The same pre-existing-residual ruling as
      task 2.1 applies: fix any bare old-namespace leftover the report names
      on untouched lines, so the verb exits 0.
- [x] 2.3 [req: epic-video-section] Add the `## Video` section grammar to
      `.shipd/README.md`: apply the content-directory README hunk from
      `git -C /Users/mikkelbergmann/projects/automikk diff 48648a8..dbe12a4 -- '*README.md'`
      (that range touches exactly one README — automikk's content-directory one)
      under the token map, placed alongside the existing `## Research` grammar
      and leaving oracle-qa-ledger's `## Questions and answers` grammar
      untouched.

## 3. Ship gate

- [x] 3.1 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` by one patch level.
- [x] 3.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -q` (full
      engine suite including the ported cases) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py` (master library
      clean); both exit 0.
