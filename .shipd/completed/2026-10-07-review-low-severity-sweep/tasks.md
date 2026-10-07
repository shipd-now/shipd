## 1. Free SKILL.md's line budget before adding anything

- [x] 1.1 [req: review-skill] Confirm the starting point: run `wc -l
      plugins/s/skills/review/SKILL.md` and `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and note both pass (329 lines,
      green suite) before any edit — this is the baseline the later tasks
      trim against.
- [x] 1.2 [req: review-skill] Create
      `plugins/s/skills/review/references/new-code-checks.md`: move step 5's
      five sub-bullets ("Wrong quantity measured," "Escape hatch lapsing the
      guarantee," "Termination on hostile input," "Boundary agreement," "Doc
      comment versus code") and their explanatory sentences into it verbatim,
      as the reference's full guidance, following the shape of
      `plugins/s/skills/review/references/risk-lenses.md` (a short intro sentence, then the checks
      with their explanations, then worked examples if helpful).
- [x] 1.3 [req: review-skill] In `plugins/s/skills/review/SKILL.md`, replace
      step 5's five inline bullets with a short paragraph — keep "For every
      function, class, guard, or helper the diff introduces, judge it against
      its own stated purpose — do not wave it through because it is new
      rather than modified" and add a pointer: "Read
      `${CLAUDE_PLUGIN_ROOT}/skills/review/references/new-code-checks.md` for
      the five checks and worked examples." Add a new row to the `##
      References` table: `plugins/s/skills/review/references/new-code-checks.md` loaded when "a
      function, class, guard, or helper is new in the diff."
- [x] 1.4 [req: review-skill] Run `wc -l plugins/s/skills/review/SKILL.md`
      and the suite from 1.1 again; confirm the extraction net-freed lines
      (fewer than the 329-line baseline) and nothing broke.

## 2. Redefine the low-severity rubric

- [x] 2.1 [req: review-skill] In `plugins/s/skills/review/SKILL.md`'s
      `### 6. Report by cohort` severity rubric, replace the `- **low** —
      style, naming, minor redundancy, defensive nits.` bullet: redefine low
      as a real but minor defect, naming the categories — a swallowed or
      silently-dropped error; a resource or file leak on a rare or cleanup
      path; dead or duplicated code; a field or variable declared but never
      read; an unstable or incorrect identity (e.g. a list/row key derived
      from array index instead of a stable id); a blocking/synchronous call
      where the surrounding context is async or event-driven — and state
      explicitly that pure style, naming preference, and formatting are never
      findings at any severity.
- [x] 2.2 [req: review-skill] Make the identical rubric edit to
      `plugins/s/harness/bodies/review.md`'s own copy of the severity rubric
      (its numbered report step's `- **low** — ...` line), word for word
      consistent with 2.1 so the two surfaces do not drift.
- [x] 2.3 [req: review-skill] Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests -v`
      and confirm it stays green (no test hard-codes the old wording;
      `test_severity_rubric_stayed_inline` checks only generic substrings).

## 3. Add the breadth-sweep step

- [x] 3.1 [req: review-skill] In `plugins/s/skills/review/SKILL.md`, add a
      new workflow step `### 5c. Breadth sweep for minor defects`, positioned
      after `### 5b. Risk lenses` and before `### 6. Report by cohort`:
      after judging new code and applying the risk lenses, revisit each
      changed file once more, end to end, for a remaining low-severity
      defect of the categories named in the rubric (2.1) — a pass the
      structural diff and signature-chasing steps above do not exist to
      catch, since a minor defect can sit beside a hunk without being part
      of it structurally.
- [x] 3.2 [req: review-skill] In `plugins/s/harness/bodies/review.md`, insert
      the equivalent new numbered step after the existing risk-lenses step
      (currently step 7) and before the existing spec-verification step
      (currently step 8), stating the same breadth-sweep instruction as 3.1
      in this file's own fully-inline style (it ships into other repos with
      no `${CLAUDE_PLUGIN_ROOT}` and can never gain a references table).
      Renumber every subsequent step in this file by one.
- [x] 3.3 [req: review-skill] Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests -v`
      and `python3 -m unittest discover -s plugins/s/skills/build/tests -v`
      (the latter covers the copilot-template tests, which reference neither
      file's step numbers) and confirm both stay green. If
      `test_under_line_ceiling` fails here, trim the new step's wording (not
      the rubric from task 2) until it passes — do not move content back out
      of the reference from task 1 to make room.

## 4. Spec and version

- [x] 4.1 [req: review-skill] Confirm
      `.shipd/verified/semantic-review/spec.md`'s `review-skill` requirement,
      once this change merges, states the redefined low rubric, the
      breadth-sweep pass, and "four judgement passes" (not three) — this
      lands automatically through the staged delta at
      this change's installed delta spec when the change is emitted; this task
      is to re-read the merged result and confirm it matches SKILL.md and
      harness/bodies/review.md word for word on the rubric categories.
- [x] 4.2 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.249` to `0.6.250`
      (per `AGENTS.md`: every change touching `plugins/s/` bumps it in the
      same PR).

## 5. Verification

- [x] 5.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-low-severity-sweep`), and confirm every suite and
      both lints pass, with `test_under_line_ceiling` green.
