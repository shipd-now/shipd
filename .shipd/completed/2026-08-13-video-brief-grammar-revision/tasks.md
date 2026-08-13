## 1. Drop the speaker surface from the linter

- [x] 1.1 [req: video-brief-validation, video-brief-format] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add tests that
      `lint_video` produces no finding for a brief carrying no `## Speakers`
      section, and none for a source entry that is a bracketed timestamp
      followed only by what was said. Run them and observe the Speakers one
      fail — the section is still required.
- [x] 1.2 [req: video-brief-validation, video-brief-format] In
      `plugins/s/skills/build/scripts/spec_lint.py`, delete the `## Speakers`
      section check from `lint_video` (the block around lines 916-922 that
      reports a missing section and an entry-less section) and delete the
      now-unused `VIDEO_SPEAKER_ENTRY_RE` (line 857). Leave `VIDEO_TIMESTAMP_RE`
      unchanged — it already accepts a speaker-free entry. Confirm the tests
      from 1.1 pass.
- [x] 1.3 [req: video-brief-validation] In the same file, update `lint_video`'s
      docstring and the `VIDEO_TIMESTAMP_RE` comment (around lines 860 and 891)
      to stop describing a required `## Speakers` section and a speaker name
      after the timestamp.

## 2. Validate the Project header

- [x] 2.1 [req: video-brief-validation, video-brief-format] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add a test that
      `lint_video` reports a finding naming the brief file when the header
      carries a `Project:` value naming a slug the workspace registry does not
      declare, and a test that a brief with no `Project:` line produces no
      finding and attempts no registry validation. Run and observe the first
      fail.
- [x] 2.2 [req: video-brief-validation, video-brief-format] In
      `plugins/s/skills/build/scripts/spec_lint.py`, extend `lint_video` to
      look for a `Project:` key among the pairs returned by
      `_video_header_metadata` and, only when one is present, call the existing
      `_check_brief_project(ws_root, project_value, path, errors)` helper
      defined at line 654, resolving `ws_root` with
      `sc.find_workspace_root(root)`. Confirm the tests from 2.1 pass.

## 3. Revise the ingest skill

- [x] 3.1 [req: video-skill-arbitration] In
      `plugins/s/skills/video-ingest/SKILL.md`, delete the entire
      `## Speakers and arbitration` section, including the naming round, the
      `samples`/`afplay`/`merge-speakers`/`roster` instructions, and the decider
      rules.
- [x] 3.2 [req: video-skill-conflict-recency] In the same file, add a short
      section stating that conflicting intents about the same target resolve by
      recency — the latest statement is the outcome, superseded statements are
      retained with their timestamps, and a conflict that recency cannot order
      goes to `## Open questions` with both positions and neither recorded as
      the outcome.
- [x] 3.3 [req: video-skill-brief-emission, video-brief-format] In the same
      file's brief grammar block and the prose describing it, remove the
      `## Speakers` section and the speaker name from the `## Sources` entry
      format, so a source entry is `[HH:MM:SS] <what they said>`, and remove the
      `Decider:` header line from the documented metadata.
- [x] 3.4 [req: video-skill-brief-emission] In the same file, document the
      optional `Project:` header line: authored with the project's declared
      workspace-registry slug when the project is known — named at invocation,
      or because the invoking repository is a declared project — and omitted
      entirely rather than guessed when it is not.
- [x] 3.5 [req: video-skill-arbitration, video-skill-conflict-recency] In the
      same file, rewrite staged-pipeline step 5 (lines 74-75, "**Ground,
      arbitrate, and compose.** … resolve speaker names and any conflicting
      statements") so it grounds candidates on frames, resolves conflicting
      statements by recency, and composes — naming no speakers. Leave the other
      numbered steps as they are.

## 4. Guard the plan entry point

- [x] 4.1 [req: plan-video-entry] In
      `plugins/s/skills/plan/SKILL.md`, extend the "Video entry point" section
      with the project check: compare the brief's `Project:` against the
      planning repository's declared project slug, and on a mismatch report both
      names and end the turn without emitting.
- [x] 4.2 [req: plan-video-entry] In the same section, document that the check
      runs only when both sides are known — no `Project:` line, or a repository
      resolving to no declared project, means no comparison — so a
      registry-less workspace is never refused.
- [x] 4.3 [req: plan-video-entry] In the same section, document the
      `--cross-project` override: when the invocation argument carries it, the
      skill proceeds and states in user-visible text that the project check was
      overridden.
- [x] 4.4 [req: plan-video-entry] In the same file's "What still stops the
      flow" list, add the project mismatch as a stop condition, matching how the
      epic-sized-brief stop is listed.

## 5. Fixture, verification, and release

- [x] 5.1 [req: video-brief-format] In
      `evals/cases/plan-video-brief/fixture/.shipd/video/report-json-export/brief.md`,
      delete the `## Speakers` section and remove the speaker name from every
      `## Sources` entry, leaving each entry as its bracketed timestamp followed
      by what was said. Do not delete the case.
- [x] 5.2 [req: *] Run the engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm every test passes.
- [x] 5.3 [req: *] Confirm the shipped brief grammar accepts a speaker-free
      brief end to end. Copy the updated fixture brief to a temp path **outside**
      the content directory, then install it under a throwaway slug:
      `python3 plugins/s/skills/build/scripts/spec_emit.py --root
      evals/cases/plan-video-brief/fixture video probe-speakerfree --from
      <temp>/brief.md`, confirm it exits zero, and delete the probe directory.
      Never point `--from` at a file inside the destination slug's own
      directory with `--replace`: the engine moves that directory aside before
      copying, so the command would delete its own source.
- [x] 5.4 [req: *] Run the eval harness's video-brief case
      (`python3 evals/run.py --case plan-video-brief`) from the repo root, since
      this change edits two `SKILL.md` files, and report the pass rate.
- [x] 5.5 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` to
      the next patch version, as required for any change touching
      `plugins/s/`.
