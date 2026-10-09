# Tasks

- [x] 1.1 [P1] [req: skill-template] Apply the MODIFIED `skill-template`
      delta to the master library by running the merge, so
      `.shipd/verified/copilot-review-skill/spec.md` carries the deferral
      instead of its own copy of the `low` definition, the impact floor and
      the no-omission rule. Confirm afterwards that the merged requirement
      names `review-skill` as the owner and that the words
      "impact is contained" and "grounds for omitting" no longer appear in it.
- [x] 1.2 [P1] [req: skill-template] Confirm no file under `plugins/s/`
      changed. A diff of this branch against the main branch must touch only
      the content directory — the whole point of this change is that it needs
      no plugin version bump while a measurement runs against v0.6.276. If any
      plugin file appears, stop and report rather than bumping the version.
- [x] 2.1 [P2] [req: skill-template] Verify the new scenarios against the real
      files rather than the suites. For "The template's rubric matches the
      skill's", compare the `low` bullet and the floor paragraph in
      `plugins/s/integrations/copilot/SKILL.md` against those in
      `plugins/s/skills/review/SKILL.md` on whitespace-normalised text and
      confirm they state the same definition, the same floor and the same three
      instances. For "This requirement restates no rubric wording", read the
      merged requirement and confirm it reproduces neither the `low` definition
      nor the floor.
- [x] 2.2 [P2] [req: skill-template] Run the full library lint
      (`python3 plugins/s/skills/build/scripts/spec_lint.py`) and the review
      suite (`python3 -m unittest discover -s
      plugins/s/skills/review/tests`), reading the suite verdict with
      `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over a captured log
      rather than tailing it. The review suite must still pass unchanged — this
      change alters no file it reads, so a failure here means the delta touched
      something it should not have.
