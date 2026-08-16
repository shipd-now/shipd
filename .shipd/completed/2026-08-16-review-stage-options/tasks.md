## 1. Disposition-aware poster

- [x] 1.1 [req: gate-poster] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add failing
      tests for `post --disposition`: `all` (and omitted) keeps
      `success` iff verdict `pass`; `high-only` posts `success` with only
      medium/low findings and `failure` with a high; `none` posts
      `success` with a high; a non-`all` scope adds a
      `Disposition: <scope>` line to the summary body and names the scope
      in the status description; `--model tier-below` adds a
      `Model: tier-below` summary line and is absent when the flag is
      omitted. Use the existing fake `gh` seam; run the suite and observe
      the new tests fail.
- [x] 1.2 [req: gate-poster] In
      `plugins/s/skills/review/scripts/review_gate.py`, add
      `--disposition {all,high-only,none}` (default `all`) and `--model`
      to the `post` subparser; thread both into `post(...)`; compute the
      status state by scope (`all`: verdict pass; `high-only`: no
      finding with severity `high`; `none`: always `success`); append
      `(disposition <scope>)` to the status description for non-`all`
      scopes; and extend `render_summary` to emit the
      `Disposition:`/`Model:` lines under the effort line when given.
      Confirm the 1.1 tests pass.

## 2. Autoreply verb

- [x] 2.1 [req: auto-disposition-verb, gate-test-coverage] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add failing
      tests for `autoreply` against a fake `gh` seam serving the
      GraphQL threads query: `high-only` replies to unreplied
      gate-authored medium and low roots, leaves high and unparseable
      roots untouched (reporting the unparsed one), and prints
      `replied=2`; `none` replies to every unreplied gate thread;
      already-replied threads and human-authored threads are never
      touched; a re-run prints `replied=0`; and a round-trip test
      asserting the severity parser recovers the severity from every
      `_inline_body`-rendered first line. Run the suite and observe the
      new tests fail.
- [x] 2.2 [req: auto-disposition-verb] In
      `plugins/s/skills/review/scripts/review_gate.py`, add a
      module-level severity-marker regex derived from the same
      `**<severity> — ` prefix `_inline_body` renders (use it in a
      parse helper), and an `autoreply(pr, gh, disposition, body=None,
      out=...)` function: list threads via `_list_review_threads`,
      select gate-authored unresolved threads with exactly one comment,
      filter by parsed root severity per scope, post the canonical
      policy reply (default body naming the scope, `--body` override)
      via the REST `in_reply_to` create, and print `replied=<n>` on
      stdout. Wire an `autoreply` subparser with `pr`,
      `--disposition {high-only,none}` (required), and `--body`.
      Confirm the 2.1 tests pass and the full review suite stays green.

## 3. Skill flow and hand-off

- [x] 3.1 [req: skill-post-flow] In
      `plugins/s/skills/review/SKILL.md`, add a "Review stage options"
      note to the "Posting to a PR (the gate)" section: the invoker may
      pass `disposition=<all|high-only|none>` (default `all`) and
      `model=<tier>`; both pass through to `review_gate.py post` as
      `--disposition`/`--model`; the model tier is recorded provenance
      applied by the driver that spawns the reviewing session, and the
      skill never resolves the pipeline configuration itself.
- [x] 3.2 [req: skill-post-flow] In the same SKILL.md posting flow,
      make step 5 scope-aware: `all` keeps the existing full loop;
      `high-only` implements (or reasoned-replies) only high findings,
      re-reviews and re-posts after any push, then runs
      `review_gate.py autoreply <pr> --disposition high-only`;
      `none` skips per-finding judgment and runs
      `autoreply <pr> --disposition none`; every scope finishes with
      `resolve` and step 7's report additionally names the acting scope
      when it is not `all`.
- [x] 3.3 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` (patch bump), since this
      change touches `plugins/s/`.
- [x] 3.4 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/review/tests -q`
      and `python3 -m unittest discover -s plugins/s/skills/build/tests
      -q` and confirm both pass without network access or third-party
      packages installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Edit | 31 | 21.6k |
| Bash | 46 | 14.7k |
| Write | 4 | 8.6k |
| (no tool) | 0 | 5.7k |
| Read | 9 | 874 |
| Agent | 2 | 704 |
| **Total** | 92 | 52.2k |
