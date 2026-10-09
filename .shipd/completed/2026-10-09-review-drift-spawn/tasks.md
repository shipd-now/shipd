## 1. The drift spawn gets the diff

- [x] 1.1 [req: review-skill] Confirm the starting point: the review suite is
      green at 303 tests, and
      `plugins/s/skills/review/references/verification.md`'s drift-exception
      paragraph specifies a spawn carrying the description and no diff.
- [x] 1.2 [req: review-skill] Change that paragraph so the drift spawn carries
      the description **and** the diff. Keep the premise sentence already there
      — that a drift claim is a relationship between the description and the
      diff — and make the conclusion follow from it instead of contradicting
      it.
- [x] 1.3 [req: review-skill] State the asymmetry explicitly in the same place:
      the defect spawn carries the diff and not the description; the drift
      spawn carries both. Say that this is deliberately not a mirror image,
      because reading it as one is what produced the error being fixed. That
      sentence is the guard against someone later "restoring symmetry".
- [x] 1.4 [req: review-skill] Leave the defect spawn's blindness untouched and
      confirm by reading it back that the description cannot reach it. That is
      the one thing this change could break by accident.

## 2. Category on killed entries

- [x] 2.1 [req: review-skill] In
      `plugins/s/skills/review/references/json-output.md`, add `category` to
      each `killed` entry, carrying the same taxonomy value the candidate held.
      State why: without it a consumer cannot tell a drift kill from a defect
      kill except by parsing prose.
- [x] 2.2 [req: review-skill] Apply the same addition to
      `plugins/s/harness/references/review.md`'s machine-payload section, which
      carries its own copy of the schema.

## 3. Per-spawn candidate counts

- [x] 3.1 [req: review-skill] In the same two payload surfaces, have `verifier`
      report a count per spawn alongside the existing `candidates` total.
      Positions are zero-based within their own spawn, so a single total cannot
      say which spawn a position belongs to.
- [x] 3.2 [req: review-skill] Keep `candidates` with its current name and
      meaning as the total. Do not repurpose it — a consumer reading that field
      today would otherwise be handed a different number under an unchanged
      name, with nothing to signal the change.

## 4. Mirror onto the harness body

- [x] 4.1 [req: review-skill] Apply all three changes inline in
      `plugins/s/harness/bodies/review.md`'s verify step: the drift spawn
      carrying both, the stated asymmetry, `category` on killed entries, and
      the per-spawn counts. That file reads no reference, so anything omitted
      is gone for every repository that installs it.
- [x] 4.2 [req: review-skill] Report the worst rendered harness body across
      every registered harness against 250, measured at the end of your work.

## 5. Tests

- [x] 5.1 [req: review-skill] Add tests pinning: the drift spawn carries both
      the description and the diff; the defect spawn carries no description;
      the asymmetry is stated rather than implied; `killed` entries carry
      `category` on both payload surfaces; and `verifier` reports per-spawn
      counts.
- [x] 5.2 [req: review-skill] Check whether any existing test asserts the drift
      spawn carries no diff. If one does, re-aim it rather than deleting it —
      its premise is now wrong by design, and deleting it would remove the only
      guard on what the drift spawn carries.
- [x] 5.3 [req: review-skill] Prove every absence assertion fails against the
      pre-change text before trusting it. Note that this repository's prose is
      hard-wrapped at 88 columns, so a plain substring spanning a line break
      silently passes — use whitespace-tolerant patterns.

## 6. Version and verification

- [x] 6.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.273` to `0.6.274`.
- [x] 6.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      303-test baseline.
- [x] 6.3 [req: *] Run the build suite capturing stderr, and read the verdict
      with `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests" /tmp/bs274.log`. Do
      not use `tail` — this suite prints subprocess output after its own
      summary.
- [x] 6.4 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 6.5 [req: review-skill] Read the finished drift paragraph as a stranger
      and answer one question: could someone reading it conclude the two spawns
      are mirror images and "restore symmetry" by removing the diff again?
      Quote what you read. That reading is what caused the defect.
