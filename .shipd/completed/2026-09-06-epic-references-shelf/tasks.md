## 1. References shelf lint

- [x] 1.1 [req: epic-references-link-lint] Add `EpicReferencesLintTest` to
      `plugins/s/skills/build/tests/test_spec_lint.py`, mirroring
      `EpicResearchLintTest` (line 1027): a resolving docs entry; one section
      mixing resolving research + video + docs entries; a dead link (error
      naming the link); an existing file outside all three folders (error);
      an empty `## References` section (error); an absent section (no
      finding); and a dead `## Research` link reported unchanged alongside a
      resolving `## References` section. Run the class and observe it fail —
      the section is unvalidated today.
- [x] 1.2 [req: epic-references-link-lint, epic-references-section]
      In `plugins/s/skills/build/scripts/spec_lint.py`, generalize
      `_check_epic_link_section` (line 583) so its folder parameter is a
      tuple of folders (a link resolves when it lands under any of them);
      keep the two legacy calls' error text byte-identical, rendering the
      multi-folder message as "…under the content directory's research/,
      video/, or docs/ folders". Add the `## References` call in `lint_epic`
      after the `## Video` call (line 714) with folders
      `("research", "video", "docs")` and noun "reference file". Update the
      section comment at line 103 and the `lint_epic` docstring. Confirm the
      1.1 tests pass.
- [x] 1.3 [req: epic-references-section] In `.shipd/README.md`'s epic
      contract rules (after the **Video (optional)** bullet, ~line 796), add
      a **References (optional)** bullet: superset shelf over `research/`,
      `video/`, and `docs/`, same resolve rules, empty/dead/outside-folder
      errors, new authoring prefers it while `## Research`/`## Video` stay
      valid forever. Add a `## References` line entry to the epic example
      block (~line 718).

## 2. /s:epic wiring

- [x] 2.1 [req: epic-supplied-document-install, research-fed-authoring, video-fed-epic-authoring]
      In `plugins/s/skills/epic/SKILL.md`: switch
      the supplied-document install (lines 63-80) from `spec_emit.py
      research` to `spec_emit.py docs <slug> --from <file>` (same slug and
      staged-title rules; note `--root` precedes the subcommand when used),
      linking installs from `## References`; record consumed research
      reports (line 62) and video briefs (line 89) under `## References`
      for newly authored epics, extending a pre-existing legacy section in
      place when one exists; add `## References (optional)` to the contract
      template (lines 166-172) and a References rules bullet beside the
      Research/Video bullets (lines 203-217).
- [x] 2.2 [req: epic-references-section] Mirror the contract in the harness:
      `plugins/s/harness/references/epic.md` (template block and the
      "Research and Video (both optional)" rule gain References), and
      `plugins/s/harness/bodies/epic.md` — the supplied-input sentence
      (lines 24-26) installs non-installed documents through the docs kind
      and links `## References`, and the reference-pointer line (line 59)
      names the References section too.

## 3. /s:plan wiring

- [x] 3.1 [req: plan-supplied-document-install] In
      `plugins/s/skills/plan/SKILL.md`, add a "Supplied documents" rule to
      step 1 (Investigate): when the user supplies a context document not
      already under `research/`, `video/`, or `docs/`, install it with
      `spec_emit.py docs <slug> --from <file>` (slug from the level-1 title
      or filename; stage a titled copy for an untitled file; never a raw
      copy into the tree), read it back via `spec_status.py cat docs
      <slug>`; when the change carries `Epic:` resolving in the repo, append
      a link entry to that epic's `## References` section (creating it when
      absent); otherwise cite the document in `plan.md` prose and edit no
      epic.
- [x] 3.2 [req: plan-supplied-document-install] Add the matching one-
      sentence rule to `plugins/s/harness/bodies/plan.md` so the harness
      body names the same install-and-link path.

## 4. Ship gate

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.6.180 → 0.6.181. Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (all pass, no textual installed) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py --epic
      epic-knowledge --root .` (exit 0).
