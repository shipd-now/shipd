## 1. The video pre-step

- [x] 1.1 [req: plan-video-entry] In `plugins/s/skills/plan/SKILL.md`, add a
      "Video entry point" section placed before the Flow's investigation step:
      it fires when the invocation argument is a path whose extension is a
      recognized video container (`.mov`, `.mp4`, `.m4v`, `.webm`, `.mkv`) or a
      slug that `video_ingest.py path <slug>` resolves to an existing bundle,
      and otherwise falls through to the ordinary flow untouched.
- [x] 1.2 [req: plan-video-entry] In that same section, specify obtaining the
      brief by invoking the `/s:video-ingest` skill **by reference** —
      mirroring how `plugins/s/skills/build/SKILL.md:124` invokes the plan flow
      — passing the path or slug through unchanged, and explicitly forbidding
      restating that skill's ingest instructions here.
- [x] 1.3 [req: plan-video-entry] In that same section, state that the brief is
      an input to investigation rather than a replacement: the codebase-first
      rule still applies in full, affected capabilities and files are still
      established by reading the repository, and the installed brief's slug is
      named in user-visible text.
- [x] 1.4 [req: plan-video-entry] In the Flow's numbered steps, add a reference
      to the new section at the point it runs, so a reader following the Flow
      top-to-bottom reaches it before investigation.

## 2. The epic advisory

- [x] 2.1 [req: plan-video-epic-advisory] In
      `plugins/s/skills/plan/SKILL.md`, add the epic advisory to the video
      section: where the brief's intents are too broad for one change, report
      that assessment, name the intents behind it, recommend `/s:epic`, and
      stop without emitting. State that the skill never invokes `/s:epic`
      itself and applies no mechanical threshold.
- [x] 2.2 [req: plan-video-epic-advisory] In that `SKILL.md`'s "What still
      stops the flow" list, add the epic-sized brief as a condition that ends a
      turn, so it is not mistaken for the auto-proceed default.

## 3. The eval case

- [x] 3.1 [req: *] Create `evals/cases/plan-video-brief/fixture/` as a minimal
      repo matching the shape of `evals/cases/plan-csv-export/fixture/` (an
      `.shipd/` layout with `verified/`, `planned/`, `completed/`, plus a small
      `src/`), and add a pre-installed brief at the fixture's
      `.shipd/video/<slug>/brief.md` conforming to the grammar in `.shipd/README.md`'s
      "Video intent briefs" — a title, a `Video:` header on the line
      immediately after it, `## Speakers`, one cited `## Intents` entry, and a
      `## Sources` entry opening with a zero-padded `[HH:MM:SS]` timestamp.
- [x] 3.2 [req: *] Verify the fixture's brief is well-formed by installing a
      copy of it into a scratch root outside the repo with
      `spec_emit.py --root <scratch> video <slug> --from <fixture brief>` and
      confirming exit zero. Do not leave the scratch root behind.
- [x] 3.3 [req: *] Create `evals/cases/plan-video-brief/prompt.md` pointing
      `/s:plan` at that bundle slug, phrased so the expected outcome is a
      single lint-clean change — matching the grading the runner applies
      (`evals/run.py`).
- [x] 3.4 [req: *] Confirm the runner discovers the new case:
      `python3 evals/run.py --case plan-video-brief` lists and attempts it. This
      spends real model budget; run it once.

## 4. Ship

- [x] 4.1 [req: *] Run the runner's own unit tests, which need no live session:
      `uvx pytest evals/tests/ -q`. Confirm they pass.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm 920 tests pass — this change
      touches no engine code, so the suite must be unchanged and green.
- [x] 4.3 [req: *] Per `AGENTS.md`, this change edits a `SKILL.md` the existing
      eval cases exercise, so run them: `python3 evals/run.py --case
      plan-csv-export` and `--case plan-new-capability`. Confirm both still
      pass, demonstrating the video pre-step did not disturb the ordinary
      no-video path. Record the pass-rates in the PR description. This spends
      real model budget.
- [x] 4.4 [req: *] Confirm `git status --short` in both the worktree and the
      main checkout shows only this change's intended files and no scratch
      artifact from tasks 3.2 or 3.4.
- [x] 4.5 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.82` to `0.6.83`.
