# review-incremental

- [x] 1.1 [P1] [req: review-incremental] Extend `plugins/s/skills/review/tests/test_review_gate.py` with the assertions this change must satisfy, and confirm they FAIL before any other task is claimed. Build thread fixtures through the real renderer the way `_gate_thread` already does — never hand-written bodies. Cover: a rendered body ends with the identity marker and `parse_severity` still returns its severity; two findings differing only in line number hash identically; two differing in `what` text hash differently; `prior` classifies a thread with a reasoned reply as `replied`, one whose only replies are a canonical `autoreply` body as `autoreplied`, one with no reply but a later commit as `commit-only`, and one with neither as `none`; and `prior` mutates nothing. Do not weaken any existing assertion — all 74 current tests must keep their strength.
- [x] 2.1 [P2] [req: review-incremental] In `plugins/s/skills/review/scripts/review_gate.py`, add the identity helper: a function taking a finding's `location` path and `what` text and returning the first twelve hex characters of the SHA-256 of the path, a newline, and the `what` lowercased with whitespace runs collapsed to one space. Add a second helper that extracts a hash from a rendered body, returning `None` where no marker is present. Use only the standard library, per the constitution.
- [x] 2.2 [P2] [req: review-incremental] In the same file, append the marker `<!-- shipd-finding <hash> -->` as the last element of `_inline_body`'s output, separated from the prose by a blank line. It must come after any `suggestion` fence. Do not touch the opening severity marker — `parse_severity` matches the body's lstripped start, so a prepended marker would break every severity readback.
- [x] 3.1 [P3] [req: review-incremental] Add `path` to the `reviewThreads` node selection in `_THREADS_QUERY` in `review_gate.py`, and carry it through `_list_review_threads` into each thread dict alongside the fields it already returns. Confirm the existing `resolve` and `autoreply` verbs still pass their tests, since both consume that same helper.
- [x] 4.1 [P4] [req: review-incremental] Add the `prior` verb to `review_gate.py`: register it with `sub.add_parser` alongside the existing five, resolve the pull request and repository the way the other verbs do, list the gate-authored threads (root comment authored by the authenticated viewer), and emit one JSON entry per thread with `hash`, `path`, `severity`, `what`, `thread_id`, `resolved` and `disposition`. Classify per the delta: all non-root comments exactly matching a canonical body in `AUTOREPLY_DISPOSITIONS` gives `autoreplied`; any other reply gives `replied`; no reply but a commit dated after the thread's creation gives `commit-only`; neither gives `none`. The verb decides nothing about suppression and mutates nothing.
- [x] 5.1 [P5] [req: review-incremental] Document the read-back in `plugins/s/skills/review/references/posting.md`: add a step before the existing disposition loop instructing the reviewer to run `prior`, omit a finding whose hash matches a `replied` thread, and state the omission count and the pull request in the report. Explain why the other three classifications do not suppress — `commit-only` means implemented, so a recurrence is a regression; `autoreplied` means nobody assessed it; `none` means undispositioned.
- [x] 5.2 [P5] [req: review-incremental] Edit the `posting.md` row of the `## References` table in `plugins/s/skills/review/SKILL.md` (line 46), extending its `Load when` cell so the cell also states that posting reads prior findings back before reporting. Add no line anywhere in the file — it stands at 299 against a ceiling of under 300, so there is no room at all. Report the final line count and confirm `test_under_line_ceiling` and `test_table_cell_agrees_with_reference_condition` both still pass.
- [x] 6.1 [P6] [req: *] Bump `"version"` in `plugins/s/.claude-plugin/plugin.json` to `0.6.219`, per the cache-snapshot rule in AGENTS.md.
- [x] 6.2 [P6] [req: *] Run `python3 -m unittest discover -s plugins/s/skills/review/tests -v` and confirm every test passes, task 1.1's new assertions included. Then run `python3 -m unittest discover -s plugins/s/skills/build/tests -v` and confirm no regression. Report both counts.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 152 | 43.1k |
| Edit | 20 | 23.6k |
| Read | 42 | 12.7k |
| (no tool) | 0 | 4.8k |
| Agent | 4 | 2.1k |
| ToolSearch | 2 | 607 |
| **Total** | 220 | 86.8k |
