# Tasks

- [x] 1.1 [P1] [req: review-risk-lenses] Correct the header of
      `plugins/s/skills/review/references/risk-lenses.md` to state **six
      triggers and five lenses**, matching `review-risk-lenses` and the file's
      own six `##` sections. Change nothing else in the file — the lens
      content, the worked examples and the severity floors stay exactly as
      they are, because this change ships alone so a round set can attribute
      what it finds to this one sentence.
- [x] 1.2 [P1] [req: review-risk-lenses] Add `RiskLensCountsAgreeTest` to
      `plugins/s/skills/review/tests/test_skill_references.py` pinning three
      things: the header states the right counts and not the transposed pair;
      the file carries exactly six `##` sections; and every trigger phrase
      `SKILL.md` names has a section of its own. The third catches a seventh
      trigger being added to the skill and not here. Prove the guard
      non-vacuous by restoring `main`'s header with the file otherwise intact
      and watching it fail, recording the byte counts so a truncating probe is
      not mistaken for a result, and run the probe with
      `PYTHONDONTWRITEBYTECODE=1 python3 -B` with `__pycache__` cleared.
- [x] 1.3 [P1] [req: review-risk-lenses] Bump
      `plugins/s/.claude-plugin/plugin.json` to the next free number **above
      whatever the main branch carries at the time**. Read it; do not assume.
      Main moved four times during this series' final changes, and a version at
      or below main's moves the plugin version backwards.
- [x] 2.1 [P2] [req: review-risk-lenses] Verify. Run the review suite and the
      build suite, reading each verdict with
      `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over a captured log
      rather than tailing it, and never concurrently with a mutating probe.
      Confirm the whole-library lint passes and `version_guard.py` exits 0
      against the main branch.
- [x] 2.2 [P2] [req: review-risk-lenses] Confirm the change touches exactly
      three files under `plugins/` and that the only prompt-path file among
      them is `plugins/s/skills/review/references/risk-lenses.md` — not
      `plugins/s/skills/review/SKILL.md`, not the harness
      body, not the copilot template. This change deliberately moves one
      measured surface and nothing else, so a stray edit anywhere else makes
      the next round set unattributable.
