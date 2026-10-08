## 1. Raise the figure

- [x] 1.1 [req: body-content] Confirm the starting point by rendering every
      command body against every registered harness's own declared features,
      and report the worst case. It should be 194 lines, for the `review` body
      on the `aider` harness.
- [x] 1.2 [req: body-content] In
      `plugins/s/skills/build/tests/test_harness_bodies.py`, change
      `test_every_body_stays_lean_at_the_full_vocabulary` to assert under 250
      instead of under 200, in both loops it runs — the full-vocabulary loop
      and the per-registered-harness loop. Do not change which cases it
      renders.
- [x] 1.3 [req: body-content] Extend the docstring with three things: that this
      fourth raise was asked for and chosen rather than reached by drift, after
      the third raise's own docstring flagged that a fourth should be a
      decomposition conversation; the structural reason the file grows, which is
      that it ships standalone, can read no reference file, and so repeats every
      rule the review skill gains in full; and the measured worst case at the
      time of the raise, 194 for `review` on `aider`, so a later reader can see
      the rate of movement rather than only the endpoint.
- [x] 1.4 [req: body-content] Do not restate 250 anywhere else. Grep the
      repository for the old figure and confirm no second owner appeared.

## 2. Version and verification

- [x] 2.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.271` to `0.6.272`.
- [x] 2.2 [req: *] Run the build suite with stderr captured — `python3 -m
      unittest discover -s plugins/s/skills/build/tests > /tmp/bs272.log 2>&1;
      tail -4 /tmp/bs272.log` — and report the verdict verbatim.
- [x] 2.3 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests` and confirm it stays at 293.
- [x] 2.4 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 2.5 [req: body-content] Confirm `git diff --name-only main` lists only the
      test file and `plugin.json`. No body content changes in this change.
