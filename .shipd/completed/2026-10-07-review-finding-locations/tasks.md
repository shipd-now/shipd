## 1. Schema: `location` becomes `locations`

- [x] 1.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add a failing
      test asserting that `plugins/s/skills/review/references/json-output.md`
      and `plugins/s/harness/references/review.md` both document a finding's
      location as a non-empty `locations` array, not a singular `location`
      string. Run it and observe it fail.
- [x] 1.2 [req: review-skill] In
      `plugins/s/skills/review/references/json-output.md`, replace
      `"location": "path/to/file.ext:LINE"` with
      `"locations": ["path/to/file.ext:LINE", "other/file.ext:LINE2"]` in the
      shape block; state in the rules paragraph that the array is non-empty
      and `locations[0]` is the primary/fix site; and update the `suggestion`
      rules to say the suggestion anchors `locations[0]` to a RIGHT-side
      diff line (not "the finding's `location`").
- [x] 1.3 [req: review-skill] Mirror the identical `locations` shape and rules
      sentence in `plugins/s/harness/references/review.md`. Confirm the 1.1
      test passes.

## 2. Skill instruction: fix-site anchoring and one finding per recurrence

- [x] 2.1 [req: review-skill] In `plugins/s/skills/review/SKILL.md` step 6
      ("Report by cohort"), change "For each finding: the **location**,
      **what** is wrong..." to instruct: a finding's location names the line
      its own fix would change, never a caller or symptom site; and a defect
      recurring at more than one call site is one finding whose `locations`
      names every site, not one finding per site.

## 3. `review_gate.py`: multi-location anchoring, hashing, and rendering

- [x] 3.1 [req: gate-poster] In
      `plugins/s/skills/review/tests/test_review_gate.py`, rename every
      fixture's `"location": "<path>:<line>"` to
      `"locations": ["<path>:<line>"]`, including the `_finding()` test
      helper's `location=` parameter (renamed `locations=`, defaulting to a
      one-element list) and every call site that passes it — no behavior
      change for the single-location case. Then add new failing tests: (a) a
      finding whose `locations` names two sites that both anchor, in two
      different files, posts two distinct inline comments, each carrying the
      finding's what/why/fix and each with its own `<!-- shipd-finding ...
      -->` hash; (b) a finding with one anchorable and one off-diff location
      posts one inline comment, for the anchorable site, and is not folded
      into "Additional findings"; (c) a finding whose every location is
      off-diff posts no inline comment and is folded whole; (d) a finding
      with more than one location and a committable suggestion carries that
      suggestion only on the comment anchored at `locations[0]`, with every
      other comment rendering as prose; (e) the summary table row and the
      "Additional findings" bullet for a multi-location finding show
      `locations[0]` followed by `(+N more)`. Run the suite and observe (a)
      through (e) fail against the current single-location code.
- [x] 3.2 [req: gate-poster] In
      `plugins/s/skills/review/scripts/review_gate.py`: add
      `_parse_locations(f)`, mapping every string in
      `f.get("locations") or []` through the existing `_parse_location` and
      dropping entries that fail to parse; rewrite `_split_findings` so a
      finding is anchored when any of its locations resolves to a
      RIGHT-side commentable line, yielding one `(finding, path, line,
      index)` tuple per commentable location, and lands in `unanchored` only
      when none resolve; add an optional `index=0` parameter to
      `_finding_hash`, folded into the digest only when the finding declares
      more than one location (so a single-location finding's hash is
      byte-identical to today's), and thread it through every call site that
      builds an inline comment's identity marker; have `_inline_body` append
      an "Also recurs at: <path:line>, <path:line>" line when the finding
      carries locations beyond the one the current comment anchors; restrict
      the suggestion path so `_suggestion`/`_review_comment` only ever attach
      a `suggestion` block to the comment anchored at `locations[0]`; update
      `_detail_cell` and the "Additional findings" renderer to show
      `locations[0]` plus `(+N more)` when `len(locations) > 1`.
- [x] 3.3 [req: gate-poster] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm every test, including the
      3.1 additions, passes.

## 4. `posting.md` wording

- [x] 4.1 [req: gate-poster] In
      `plugins/s/skills/review/references/posting.md` step 5, change "posts
      anchored inline comments for in-diff findings (folding the rest into
      the summary)" to describe one inline comment per anchorable location
      across a finding's `locations` array, with a finding folded into the
      summary only when none of its locations anchor.

## 5. Version bump

- [x] 5.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` (per `AGENTS.md`: every change
      touching `plugins/s/` bumps it in the same PR so the cached plugin
      snapshot is not left stale).

## 6. Verification

- [x] 6.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-finding-locations`), and confirm every suite and
      both lints pass.
