## 1. Failing tests

- [ ] 1.1 [req: gate-poster] In
      `plugins/s/skills/review/tests/test_review_gate.py`
      `MultiLocationFindingTest`, rewrite
      `test_two_anchorable_locations_post_two_inline_comments` as
      `test_two_anchorable_locations_post_one_inline_comment`: one comment at
      `a.py:5` whose body contains `Also recurs at: b.py:10` and whose
      `_extract_finding_hash` equals `review_gate._finding_hash("a.py",
      "boom")`. Add a test of the 2026-11-21 case in one file: a medium
      finding at `a.py:2` and `a.py:4` (both commentable under `PATCH_A`) and
      an assertion of exactly one comment at line 2 carrying
      `Also recurs at: a.py:4`.
- [ ] 1.2 [req: gate-poster] In the same class, rewrite
      `test_suggestion_only_on_locations_zero_comment` to assert one comment
      carrying `SUGGESTION_FENCE`. Add
      `test_off_diff_first_location_anchors_next_site`: a confident finding at
      `["z.py:99", "a.py:5"]` gives one comment at `a.py:5` with no
      `SUGGESTION_FENCE`, carrying `Also recurs at: z.py:99`, with hash
      `review_gate._finding_hash("a.py", "boom", 1)`.
- [ ] 1.3 [req: gate-poster] In the same class, rewrite
      `test_all_off_diff_multi_location_shows_locations_zero_and_more` as
      `test_folded_finding_names_every_location`. The summary body carries
      `- **z.py:99** [` and `  - Also recurs at: y.py:88, x.py:77`, and the
      table row still carries `z.py:99 (+2 more)`. In
      `test_summary_shows_plus_n_more_for_multi_location`, keep the `(+2 more)`
      assertion. Add an assertion that a folded `already_there` multi-location
      finding (category `bug`, every location off-diff) carries the same
      `Also recurs at:` sub-line.
- [ ] 1.4 [req: gate-poster] In `RoomFindingTest`, change the expected data
      dict of the existing per-severity test to include
      `"locations": ["a.py:5"]`. Rewrite
      `test_second_location_carries_its_own_site` to also assert
      `data["locations"] == ["a.py:5", "b.py:9"]`. In `RoomPostTest`, add a
      test running `review_gate.post(..., room_agent="author")` with a finding
      at two anchorable locations and asserting exactly one inline comment
      contains `<!-- shipd-room `.
- [ ] 1.5 [req: review-incremental] In `PriorTest`, add tests that build two
      threads with `_thread(..., body=review_gate._inline_body(f,
      location_index=i), path=...)` for `f` at
      `{"id": "f1", "locations": ["a.py:5", "b.py:9"], "what": "boom",
      "severity": "high", "why": "w", "fix": "x"}`, `i` in 0 and 1. Assert
      that `review_gate.prior("7", gh, findings=[f])` gives both entries
      `"finding": "f1"`. Assert that, with only the index-1 thread carrying
      `reply_bodies=["Not applicable"]`, that entry is `replied` with
      `finding` `f1`. Assert that `prior("7", gh)` without `findings` returns
      entries with no `finding` key. Assert that
      `_run_main(["prior", "7", "--from", <tmp json path>], gh)` prints
      entries carrying `finding`. Assert that `finding_identities(f)` equals
      `[_finding_hash("a.py", "boom"), _finding_hash("b.py", "boom", 1)]`.
- [ ] 1.6 [req: review-incremental] In `ResolveTest`, add a test with the
      same two old per-location threads, no reply, and a commit dated after
      both. `review_gate.resolve("7", gh)` resolves both thread ids and
      reports `unresolved` 0. In `AutoreplyTest`, add a test where
      `autoreply("7", gh, "none")` replies to both old threads.
- [ ] 1.7 [req: *] From `plugins/s/skills/review`, run
      `python3 -B -m unittest discover -s tests 2>&1 | tail -3` and observe
      failures from the new tests (1.6 may already pass).

## 2. Poster changes in review_gate.py

- [ ] 2.1 [req: gate-poster] In
      `plugins/s/skills/review/scripts/review_gate.py` `_split_findings`,
      append only the first anchorable `(f, path, line, idx)` per finding,
      then `break`. Update its docstring to "one per finding, at its first
      anchorable location".
- [ ] 2.2 [req: gate-poster] In `_inline_body`, update the docstring to say
      the one comment names every other location and carries its anchored
      site's per-location identity. Change no logic.
