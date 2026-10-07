## 1. Confirm the drift before correcting it

- [x] 1.1 [req: review-skill-references] Record the three facts the
      correction rests on: `wc -l plugins/s/skills/review/SKILL.md` (325),
      the `assertLess` constant in
      `plugins/s/skills/review/tests/test_skill_references.py`'s
      `test_under_line_ceiling` (330), and the four spec sites stating a
      ceiling. Confirm `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` is green.

## 2. Give the ceiling one owner

- [x] 2.1 [req: review-skill-references] The staged delta extends
      `review-skill-references`' sentence to claim ownership of the 330-line
      figure and forbid other requirements restating it. Confirm the merged
      master reads that way after the change applies.
- [x] 2.2 [req: review-risk-lenses] Confirm the merged master has
      `review-risk-lenses` carrying no line figure, with its "The skill body
      still fits the ceiling" scenario referring to the owner instead.
- [x] 2.3 [req: review-lint-step] Confirm the same for `review-lint-step`
      and its copy of that scenario.
- [x] 2.4 [req: review-incremental] Confirm `review-incremental` keeps its
      adding-no-line guarantee and its `posting.md` row assertion, having
      dropped only the 300-line figure from both the requirement and its
      "The trigger costs no line" scenario.

## 3. Verification

- [x] 3.1 [req: *] Confirm no file under `plugins/s/` changed — `git status`
      should show only `.shipd/` paths — so no version bump is needed and
      the plugin ships identical bytes.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-skill-ceiling-owner`), confirming the suite and
      both lints pass.
- [x] 3.3 [req: *] Grep the merged master for `under 300 lines` and confirm
      no occurrence remains in the `semantic-review` capability.
