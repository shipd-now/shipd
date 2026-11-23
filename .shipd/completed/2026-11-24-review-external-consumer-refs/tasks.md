## 1. The `linked` verb

- [x] 1.1 [req: linked-prs-verb] In
      `plugins/s/skills/review/tests/test_review_gate.py`, extend `FakeGh`
      with three keyword arguments: `pr_body` (string, default `""`),
      `timeline` (list of event dicts, default empty), and `linked_pulls`
      (dict mapping `"<owner>/<repo>#<n>"` to a pull dict with `head.sha`,
      `state`, `merged`, `html_url`, or to a `(rc, stdout, stderr)` triple for
      a failed read), plus `timeline_fail` (bool) and `search_results` (list
      of dicts with `number`, `url`, `headRefOid`). Dispatch:
      `pr view ... --json body` answers `{"body": pr_body}`;
      `api repos/<repo>/issues/<n>/timeline` answers the `timeline` list, or
      exit 1 when `timeline_fail`; `api repos/<o>/<r>/pulls/<n>` answers from
      `linked_pulls`; `pr list --repo ...` answers `search_results`. Place the
      `body` branch before the existing generic `pr view` branch.
- [x] 1.2 [req: linked-prs-verb] In the same file, add a `LinkedTest` class
      with one test per scenario of `linked-prs-verb`, calling
      `review_gate.main(["linked", ...], gh=fake)` and reading stdout. Use
      the invented repository name acme/consumer and pull request 406 as
      fixture names. The
      search-without-repo test asserts `fake.calls` is empty. Run the module
      and observe the new tests fail: the verb does not exist yet.
- [x] 1.3 [req: linked-prs-verb] In
      `plugins/s/skills/review/scripts/review_gate.py`, add a function
      `linked(pr, gh, repo=None, search=None)` returning the entry list per
      plan.md's "Verb shape", "Three sources" and "Head commits" decisions.
      Resolve the reviewed pull request's number with `_resolve_pr` and its
      repository with the module's existing `nameWithOwner` read. Call
      `_fail` when the timeline read exits non-zero.
- [x] 1.4 [req: linked-prs-verb] In the same file, add `_cmd_linked(args, gh)`
      printing `json.dumps(entries)`, and register a `linked` subparser in
      `main` with `pr`, `--repo` and `--search`. Make `main` call
      `parser.error` when `--search` is set without `--repo`, beside the
      existing `--room-to` check. Add a `linked <pr>` line to the module
      docstring's verb list. Confirm the `LinkedTest` tests pass.

## 2. The review rule

- [x] 2.1 [req: external-consumer-refs, copilot-external-consumer-refs] In
      `plugins/s/skills/review/tests/test_skill_references.py`, append
      `"consumers in another repository"` to `DOWNSTREAM_CHECKS`. Add a test
      class `ExternalConsumerRuleTest` asserting, case-insensitively: that
      `plugins/s/skills/review/references/call-site-tracing.md` holds the heading
      `## Consumers in another repository` and the strings
      `review_gate.py" linked`, `?ref=` and `could-not-verify`; that
      `plugins/s/skills/review/references/posting.md` holds `review_gate.py linked`; and that
      `COPILOT_SKILL_MD` and `HARNESS_REVIEW_BODY` each hold
      `another repository`, `?ref=` and `/timeline`. Run the module and
      observe the new assertions fail.
- [x] 2.2 [req: external-consumer-refs] In
      `plugins/s/skills/review/SKILL.md`, insert block A of
      `artefacts/review-text.md` directly after the
      `**Uneven sibling sites**` bullet of step 3. Confirm the file holds
      fewer than 340 lines.
- [x] 2.3 [req: external-consumer-refs] In
      `plugins/s/skills/review/references/call-site-tracing.md`, insert
      block B of `artefacts/review-text.md` between the `## Downstream impact`
      section and the `## Call-site values` section.
- [x] 2.4 [req: external-consumer-refs] In
      `plugins/s/skills/review/references/posting.md`, append block C of
      `artefacts/review-text.md` to flow step 2, after the sentence ending
      "what the review compared."
- [x] 2.5 [req: copilot-external-consumer-refs] In
      `plugins/s/integrations/copilot/SKILL.md`, append block D of
      `artefacts/review-text.md` as the last bullet of
      `### 3. Check downstream impact`.
- [x] 2.6 [req: external-consumer-refs] In
      `plugins/s/harness/bodies/review.md`, append block E of
      `artefacts/review-text.md` to the end of step 4. Confirm
      `test_skill_references.py` now passes in full.

## 3. Docs and version

- [x] 3.1 [req: external-consumer-ships] Through `/s:document`, add a
      `## The linked verb` section to `docs/semantic-review-reference.md`
      after `## The \`prior\` verb`. State the invocation
      `review_gate.py linked <pr> [--repo <owner>/<repo>] [--search <terms>]`,
      a table of the entry fields (`repo`, `number`, `url`, `state`,
      `head_sha`, `source`, and `error` on a failed read), the three `source`
      values, and the exit codes. Add "and the `linked` verb's output" to the
      page's opening list. Keep the page at 250 lines or fewer and run
      `plugins/s/skills/document/scripts/docs_lint.py` on it until clean.
- [x] 3.2 [req: external-consumer-ships] Through `/s:document`, add one
      paragraph to `## Severity and the blocking rule` in
      `docs/semantic-review.md`: a consumer in another repository is read at
      a named ref, linked pull request heads first, and a default-branch read
      alone never blocks. Add "and `linked`'s output" to the `## Reference`
      link line. Keep the page at 100 lines or fewer, list no flag and no
      JSON field, and run `docs_lint.py` on it until clean.
- [x] 3.3 [req: external-consumer-ships] In
      `plugins/s/.claude-plugin/plugin.json`, raise the patch number of
      `version` by one above the value on the remote main branch.
- [x] 3.4 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests` and
      `python3 -m unittest discover -s plugins/s/skills/build/tests`. Search
      each run's full output for `OK` or `FAILED`, and confirm both print
      `OK`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 79 | 38.7k |
| SubagentHandback | 5 | 7.8k |
| Write | 1 | 2.4k |
| Edit | 6 | 2.1k |
| Agent | 3 | 1.8k |
| SendMessage | 3 | 1.6k |
| (no tool) | 0 | 1.0k |
| Monitor | 3 | 909 |
| ToolSearch | 3 | 430 |
| Read | 2 | 260 |
| **Total** | 105 | 57.0k |