- [ ] 2.3 [req: gate-poster] In `_room_finding_line`, add
      `"locations": list(f.get("locations") or [])` to the data dict.
- [ ] 2.4 [req: gate-poster] In `render_summary`'s inner `bullets`, render
      the bold location as `locations[0]` (else `(no location)`) with no
      `(+N more)`. When `len(locations) > 1`, append
      `"  - Also recurs at: " + ", ".join(locations[1:])` directly after the
      bullet line and before Why and Fix. Leave `_detail_cell` unchanged.
- [ ] 2.5 [req: gate-poster] In `_review_comment`'s docstring, replace
      "A suggestion is only ever attached to the comment anchored at
      locations[0]; all other comments render as prose only" with "A
      suggestion attaches only when the finding's one comment anchors at
      locations[0]; otherwise the comment is prose only".

## 3. Prior matching in review_gate.py

- [ ] 3.1 [req: review-incremental] Add `finding_identities(f)` after
      `_finding_hash`. It returns the list of
      `_finding_hash(path, f.get("what"), i if len(locations) > 1 else 0)` for
      each `i, loc in enumerate(f.get("locations") or [])` whose
      `_parse_location(loc)` path is not `None`.
- [ ] 3.2 [req: review-incremental] Change `prior(pr, gh)` to
      `prior(pr, gh, findings=None)`. When `findings` is not `None`, set each
      entry's `"finding"` to the `id` of the first finding whose
      `finding_identities` contain the entry's `hash` (`None` when the hash is
      `None` or nothing matches). Without `findings`, add no key. Extend the
      docstring.
- [ ] 3.3 [req: review-incremental] In `main`, add
      `pv.add_argument("--from", dest="from_", default=None, ...)` to the
      `prior` parser. In `_cmd_prior`, when `args.from_` is set, call
      `prior(args.pr, gh, findings=_load_review(args.from_).get("findings")
      or [])`.
- [ ] 3.4 [req: *] From `plugins/s/skills/review`, run
      `python3 -B -m unittest discover -s tests 2>&1 | tail -3` and confirm
      `OK`. Then from `plugins/s/skills/room`, run
      `python3 -B -m unittest discover -s tests 2>&1 | tail -3` and confirm
      `OK`.

## 4. Docs

- [ ] 4.1 [req: review-incremental] In
      `plugins/s/skills/review/references/posting.md` step 3, replace the
      hash-comparison sentence. The new text: write the surviving findings'
      draft `--json` object to a temp file, run
      `review_gate.py prior <pr> --from <that file>`, and omit each finding
      whose `id` an entry classified `replied` names in `finding`. Say that
      `finding` matches threads at any of the finding's locations, including
      threads an earlier gate posted per location. Keep the four class
      bullets.
- [ ] 4.2 [req: gate-poster] In the same file's step 5, replace "posts one
      inline comment per anchorable location across a finding's `locations`
      array" with "posts one inline comment per finding at its first
      anchorable location, naming the others on an `Also recurs at:` line".
- [ ] 4.3 [req: review-incremental, gate-poster] In
      `docs/semantic-review-reference.md`'s `## The prior verb` section, add a
      `finding` row to the field table ("with `--from`, the `id` of the
      payload finding this thread belongs to, or `null`"). Add one paragraph:
      the poster posts one comment per finding, an older pull request can
      carry one thread per location for the same finding, and `--from` maps
      each of those threads to that finding. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/semantic-review-reference.md`
      and confirm exit 0 with no new warning on the edited lines.

## 5. Version and full verification

- [ ] 5.1 [req: *] Advance the plugin version in
      `plugins/s/.claude-plugin/plugin.json`. Run `git fetch origin main`.
      When `python3 plugins/s/skills/build/scripts/version_guard.py --help`
      lists `--advance`, leave the number to `/s:build`'s ship-time step;
      otherwise set `version` one patch above the one in
      `git show origin/main:plugins/s/.claude-plugin/plugin.json`.
- [ ] 5.2 [req: *] From the repository root, run
      `python3 -B -m unittest discover -s plugins/s/skills/review/tests 2>&1 | tail -3`,
      `python3 -B -m unittest discover -s plugins/s/skills/room/tests 2>&1 | tail -3`
      and `python3 -B -m unittest discover -s plugins/s/skills/build/tests 2>&1 | tail -3`.
      Confirm each prints `OK`.
