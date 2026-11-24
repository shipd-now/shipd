## 1. Tests first

- [x] 1.1 [req: linked-prs-verb] In
      `plugins/s/skills/review/tests/test_review_gate.py`, make `FakeGh`
      answer the timeline read with a new `timeline_raw` keyword argument
      (a string returned as stdout verbatim when set, default `None`), and
      make its `pr list --repo` branch return `search_results` unchanged
      while the call stays recorded in `fake.calls`.
- [x] 1.2 [req: linked-prs-verb] In the same file, add to `LinkedTest` one
      test for each of these scenarios of `linked-prs-verb`: the body
      shorthand reference; the listing call carrying `--search` and
      `--limit 200`; the repository with no search terms; the full listing
      warning (200 results); the short listing staying silent; the URL in
      another repository (construct `FakeGh` with
      `pr_url="https://github.com/other/repo/pull/7"` and assert the timeline
      path and that no call starts with `repo view`); the two-page timeline
      (via `timeline_raw`); and the merged state. Run the module and observe
      the new tests fail.

## 2. The verb

- [x] 2.1 [req: linked-prs-verb] In
      `plugins/s/skills/review/scripts/review_gate.py`, change `linked` to
      take the repository from the URL `_resolve_pr` returns, per plan.md's
      "Repository from the URL" decision, and remove its `_resolve_repo`
      call.
- [x] 2.2 [req: linked-prs-verb] In the same file, add the constant
      `LINKED_SEARCH_LIMIT = 200`, pass it as `--limit` on the `gh pr list`
      call, and write the warning line from plan.md's "Limit" decision to
      stderr when the listing holds that many items.
- [x] 2.3 [req: linked-prs-verb] In the same file, add the shorthand regex
      from plan.md's "Shorthand" decision beside `_PR_URL_RE`, and run it
      over the body after the URL matches, adding each match as a `body`
      entry.
- [x] 2.4 [req: linked-prs-verb] In the same file, correct the three
      descriptions of the search source — the module docstring's `linked`
      entry, the `linked` function docstring, and the `linked` subparser
      help — to say that `--repo` lists that repository's open pull requests,
      up to 200, narrowed by `--search` where given, and that the body source
      reads URLs and shorthand. Confirm every `LinkedTest` test passes.

## 3. Text, docs and version

- [x] 3.1 [req: linked-hardening-ships] In
      `plugins/s/skills/review/references/posting.md`, change the call
      `review_gate.py linked <number> --repo <owner>/<repo>` to
      `review_gate.py linked <number> --repo <owner>/<repo> --search <symbol>`,
      re-wrapping only that paragraph.
- [x] 3.2 [req: linked-hardening-ships] In
      `plugins/s/skills/review/references/call-site-tracing.md`, append this
      sentence to the "List the linked pull requests first" bullet: "Where
      the verb warns that the search listing is full, narrow `--search`;
      where you cannot, record a could-not-verify entry."
- [x] 3.3 [req: linked-hardening-ships] Through `/s:document`, revise the
      `## The linked verb` section of `docs/semantic-review-reference.md`:
      state that `--repo` alone lists every open pull request in that
      repository and that `--search` narrows the listing; state the 200 limit
      and its stderr warning; change the `body` row to name a URL or
      `<owner>/<repo>#<number>` shorthand; change the `search` row to "an
      open pull request in `--repo`, narrowed by `--search` where given"; and
      state that `--repo` bounds the head reads. Keep the page at 250 lines
      or fewer and run `plugins/s/skills/document/scripts/docs_lint.py` on it
      until it exits 0.
- [x] 3.4 [req: linked-hardening-ships] In
      `plugins/s/.claude-plugin/plugin.json`, raise the patch number of
      `version` by one above the value on the remote main branch.
- [x] 3.5 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests` and
      `python3 -m unittest discover -s plugins/s/skills/build/tests`. Search
      each run's full output for `OK` or `FAILED`, and confirm both print
      `OK`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 45 | 20.3k |
| SubagentHandback | 2 | 3.3k |
| Agent | 3 | 2.0k |
| Write | 1 | 1.6k |
| Read | 6 | 908 |
| Edit | 2 | 508 |
| (no tool) | 0 | 477 |
| ToolSearch | 2 | 370 |
| Monitor | 1 | 261 |
| **Total** | 62 | 29.7k |
